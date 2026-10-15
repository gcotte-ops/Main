#!/usr/bin/env python3
"""
Détection des contacts HubSpot en doublon : produit doublons_contacts.xlsx, dont l'onglet
« Doublons » est lu par fusion_doublons_hubspot.py (lignes de niveau « Certain »).

La détection est en LECTURE SEULE : elle n'écrit jamais dans HubSpot.

À lancer APRÈS la fusion des entreprises, sur une NOUVELLE extraction des contacts : une fois
les ID d'entreprise stabilisés, « même entreprise associée » devient un lien fiable.
Ordre complet : détection puis fusion des entreprises, détection puis fusion des contacts.

Noms : civilités retirées (nettoyer_nom), prénom et nom normalisés, prénom et nom inversés
compatibles (prenoms_compatibles du script de fusion).
Liens forts : même entreprise associée, même domaine email professionnel (hors webmail et
adresse générique), même mobile, même téléphone fixe.

  Bloquée    B-C1 prénoms incompatibles (deux prénoms complets différents, initiales qui ne
             correspondent pas) : la paire n'est jamais groupée (« Personnes distinctes »).
  Certain    CC1 même email (principal identique, ou principal de l'un parmi les emails
             secondaires de l'autre) ; une adresse générique (contact@, accueil@...) avec des
             noms de famille différents ne fait aucun lien ;
             CC2 même boîte sur un domaine mal orthographié + même nom de famille ;
             CC3 même prénom + même nom + au moins un lien fort.
             Jamais Certain : webmails seuls, entreprises différentes sans autre lien, prénom
             réduit à une initiale (sauf CC1), adresse générique partagée.
  Probable   les cas ci-dessus « jamais Certain » ; même prénom et même nom sans autre lien
             (nom porté par 3 fiches au plus : au-delà, homonymes probables) ; nom de famille à
             une faute près, incomplet (prénom ou nom absent) ou composé (« Da Trindade » /
             « Lopes Da Trindade ») + un lien fort ; fiche sans nom dont l'email reprend le
             prénom et le nom de l'autre fiche + un lien fort ; même boîte sur un domaine
             proche, nom absent.

Groupes : même règle stricte que pour les entreprises (aucun chaînage dans un groupe Certain).
Racine suggérée : email valide et non en échec, puis entreprise associée, puis activité la
plus récente, puis la fiche la plus complète. La fusion choisit de toute façon sa fiche
principale elle-même : la racine sert à la relecture.

Exemples :
  python detection_contacts_hubspot.py                                 # lecture HubSpot
  python detection_contacts_hubspot.py --depuis-export contacts.csv    # sans l'API
  python detection_contacts_hubspot.py --ancien doublons_potentiels_hubspot.xlsx

Accès HubSpot : variable d'environnement HUBSPOT_TOKEN = jeton d'une application privée avec
les droits crm.objects.contacts.read, crm.objects.companies.read et crm.objects.owners.read.
"""

import argparse
import datetime
import os
import re
import sys

import detection_entreprises_hubspot as de
import fusion_doublons_hubspot as fc
import normalisation as nz
from fusion_doublons_hubspot import PORTAIL_DEFAUT, ErreurHubSpot, date_iso, normaliser

CERTAIN, PROBABLE = de.CERTAIN, de.PROBABLE
FICHIER_SORTIE = "doublons_contacts.xlsx"
LIEN_FICHE = fc.LIEN_FICHE

PROPRIETES = fc.PROPRIETES + ["notes_last_updated"]

# Au-delà de ce nombre de fiches portant le même prénom et le même nom, deux d'entre elles
# sans autre lien sont des homonymes probables : elles ne sont pas proposées.
NOM_COURANT = 4
FORTS = ("meme_entreprise", "meme_domaine_pro", "meme_mobile", "meme_fixe")
LIENS_DIRECTS = {"meme_email", "email_generique", "meme_boite", "boite_generique",
                 "meme_personne", "prenom_compatible", "nom_faute", "nom_incomplet",
                 "nom_inclus", "email_designe", "meme_mobile", "meme_fixe"}
LIENS_GENERIQUES = {"email_generique", "boite_generique"}

COLONNES = ["Groupe", "Niveau", "Raison du rapprochement", "Racine suggérée", "ID HubSpot",
            "Lien HubSpot", "Prénom", "Nom", "E-mail", "Téléphone", "Entreprise",
            "Intitulé du poste", "Propriétaire du contact", "Date de création",
            "Autres emails", "Mobile", "ID entreprise associée", "Liens avec la racine"]

# (catégorie, préfixe, onglet, niveau affiché)
ONGLETS_RELECTURE = [("generique", "A-", "Adresses génériques partagées", "À vérifier"),
                     ("bloquees", "P-", "Personnes distinctes", "Bloqué")]

ALIAS_EXPORT = {
    "id": ["id de fiche d'informations", "record id", "id hubspot", "id", "contact id",
           "id du contact"],
    "firstname": ["prenom", "first name", "firstname"],
    "lastname": ["nom", "nom de famille", "last name", "lastname"],
    "email": ["e mail", "email", "adresse e mail", "email address"],
    "hs_additional_emails": ["autres emails", "adresses e mail supplementaires",
                             "additional email addresses"],
    "phone": ["numero de telephone", "telephone", "phone number"],
    "mobilephone": ["mobile", "numero de telephone portable", "telephone portable",
                    "mobile phone number"],
    "jobtitle": ["intitule du poste", "poste", "job title"],
    "company": ["nom de l'entreprise", "entreprise", "company name"],
    "associatedcompanyid": ["id entreprise associee", "id de l'entreprise principale associee",
                            "id de l'entreprise associee", "associated company id"],
    "hubspot_owner_id": ["proprietaire du contact", "proprietaire", "contact owner"],
    "createdate": ["date de creation", "create date"],
    "hs_email_hard_bounce_reason_enum": ["raison du hard bounce de l'e mail",
                                         "email hard bounce reason"],
    "notes_last_updated": ["derniere activite", "date de la derniere activite",
                           "last activity date"],
}

REGLES_PAR_COLONNE = {
    "hs_additional_emails": "email principal de l'un parmi les emails secondaires de l'autre",
    "phone": "même téléphone fixe",
    "mobilephone": "même mobile",
    "associatedcompanyid": "même entreprise associée (ID entreprise affiché seulement si la "
                           "colonne Entreprise contient un ID)",
    "hs_email_hard_bounce_reason_enum": "racine : email en échec",
    "notes_last_updated": "racine : activité la plus récente",
    "hubspot_owner_id": "propriétaire",
}


# --------------------------------------------------------------------------- #
# Fiches
# --------------------------------------------------------------------------- #

class FicheContact(fc.Fiche):
    """Fiche contact du script de fusion, avec la date de dernière activité."""

    def __init__(self, *args, activite="", **kwargs):
        super().__init__(*args, **kwargs)
        self.activite = date_iso(nz.nettoyer(activite))


def personne(texte):
    """normaliser() puis ponctuation retirée : « Mengue M’ella » -> « mengue m ella »."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", normaliser(texte))).strip()


class Normes:
    """Formes normalisées d'une fiche contact (calculées une fois)."""

    def __init__(self, fiche):
        self.prenom = personne(fiche.prenom_net)
        # Prénom recopié en tête du nom retiré (« Martial » / « Martial FORT »).
        self.nom = personne(fc.nom_sans_prenom(fiche))
        self.initiale = bool(self.prenom) and fc.est_initiale(fiche.prenom_net)
        self.email = nz.email(fiche.email)
        autres = [e for e in nz.emails_liste(fiche.emails_secondaires) if e != self.email]
        self.emails = ([self.email] if self.email else []) + list(dict.fromkeys(autres))
        self.domaines_pro = {nz.domaine_email(e) for e in self.emails
                             if fc.email_valide(e) and not nz.est_webmail(e)
                             and not nz.est_generique(e)}
        self.webmail = bool(self.email) and nz.est_webmail(self.email)
        self.numeros = {}
        for numero in (fiche.telephone, fiche.mobile):
            d = nz.telephone(numero)
            if d:
                self.numeros[d] = "mobile" if d[:2] in ("06", "07") else "fixe"
        self.entreprise = str(fiche.id_entreprise or "").strip()
        self.complet = nz.compact(self.prenom + self.nom)
        # Partie locale réduite à ses lettres : « remy.viallet » -> « remyviallet ».
        self.local = re.sub(r"[^a-z]", "", nz.sans_accents(nz.local_email(self.email)))


def normes(fiche):
    n = getattr(fiche, "_normes", None)
    if n is None:
        n = fiche._normes = Normes(fiche)
    return n


# --------------------------------------------------------------------------- #
# Comparaison de deux fiches
# --------------------------------------------------------------------------- #

class PaireContact:

    def __init__(self, a, b):
        self.a, self.b = a, b
        self.liens = set()
        self.forts = 0
        self.blocage = []
        self.regles = []
        self.exclusions = []
        self.niveau_brut = ""
        self.niveau = ""
        self.categorie = ""
        self.adresse = ""              # adresse partagée

    @property
    def bloquee(self):
        return bool(self.blocage)


def designe(n_sans_nom, n_nomme):
    """L'email de la fiche sans nom reprend le prénom et le nom de l'autre."""
    if not n_sans_nom.local or not n_nomme.prenom or not n_nomme.nom:
        return False
    nom = nz.compact(n_nomme.nom)
    return n_sans_nom.local in (nz.compact(n_nomme.prenom) + nom, n_nomme.prenom[0] + nom,
                                nom + nz.compact(n_nomme.prenom))


def evaluer(a, b, frequences=None):
    """Compare deux fiches contacts (sections 6.1 à 6.4). frequences : nombre de fiches par
    prénom + nom (base complète), pour écarter les noms courants sans autre lien."""
    na, nb = normes(a), normes(b)
    p = PaireContact(a, b)
    L = p.liens

    # Noms.
    if na.prenom and nb.prenom and na.nom and nb.nom:
        if na.prenom == nb.prenom and na.nom == nb.nom:
            L.add("meme_personne")
        elif na.prenom == nb.nom and na.nom == nb.prenom:
            L.update(("meme_personne", "inverses"))
        elif na.nom == nb.nom and fc.prenoms_compatibles(a, b):
            L.add("prenom_compatible")
        elif (fc.prenoms_compatibles(a, b) and min(len(na.nom), len(nb.nom)) >= 5
              and nz.distance_un(nz.compact(na.nom), nz.compact(nb.nom))):
            L.add("nom_faute")
    elif bool(na.prenom) != bool(nb.prenom) and na.nom and nb.nom:
        # Nom complet saisi dans le seul champ nom : « Sophie-Anne BRACCHI SEBAIBI ».
        seul, complet = (na, nb) if not na.prenom else (nb, na)
        if nz.compact(seul.nom) in (complet.complet, nz.compact(complet.nom + complet.prenom)):
            L.update(("meme_personne", "nom_un_champ"))
    if na.nom and nb.nom and (na.nom == nb.nom or "inverses" in L or "nom_un_champ" in L):
        L.add("meme_nom_famille")
    if "meme_personne" not in L and fc.prenoms_compatibles(a, b):
        if (na.nom and na.nom == nb.nom and bool(na.prenom) != bool(nb.prenom)) or \
                (na.prenom and na.prenom == nb.prenom and bool(na.nom) != bool(nb.nom)):
            L.add("nom_incomplet")               # « M. BORIES » / « Philippe Bories »
        elif (na.prenom and nb.prenom and na.nom and nb.nom and na.nom != nb.nom
              and nz.contient_suite(na.nom, nb.nom)):
            L.add("nom_inclus")                  # « Lopes Da Trindade » / « Da Trindade »
    sans_nom_a, sans_nom_b = not (na.prenom or na.nom), not (nb.prenom or nb.nom)
    if (sans_nom_a and designe(na, nb)) or (sans_nom_b and designe(nb, na)):
        L.add("email_designe")
    initiale = na.initiale or nb.initiale

    # Emails.
    if na.email and na.email in nb.emails:
        p.adresse = na.email
    elif nb.email and nb.email in na.emails:
        p.adresse = nb.email
    if p.adresse:
        L.add("email_generique" if nz.est_generique(p.adresse) else "meme_email")
    elif na.email and nb.email and fc.meme_boite(na.email, nb.email):
        L.add("boite_generique" if nz.est_generique(na.email) else "meme_boite")

    # Liens forts.
    if na.entreprise and na.entreprise == nb.entreprise:
        L.add("meme_entreprise")
    if na.domaines_pro & nb.domaines_pro:
        L.add("meme_domaine_pro")
    for numero in set(na.numeros) & set(nb.numeros):
        L.add("meme_mobile" if na.numeros[numero] == "mobile" else "meme_fixe")
    p.forts = sum(1 for f in FORTS if f in L)
    if na.entreprise and nb.entreprise and na.entreprise != nb.entreprise:
        L.add("entreprises_differentes")
    if na.webmail and nb.webmail and not p.forts:
        L.add("webmails_seuls")

    # Règle bloquante B-C1.
    if not fc.prenoms_compatibles(a, b):
        p.blocage.append("B-C1 – prénoms incompatibles (« {} » / « {} »)".format(
            a.prenom_net, b.prenom_net))

    # Certain (6.3) et exclusions (6.4).
    nom_identique = "meme_personne" in L or "prenom_compatible" in L
    if "meme_email" in L:
        p.regles.append("CC1")
    if "meme_boite" in L and "meme_nom_famille" in L:
        p.regles.append("CC2")
    if nom_identique and p.forts >= 1:
        p.regles.append("CC3")
    if initiale and "meme_email" not in L:
        p.exclusions.append("prénom réduit à une initiale")
    if "email_generique" in L or "boite_generique" in L:
        p.exclusions.append("adresse générique partagée")

    # Probable.
    courant = (frequences or {}).get(na.complet, 0) > NOM_COURANT - 1 if na.complet else False
    if p.regles and not p.exclusions:
        p.niveau_brut = CERTAIN
    elif (p.regles
          or ("email_generique" in L and "meme_nom_famille" in L)
          or (nom_identique and not initiale and not courant)
          or (L & {"nom_faute", "nom_incomplet", "nom_inclus"} and p.forts >= 1)
          or ("email_designe" in L and (p.forts >= 1 or nz.domaine_email(na.email)
                                        == nz.domaine_email(nb.email)))
          or ("meme_boite" in L and (sans_nom_a or sans_nom_b))):
        p.niveau_brut = PROBABLE
    if not p.niveau_brut and ("email_generique" in L or "boite_generique" in L):
        p.categorie = "generique"
    p.niveau = "" if p.bloquee else p.niveau_brut
    return p


def raison(p):
    """« Même prénom et nom + même entreprise + même mobile »."""
    L = p.liens
    if "meme_email" in L:
        base = "Même email"
    elif "meme_boite" in L:
        base = "Même boîte mail sur deux domaines proches (faute de frappe ?)"
    elif "email_generique" in L or "boite_generique" in L:
        base = "Adresse générique partagée"
    elif "email_designe" in L:
        base = "Fiche sans nom dont l’email reprend le prénom et le nom de l’autre fiche"
    else:
        base = ""
    noms = ""
    if "inverses" in L:
        noms = "Prénom et nom inversés"
    elif "nom_un_champ" in L:
        noms = "Même prénom et nom (nom complet dans un seul champ)"
    elif "meme_personne" in L:
        noms = "Même prénom et nom"
    elif "prenom_compatible" in L:
        noms = "Même nom, prénom compatible (initiale, prénom composé ou faute)"
    elif "nom_faute" in L:
        noms = "Même nom à une faute près"
    elif "nom_incomplet" in L:
        noms = "Nom incomplet sur une fiche"
    elif "nom_inclus" in L:
        noms = "Nom de famille inclus dans l’autre (nom composé)"
    texte = " + ".join(t for t in (base, noms) if t) or "Noms différents"
    for cle, libelle in (("meme_entreprise", "même entreprise"),
                         ("meme_domaine_pro", "même domaine email"),
                         ("meme_mobile", "même mobile"), ("meme_fixe", "même téléphone")):
        if cle in L:
            texte += " + " + libelle
    notes = [libelle for cle, libelle in (("entreprises_differentes", "entreprises différentes"),
                                          ("webmails_seuls", "webmails seulement"))
             if cle in L]
    if p.niveau_brut == PROBABLE and not p.forts and "meme_personne" in L:
        notes.append("changement de poste ou homonyme ?")
    notes += [e for e in p.exclusions if e != "adresse générique partagée" or base !=
              "Adresse générique partagée"]
    if notes:
        texte += " — " + ", ".join(notes)
    return texte


def liens_texte(p):
    L = p.liens
    items = []
    for cle, libelle in (("meme_email", "même email ({})".format(p.adresse)),
                         ("email_generique", "adresse générique partagée ({})".format(p.adresse)),
                         ("meme_boite", "même boîte, domaine proche"),
                         ("boite_generique", "boîte générique, domaine proche"),
                         ("meme_personne", "même prénom et nom"),
                         ("inverses", "prénom et nom inversés"),
                         ("prenom_compatible", "même nom, prénom compatible"),
                         ("nom_faute", "nom à une faute près"),
                         ("nom_incomplet", "nom incomplet sur une fiche"),
                         ("nom_inclus", "nom de famille inclus dans l’autre"),
                         ("email_designe", "email au nom de l’autre fiche"),
                         ("meme_entreprise", "même entreprise"),
                         ("meme_domaine_pro", "même domaine email"),
                         ("meme_mobile", "même mobile"), ("meme_fixe", "même téléphone"),
                         ("entreprises_differentes", "entreprises différentes"),
                         ("webmails_seuls", "webmails seulement")):
        if cle in L:
            items.append(libelle)
    items += p.exclusions + p.blocage
    return ", ".join(dict.fromkeys(items)) or "aucun lien direct"


# --------------------------------------------------------------------------- #
# Analyse
# --------------------------------------------------------------------------- #

def cle_racine(fiche):
    """Email valide et non en échec, entreprise associée, activité la plus récente, la plus
    complète, puis le plus petit ID."""
    n = normes(fiche)
    email_sur = bool(n.email) and fc.email_valide(n.email) and not fiche.en_echec
    complete = sum(1 for v in (fiche.prenom_net, fiche.nom_net, fiche.email, fiche.telephone,
                               fiche.mobile, fiche.entreprise or fiche.id_entreprise,
                               fiche.poste) if v)
    return (email_sur, bool(n.entreprise), max(fiche.activite, fiche.creation), complete,
            tuple(-x if isinstance(x, int) else x for x in de.cle_id(fiche.id)))


def cle_tri(fiche):
    n = normes(fiche)
    return (not (n.nom or n.prenom), n.nom, n.prenom, n.email, de.cle_id(fiche.id))


class AnalyseContacts(de.AnalyseDoublons):
    """Détection des contacts en doublon sur toute la base."""

    CATEGORIES = [("generique", "A-")]
    PREFIXE_BLOQUEES = "P-"

    def __init__(self, fiches, journal=print):
        super().__init__(fiches, journal)
        self.frequences = {}
        for f in self.fiches:
            cle = normes(f).complet
            if cle:
                self.frequences[cle] = self.frequences.get(cle, 0) + 1

    def comparer(self, a, b):
        return evaluer(a, b, self.frequences)

    def rapprochee(self, p):
        """Paire bloquée à lister : elle aurait eu un niveau, ou partage un email, une boîte,
        un nom ou un numéro (« Mélissa Belkadi » / « Nadia Gowsy » sur nadia.gowsy@...).
        Une adresse générique seule relève de l'onglet « Adresses génériques partagées »."""
        return bool(p.niveau_brut or p.liens & (LIENS_DIRECTS - LIENS_GENERIQUES))

    def categorie_de(self, p):
        """Les adresses génériques partagées sont listées même entre prénoms incompatibles."""
        return p.categorie

    def cle_racine(self, fiche):
        return cle_racine(fiche)

    def cle_tri(self, fiche):
        return cle_tri(fiche)

    def cles_blocage(self, f):
        n = normes(f)
        cles = set()
        for e in n.emails:
            cles.add(("email", e))
        local = nz.local_email(n.email)
        if len(local) >= 4 and not nz.est_generique(n.email):
            cles.add(("boite", local))                    # même boîte, domaine mal orthographié
        if n.nom and n.prenom:
            cles.add(("nom", nz.compact(n.nom) + "|" + n.prenom[0]))
            cles.add(("nom", nz.compact(n.prenom) + "|" + n.nom[0]))     # prénom et nom inversés
            cles.add(("designe", n.complet))
            cles.add(("designe", n.prenom[0] + nz.compact(n.nom)))
            if n.entreprise:
                cles.add(("prenom_entreprise", n.prenom + "|" + n.entreprise))
            cles.add(("designe", nz.compact(n.nom + n.prenom)))
        elif n.nom and len(n.nom.split()) >= 2:
            cles.add(("designe", n.complet))              # nom complet dans le seul champ nom
        elif n.local and not (n.prenom or n.nom):
            cles.add(("designe", n.local))
        for numero in n.numeros:
            cles.add(("telephone", numero))
        return cles

    def lignes(self, portail=PORTAIL_DEFAUT, noms_entreprises=None):
        f = self.fiches
        noms_entreprises = noms_entreprises or {}
        resultat = {"Doublons": []}
        for g in self.doublons:
            r = g.racine
            if g.origine is not None:
                motif = "Lien indirect (chaînage) avec {}".format(g.origine.numero)
                directs = [raison(self.paire(m, r)) for m in g.membres[1:]
                           if self.paire(m, r).niveau]
                if directs:
                    motif += " : " + " ; ".join(dict.fromkeys(directs))
            else:
                motif = " ; ".join(dict.fromkeys(raison(self.paire(m, r))
                                                 for m in g.membres[1:]))
                if g.issus:
                    motif += " — lien indirect (chaînage) avec " + ", ".join(
                        sorted(i.numero for i in g.issus))
            for m in g.membres:
                liens = "(racine)" if m == r else liens_texte(self.paire(m, r))
                if g.origine is not None and m != r and not self.paire(m, r).niveau:
                    liens = "lien indirect, via le groupe {} ; ".format(g.origine.numero) + liens
                resultat["Doublons"].append(self.ligne(f[m], g.numero, g.niveau, motif, m == r,
                                                       liens, portail, noms_entreprises))
        for categorie, _, onglet, niveau in ONGLETS_RELECTURE:
            lignes = resultat[onglet] = []
            for g in self.relecture[categorie]:
                r = g.racine
                if categorie == "bloquees":
                    p = self.paire(*g.membres)
                    motif = " ; ".join(p.blocage)
                    if g.via is not None:
                        autre = f[g.via]
                        motif += " — rapprochement indirect via « {} {} » ({})".format(
                            autre.prenom, autre.nom, autre.id).replace("«  ", "« ")
                    else:
                        motif += " — rapprochement écarté : " + raison(p)
                else:
                    adresses = sorted({self.paire(x, y).adresse or normes(f[x]).email
                                       for x in g.membres for y in g.membres
                                       if x < y and self.paire(x, y).categorie == categorie})
                    motif = "Adresse générique partagée par des personnes différentes : " + \
                            ", ".join(a for a in adresses if a)
                for m in g.membres:
                    liens = "(racine)" if m == r else liens_texte(self.paire(m, r))
                    lignes.append(self.ligne(f[m], g.numero, niveau, motif, m == r, liens,
                                             portail, noms_entreprises))
        return resultat

    def ligne(self, fiche, groupe, niveau, motif, est_racine, liens, portail, noms_entreprises):
        entreprise = fiche.entreprise or noms_entreprises.get(fiche.id_entreprise, "") \
            or fiche.id_entreprise
        return {
            "Groupe": groupe, "Niveau": niveau, "Raison du rapprochement": motif,
            "Racine suggérée": "Oui" if est_racine else "", "ID HubSpot": fiche.id,
            "Lien HubSpot": "Ouvrir", "_url": LIEN_FICHE.format(portail=portail, id=fiche.id),
            "Prénom": fiche.prenom, "Nom": fiche.nom, "E-mail": fiche.email,
            "Téléphone": fiche.telephone, "Entreprise": entreprise,
            "Intitulé du poste": fiche.poste, "Propriétaire du contact": fiche.proprietaire,
            "Date de création": fiche.creation[:16],
            "Autres emails": " ; ".join(normes(fiche).emails[1:]), "Mobile": fiche.mobile,
            "ID entreprise associée": fiche.id_entreprise, "Liens avec la racine": liens,
        }

    def compteurs(self):
        return super().compteurs([(c, o) for c, _, o, _ in ONGLETS_RELECTURE])


# --------------------------------------------------------------------------- #
# Lecture des données
# --------------------------------------------------------------------------- #

def fiche_depuis_hubspot(brut, proprietaires):
    p = brut.get("properties", {})
    proprietaire, actif = de.libelle_proprietaire(p.get("hubspot_owner_id") or "", proprietaires)
    return FicheContact(
        id=brut["id"], prenom=p.get("firstname"), nom=p.get("lastname"), email=p.get("email"),
        telephone=p.get("phone"), mobile=p.get("mobilephone"), poste=p.get("jobtitle"),
        entreprise=nz.nettoyer(p.get("company")),
        id_entreprise=p.get("associatedcompanyid") or "", proprietaire=proprietaire,
        proprietaire_actif=actif, creation=date_iso(p.get("createdate") or brut.get("createdAt")),
        en_echec=bool(p.get("hs_email_hard_bounce_reason_enum")),
        emails_secondaires=p.get("hs_additional_emails"),
        activite=p.get("notes_last_updated") or "")


def lire_export(chemin):
    """(fiches, colonnes absentes) depuis un export HubSpot ou l'ancien classeur."""
    lignes = de.lire_tableau(chemin)
    entetes = []
    for l in lignes:
        for e in l:
            if e not in entetes:
                entetes.append(e)
    col = de.colonnes_export(entetes, ALIAS_EXPORT)
    if "id" not in col or "email" not in col:
        raise SystemExit("Colonnes « ID » et « E-mail » introuvables dans {} (colonnes : {})"
                         .format(chemin, ", ".join(map(str, entetes))))
    absentes = [p for p in ALIAS_EXPORT if p not in col]
    fiches = []
    for l in lignes:
        v = {p: str(l.get(c) if l.get(c) is not None else "").strip() for p, c in col.items()}
        id_fiche = v.get("id", "")
        if not re.fullmatch(r"\d+(\.0)?", id_fiche):
            continue
        entreprise, id_entreprise = nz.nettoyer(v.get("company")), v.get("associatedcompanyid", "")
        if re.fullmatch(r"\d+(\.0)?", entreprise):   # l'ancien classeur affiche l'ID à défaut
            id_entreprise, entreprise = id_entreprise or entreprise.split(".")[0], ""
        proprietaire = v.get("hubspot_owner_id", "")
        fiches.append(FicheContact(
            id=id_fiche.split(".")[0], prenom=v.get("firstname"), nom=v.get("lastname"),
            email=v.get("email"), telephone=v.get("phone"), mobile=v.get("mobilephone"),
            poste=v.get("jobtitle"), entreprise=entreprise, id_entreprise=id_entreprise,
            proprietaire=proprietaire,
            proprietaire_actif=("deactivated" not in proprietaire.lower()) if proprietaire else None,
            creation=date_iso(v.get("createdate")),
            en_echec=bool(v.get("hs_email_hard_bounce_reason_enum")),
            emails_secondaires=v.get("hs_additional_emails"),
            activite=v.get("notes_last_updated", "")))
    if "associatedcompanyid" in absentes and any(f.id_entreprise for f in fiches):
        absentes.remove("associatedcompanyid")
    return fiches, absentes


def lire_hubspot(jeton, journal=print):
    client = de.ClientDetection(jeton)
    probleme = fc.verifier_jeton(client, jeton)
    if probleme:
        raise SystemExit(probleme)
    proprietaires = client.proprietaires()
    journal("Lecture des contacts HubSpot…")
    fiches = [fiche_depuis_hubspot(b, proprietaires)
              for b in client.lister("contacts", PROPRIETES, journal=journal)]
    return client, fiches


def noms_entreprises(client, ids):
    """{ID: nom} des entreprises associées affichées (lecture par lots de 100)."""
    noms, ids = {}, sorted(i for i in set(ids) if i)
    for debut in range(0, len(ids), 100):
        lot = ids[debut:debut + 100]
        try:
            rep = client.requete("POST", "/crm/v3/objects/companies/batch/read",
                                 {"properties": ["name"], "inputs": [{"id": i} for i in lot]})
        except ErreurHubSpot as e:
            print("  ! noms des entreprises non lus ({}) : ID affichés".format(e),
                  file=sys.stderr)
            return noms
        for r in rep.get("results", []):
            noms[str(r["id"])] = (r.get("properties") or {}).get("name") or ""
    return noms


# --------------------------------------------------------------------------- #
# Programme principal
# --------------------------------------------------------------------------- #

LECTURE_NIVEAUX = [
    "Certain (seul niveau fusionné par fusion_doublons_hubspot.py) : même email (principal "
    "identique, ou principal de l’un parmi les emails secondaires de l’autre) ; même boîte sur "
    "un domaine mal orthographié + même nom de famille ; même prénom et même nom + au moins un "
    "lien fort : même entreprise associée, même domaine email professionnel, même mobile ou même "
    "téléphone fixe.",
    "Jamais Certain : même prénom et nom avec seulement des webmails, ou dans deux entreprises "
    "différentes sans autre lien (changement de poste ou homonyme ?) ; prénom réduit à une "
    "initiale (sauf même email) ; adresse générique partagée (contact@, accueil@, "
    "secretariat@…). Une adresse générique partagée par des noms de famille différents ne fait "
    "aucun lien : onglet « Adresses génériques partagées ».",
    "Probable (à vérifier) : les cas « jamais Certain » ci-dessus ; nom à une faute près, nom "
    "incomplet ou nom composé + un lien fort ; fiche sans nom dont l’email reprend le prénom et "
    "le nom de l’autre. Un même "
    "prénom + nom porté par plus de {} fiches sans autre lien n’est pas proposé (homonymes)."
    .format(NOM_COURANT - 1),
    "Règle bloquante : prénoms incompatibles (deux prénoms complets différents, initiales qui ne "
    "correspondent pas) : la paire n’est jamais groupée, elle figure dans « Personnes "
    "distinctes ».",
    "Règle stricte des groupes : dans un groupe Certain, toutes les paires sont Certain ; une "
    "fiche liée à une partie seulement du groupe va dans un groupe Probable « lien indirect "
    "(chaînage) ».",
    "Webmails : gmail, yahoo, hotmail, outlook, live, orange, wanadoo, free, sfr, laposte, "
    "icloud, me, aol (jamais « même domaine email »). Civilités retirées des prénoms et noms.",
    "Racine suggérée : email valide et non en échec, puis entreprise associée, activité la plus "
    "récente, fiche la plus complète. La fusion choisit sa fiche principale elle-même.",
    "Ordre de la chaîne : 1. détection des entreprises, relecture ; 2. fusion des entreprises ; "
    "3. nouvelle extraction puis détection des contacts ; 4. fusion des contacts.",
]


def synthese(analyse, source, horodatage, comparaison=None, avertissements=()):
    c = analyse.compteurs()
    lignes = [("titre", "Doublons — contacts HubSpot", None),
              ("texte", "Analyse du {} — source : {}".format(
                  horodatage.strftime("%d/%m/%Y à %H:%M"), source), None),
              ("vide", "", None),
              ("texte", "Contacts analysés", len(analyse.fiches)),
              ("texte", "Groupes « Certain » (fusionnés)", c[CERTAIN][0]),
              ("texte", "Fiches « Certain »", c[CERTAIN][1]),
              ("texte", "Groupes « Probable »", c[PROBABLE][0]),
              ("texte", "… dont lien indirect (chaînage)", c["chainage"]),
              ("texte", "Fiches « Probable »", c[PROBABLE][1])]
    for _, _, onglet, _ in ONGLETS_RELECTURE:
        lignes.append(("texte", "{} (hors liste) : fiches".format(onglet), c[onglet][1]))
    if comparaison:
        lignes += [("vide", "", None), ("section", "Comparaison avec l’ancien classeur", None)]
        lignes += [("texte", evolution, n) for evolution, n in comparaison]
    if avertissements:
        lignes += [("vide", "", None), ("section", "Avertissements", None)]
        lignes += [("paragraphe", a, None) for a in avertissements]
    lignes += [("vide", "", None), ("section", "Comment lire les niveaux", None)]
    lignes += [("paragraphe", t, None) for t in LECTURE_NIVEAUX]
    return lignes


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Détecte les contacts HubSpot en doublon (lecture seule) et produit le "
                    "classeur de relecture lu par fusion_doublons_hubspot.py. À lancer après "
                    "la fusion des entreprises, sur une nouvelle extraction des contacts.")
    parser.add_argument("--depuis-export", metavar="FICHIER",
                        help="export HubSpot (.csv) ou ancien classeur (.xlsx) au lieu de l'API")
    parser.add_argument("-o", "--sortie", default=FICHIER_SORTIE,
                        help="classeur produit (défaut : {})".format(FICHIER_SORTIE))
    parser.add_argument("--ancien", metavar="CLASSEUR",
                        help="ancien classeur de doublons : ajoute l'onglet « Comparaison »")
    parser.add_argument("--portail", default=PORTAIL_DEFAUT, help="ID du portail HubSpot")
    args = parser.parse_args(argv)

    for chemin in (args.depuis_export, args.ancien):
        if chemin and not os.path.isfile(chemin):
            parser.error("fichier introuvable : « {} »".format(chemin))

    avertissements, client = [], None
    if args.depuis_export:
        fiches, absentes = lire_export(args.depuis_export)
        source = "export {}".format(os.path.basename(args.depuis_export))
        for colonne in absentes:
            if colonne in REGLES_PAR_COLONNE:
                message = "Colonne « {} » absente de l'export : règles désactivées : {}.".format(
                    colonne, REGLES_PAR_COLONNE[colonne])
                avertissements.append(message)
                print("  ! " + message)
    else:
        jeton = os.environ.get("HUBSPOT_TOKEN")
        if not jeton:
            parser.error("définir HUBSPOT_TOKEN (jeton d'application privée, lecture seule), "
                         "ou utiliser --depuis-export")
        client, fiches = lire_hubspot(jeton.strip())
        source = "API HubSpot (portail {})".format(args.portail)
    print("{} contacts lus".format(len(fiches)))

    analyse = AnalyseContacts(fiches).executer()
    avertissements += analyse.avertissements
    noms = {}
    if client is not None:
        affichees = {analyse.fiches[m] for groupes in [analyse.doublons] +
                     list(analyse.relecture.values()) for g in groupes for m in g.membres}
        noms = noms_entreprises(client, [f.id_entreprise for f in affichees if not f.entreprise])
    lignes = analyse.lignes(args.portail, noms)
    horodatage = datetime.datetime.now().replace(microsecond=0)

    onglets = [("Doublons", COLONNES, lignes["Doublons"])]
    onglets += [(onglet, COLONNES, lignes[onglet]) for _, _, onglet, _ in ONGLETS_RELECTURE]
    bilan = None
    if args.ancien:
        feuille = next((f for f in ("Doublons", "Doublons certains")
                        if f in de.feuilles_xlsx(args.ancien)), "Doublons")
        comparaison = de.comparer_ancien(args.ancien, lignes, {f.id for f in analyse.fiches},
                                         feuille=feuille, colonne_nom="Nom")
        onglets.append(("Comparaison", de.COLONNES_COMPARAISON, comparaison))
        bilan = de.bilan_comparaison(comparaison)
    de.ecrire_classeur(args.sortie, synthese(analyse, source, horodatage, bilan, avertissements),
                       onglets, horodatage)

    c = analyse.compteurs()
    print("\nCertain : {} groupes ({} fiches) ; Probable : {} groupes ({} fiches, dont {} "
          "liens indirects)".format(c[CERTAIN][0], c[CERTAIN][1], c[PROBABLE][0],
                                    c[PROBABLE][1], c["chainage"]))
    for _, _, onglet, _ in ONGLETS_RELECTURE:
        print("{} : {} groupes, {} fiches".format(onglet, *c[onglet]))
    if bilan:
        print("Comparaison avec l'ancien classeur : " +
              ", ".join("{} {}".format(n, e) for e, n in bilan))
    print("Classeur : {}".format(args.sortie))
    print("Rien n'a été modifié dans HubSpot. Après relecture : "
          "python fusion_doublons_hubspot.py {} --hors-ligne".format(args.sortie))
    return 0


if __name__ == "__main__":
    sys.exit(main())
