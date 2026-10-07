#!/usr/bin/env python3
"""
Fusion des contacts HubSpot en doublon certain, à partir de la liste « Doublons certains »
(export CSV de doublons_potentiels_hubspot.xlsx).

Les fiches d'un même groupe (G-001, G-002...) sont fusionnées en une seule, puis la fiche
obtenue est corrigée selon les règles de fusion Alter Watt :

  Fiche à jour   celle qui renseigne l'entreprise la plus actuelle : on regarde d'abord le
                 dernier email REÇU du contact (échange réel, l'adresse d'envoi désigne la
                 fiche), à défaut la date de création. La date retenue pour chaque fiche est
                 la plus récente des deux.
  Entreprise     celle de la fiche la plus à jour qui en a une : nom de l'entreprise et
                 entreprise associée principale. Une valeur copiée d'un domaine email
                 (« 54.fr ») est ignorée.
  Email          une seule adresse est gardée en email principal (HubSpot conserve l'autre
                 en email secondaire) : celle qui correspond à l'entreprise retenue si
                 possible (même entreprise, ou même boîte sur un domaine mal orthographié),
                 en préférant l'adresse du dernier échange, puis la « Racine suggérée ».
                 Adresses écartées : en échec (hard bounce), punycode « xn-- », domaine
                 invalide. La fiche qui porte cette adresse devient la fiche principale.
  Prénom / Nom   la fiche la mieux renseignée (prénom ET nom, prénom complet plutôt qu'une
                 initiale, forme la plus complète ; à égalité, la graphie la plus répandue).
                 Prénom avec accents (« Sophie-Anne »), NOM en majuscules (« DUCHENE »).
                 Nom complet saisi dans un seul champ (« Rémy Viallet ») : redécoupé seulement
                 si l'email le confirme (remy.viallet@).
  Téléphone      dès qu'une fiche en a un, il est repris (celui de la fiche la plus à jour
                 s'il y en a plusieurs). Idem pour le mobile. Les numéros non repris sont
                 listés dans le rapport.
  Poste          celui de la fiche la plus à jour qui en a un.
  Propriétaire   toujours un utilisateur actif quand une des fiches en a un (celui de la
                 fiche principale en priorité) ; un propriétaire désactivé n'est gardé que
                 si aucun n'est actif.

Sécurités :
  - par défaut, SIMULATION : rien n'est modifié, le rapport montre ce qui serait fait ;
  - --executer fusionne réellement (irréversible), après confirmation ;
  - un groupe dont les prénoms se contredisent n'est pas fusionné (« À VÉRIFIER »).
  - relancer le script est sans risque : les groupes déjà fusionnés sont détectés.

Aucune dépendance externe : uniquement la bibliothèque standard Python (3.8+).

Exemples :
  python fusion_doublons_hubspot.py doublons.csv --hors-ligne        # aperçu sans HubSpot
  python fusion_doublons_hubspot.py doublons.csv                     # simulation, fiches lues dans HubSpot
  python fusion_doublons_hubspot.py doublons.csv --groupes G-001,G-002 --executer
  python fusion_doublons_hubspot.py doublons.csv --executer

Accès HubSpot : variable d'environnement HUBSPOT_TOKEN = jeton d'une application privée
avec les droits crm.objects.contacts.read, crm.objects.contacts.write,
crm.objects.companies.read, crm.objects.owners.read et sales-email-read
(lecture des emails échangés).
"""

import argparse
import csv
import difflib
import io
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

API_URL = "https://api.hubapi.com"
PORTAIL_DEFAUT = "20368543"
LIEN_FICHE = "https://app-eu1.hubspot.com/contacts/{portail}/record/0-1/{id}"

# Limite des applications privées : 100 requêtes / 10 s. On reste en dessous.
DELAI_ENTRE_REQUETES = 0.15

# Deux adresses de même partie locale sur des domaines aussi proches = même boîte
# (« nantesmetropole.fr » / « nantesmetrople.fr »).
SEUIL_MEME_BOITE = 0.75

PROPRIETES = ["firstname", "lastname", "email", "hs_additional_emails", "phone", "mobilephone",
              "jobtitle", "company", "associatedcompanyid", "hubspot_owner_id", "createdate",
              "hs_email_hard_bounce_reason_enum"]

# Association contact -> entreprise « principale » (définie par HubSpot).
TYPE_ASSOCIATION_PRINCIPALE = 1

PARTICULES = {"de", "du", "des", "van", "von"}

# Civilités et titres saisis dans le champ prénom ou nom (« M. Rault », « Madame »).
CIVILITES = {"m", "mr", "mme", "mlle", "monsieur", "madame", "mademoiselle", "abbe", "pere",
             "soeur", "dr", "docteur", "me", "maitre", "mrics"}

COLONNES = {
    "groupe": "Groupe",
    "racine": "Racine suggérée",
    "id": "ID HubSpot",
    "prenom": "Prénom",
    "nom": "Nom",
    "email": "E-mail",
    "telephone": "Téléphone",
    "entreprise": "Entreprise",
    "poste": "Intitulé du poste",
    "proprietaire": "Propriétaire du contact",
    "creation": "Date de création",
}

ENTETES_RAPPORT = [
    "Groupe", "Statut", "Fiches du groupe", "Fiche principale", "Fiche la plus à jour",
    "Dernier email reçu", "ID final", "Lien HubSpot",
    "Prénom", "Nom", "Email principal", "Autres emails", "Téléphone", "Mobile",
    "Intitulé du poste", "Entreprise", "ID entreprise principale", "Propriétaire",
    "Numéros non repris", "Remarques",
]


# --------------------------------------------------------------------------- #
# Normalisation
# --------------------------------------------------------------------------- #

def sans_accents(texte):
    texte = unicodedata.normalize("NFKD", texte or "")
    return "".join(c for c in texte if not unicodedata.combining(c))


def normaliser(texte):
    """Minuscules, sans accents, tirets et espaces multiples réduits à un espace."""
    texte = sans_accents(texte).lower().replace("’", "'")
    texte = re.sub(r"[\s\-_.]+", " ", texte)
    return texte.strip()


def chiffres(numero):
    """Numéro réduit à ses chiffres, au format national (0X XX XX XX XX)."""
    d = re.sub(r"\D", "", numero or "")
    if d.startswith("0033"):
        d = d[4:]
    elif d.startswith("330") and len(d) == 12:   # +33 (0)6 ...
        d = d[3:]
    elif d.startswith("33") and len(d) == 11:
        d = d[2:]
    if len(d) == 9:
        d = "0" + d
    return d


def est_mobile(numero):
    return chiffres(numero)[:2] in ("06", "07")


def retirer_civilite(texte):
    """(« M. Frederic BEAU », True) -> (« Frederic BEAU », True) : civilités de tête retirées."""
    mots = (texte or "").split()
    retiree = False
    while mots and normaliser(mots[0]) in CIVILITES:
        mots.pop(0)
        retiree = True
    return " ".join(mots), retiree


def nettoyer_nom(prenom, nom):
    """Prénom et nom débarrassés des civilités. « M Derveau » sans nom : c'est un nom."""
    prenom, civilite = retirer_civilite(prenom)
    nom, _ = retirer_civilite(nom)
    if civilite and not nom:
        prenom, nom = "", prenom
    return prenom, nom


def ressemble_domaine(texte):
    """« 54.fr », « archoise.org » : entreprise remplie automatiquement depuis l'email."""
    return bool(re.fullmatch(r"[\w-]+(\.[\w-]+)+", (texte or "").strip()))


def est_initiale(prenom):
    return len(normaliser(prenom).replace(" ", "")) <= 1


def casse_nom(texte):
    """Casse maison : « DUCHENE » -> « Duchene », « JEAN-PIERRE » -> « Jean-Pierre »,
    « DE VILLIERS » -> « de Villiers », « D'HALLUIN » -> « d'Halluin »."""
    def mot(m):
        if re.search(r"[^\w'’-]|\d", m):              # « R&D », « 8e » : laissés tels quels
            return m
        bas = m.lower()
        if bas in PARTICULES:
            return bas
        if bas.startswith(("d'", "d’")) and len(bas) > 2:
            return "d'" + mot(m[2:])
        return "-".join("'".join(p[:1].upper() + p[1:] for p in morceau.split("'"))
                        for morceau in bas.split("-"))
    mots = [mot(m) for m in texte.split()]
    if mots and mots[0] in PARTICULES and len(mots) == 1:
        mots[0] = mots[0].capitalize()
    return " ".join(mots)


def graphie(variantes):
    """Meilleure graphie parmi des variantes d'un même nom : pas en tout-majuscules,
    avec le plus d'accents. Les variantes arrivent par ordre de préférence."""
    def score(v):
        lettres = [c for c in v if c.isalpha()]
        majuscules = bool(lettres) and all(c.isupper() for c in lettres)
        minuscules = bool(lettres) and all(c.islower() for c in lettres)
        accents = sum(1 for c in v if ord(c) > 127)
        return (not majuscules and not minuscules, accents)
    def score_mots(v):
        return (not any(len(m) > 1 and m.isupper() for m in re.split(r"[\s-]+", v)),) + score(v)
    meilleure = max(variantes, key=score_mots)  # max garde la 1re en cas d'égalité
    mots = re.split(r"[\s-]+", meilleure)
    if meilleure.islower() or any(len(m) > 1 and m.isupper() for m in mots):
        meilleure = casse_nom(meilleure)
    return meilleure


def email_valide(email):
    m = re.fullmatch(r"[^@\s]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,})", email or "")
    if not m:
        return False
    domaine = m.group(1).lower()
    return not any(part.startswith("xn--") for part in domaine.split("."))


# --------------------------------------------------------------------------- #
# Fiches
# --------------------------------------------------------------------------- #

class Fiche:
    """Une fiche contact, lue dans HubSpot ou dans le CSV."""

    def __init__(self, id, prenom="", nom="", email="", telephone="", mobile="", poste="",
                 entreprise="", id_entreprise="", proprietaire="", proprietaire_actif=None,
                 creation="", en_echec=False, racine=False, emails_secondaires="",
                 dernier_echange="", adresse_echange=""):
        self.id = str(id)
        self.prenom = (prenom or "").strip()
        self.nom = (nom or "").strip()
        self.email = (email or "").strip()
        self.telephone = (telephone or "").strip()
        self.mobile = (mobile or "").strip()
        self.poste = (poste or "").strip()
        self.entreprise = (entreprise or "").strip()
        self.id_entreprise = str(id_entreprise or "").strip()
        self.proprietaire = str(proprietaire or "").strip()
        self.proprietaire_actif = proprietaire_actif
        self.creation = creation or ""
        self.en_echec = en_echec
        self.racine = racine
        self.emails_secondaires = emails_secondaires or ""
        # Dernier email reçu du contact (date triable) et adresse d'où il l'a envoyé.
        self.dernier_echange = dernier_echange or ""
        self.adresse_echange = (adresse_echange or "").strip().lower()
        # Prénom et nom sans civilité, utilisés pour décider ; les champs bruts servent
        # à détecter ce qu'il faut corriger dans HubSpot.
        self.prenom_net, self.nom_net = nettoyer_nom(self.prenom, self.nom)

    def __repr__(self):
        return "Fiche({} {} {} <{}>)".format(self.id, self.prenom, self.nom, self.email)


def date_iso(valeur):
    """« 2023-09-05 17:23 » ou « 2023-09-05T15:23:58.243Z » -> chaîne triable."""
    return (valeur or "").replace("T", " ").replace("Z", "")[:19]


def fiche_depuis_csv(ligne):
    """Fiche construite à partir du seul CSV (mode --hors-ligne)."""
    entreprise = ligne.get(COLONNES["entreprise"], "").strip()
    id_entreprise = ""
    if entreprise.isdigit():           # le CSV affiche l'ID quand le nom n'est pas renseigné
        id_entreprise, entreprise = entreprise, ""
    proprietaire = ligne.get(COLONNES["proprietaire"], "").strip()
    actif = None
    if proprietaire:
        actif = "deactivated" not in proprietaire.lower()
    telephone = ligne.get(COLONNES["telephone"], "")
    return Fiche(
        id=ligne[COLONNES["id"]].strip(),
        prenom=ligne.get(COLONNES["prenom"], ""),
        nom=ligne.get(COLONNES["nom"], ""),
        email=ligne.get(COLONNES["email"], ""),
        telephone=telephone,
        poste=ligne.get(COLONNES["poste"], ""),
        entreprise=entreprise,
        id_entreprise=id_entreprise,
        proprietaire=proprietaire,
        proprietaire_actif=actif,
        creation=date_iso(ligne.get(COLONNES["creation"], "")),
        racine=ligne.get(COLONNES["racine"], "").strip().lower() == "oui",
    )


def actualite(fiche):
    """Date la plus récente qui atteste de la situation de la fiche."""
    return max(fiche.creation, fiche.dernier_echange)


def plus_a_jour(fiches):
    """Fiches de la plus à jour à la moins à jour (dernier échange reçu, sinon création)."""
    return sorted(fiches, key=lambda f: (actualite(f), f.creation), reverse=True)


def attribuer_echanges(fiches):
    """Un email reçu depuis l'adresse d'une autre fiche du groupe compte pour cette fiche."""
    for f in fiches:
        if not f.adresse_echange or f.adresse_echange == f.email.lower():
            continue
        autre = next((g for g in fiches if g.email.lower() == f.adresse_echange), None)
        if autre is not None and f.dernier_echange > autre.dernier_echange:
            autre.dernier_echange, f.dernier_echange = f.dernier_echange, ""


# --------------------------------------------------------------------------- #
# Règles de fusion
# --------------------------------------------------------------------------- #

def prenoms_compatibles(a, b):
    """Faux seulement si les deux fiches ont un prénom et qu'ils désignent deux personnes."""
    pa, pb = normaliser(a.prenom_net), normaliser(b.prenom_net)
    if not pa or not pb or pa == pb:
        return True
    if est_initiale(pa) or est_initiale(pb):
        return pa[0] == pb[0]
    if pa.startswith(pb + " ") or pb.startswith(pa + " "):        # Sophie / Sophie-Anne
        return True
    if pa == normaliser(b.nom_net) and pb == normaliser(a.nom_net):  # prénom et nom inversés
        return True
    return difflib.SequenceMatcher(None, pa, pb).ratio() >= 0.85   # faute de frappe


def sans_prenom_en_tete(nom, prenom):
    """« Jacques Montagne » sans « Jacques » -> « Montagne » ; None si absent."""
    p, n = normaliser(prenom), normaliser(nom)
    if p and n.startswith(p + " "):
        mots = nom.split()
        return " ".join(mots[len(prenom.split()):]).strip(" -") or None
    return None


def nom_sans_prenom(fiche):
    """Retire le prénom recopié en tête du nom (« Jacques » / « Jacques Montagne »)."""
    return sans_prenom_en_tete(fiche.nom_net, fiche.prenom_net) or fiche.nom_net


def contient(a, b):
    """Vrai si les mots de b forment une suite de ceux de a (ou l'inverse)."""
    a, b = " " + normaliser(a) + " ", " " + normaliser(b) + " "
    return a in b or b in a


def decouper_par_email(nom_complet, emails):
    """« Rémy Viallet » + remy.viallet@ -> (« Rémy », « Viallet ») ; sinon None."""
    mots = nom_complet.split()
    if len(mots) < 2:
        return None
    for email in emails:
        local = normaliser(email.split("@")[0])
        for i in range(1, len(mots)):
            prenom, nom = " ".join(mots[:i]), " ".join(mots[i:])
            p, n = normaliser(prenom).replace(" ", ""), normaliser(nom).replace(" ", "")
            if local.replace(" ", "") in (p + n, p[:1] + n) or local in (p + " " + n,
                                                                       p[:1] + " " + n):
                return prenom, nom
    return None


def choisir_nom(fiches, principale):
    """(prénom, nom, remarque) les mieux renseignés du groupe."""
    ordre = [principale] + [f for f in plus_a_jour(fiches) if f is not principale]
    completes = [(f, f.prenom_net, nom_sans_prenom(f)) for f in ordre
                 if f.prenom_net and f.nom_net]
    completes = [c for c in completes if c[2]]
    if not completes:
        emails = [f.email for f in ordre if f.email]
        for f in ordre:
            complet = f.nom_net if not f.prenom_net else f.prenom_net if not f.nom_net else ""
            decoupe = decouper_par_email(complet, emails) if complet else None
            if decoupe:
                return (graphie([decoupe[0]]), decoupe[1].upper(),
                        "nom complet redécoupé d'après l'email")
        return principale.prenom, principale.nom.upper(), "aucune fiche avec prénom et nom"

    # Prénom complet plutôt qu'une initiale, puis la répartition prénom/nom la plus répandue.
    pleines = [c for c in completes if not est_initiale(c[1])] or completes
    votes = {}
    for _, prenom, nom in pleines:
        cle = (normaliser(prenom), normaliser(nom))
        votes[cle] = votes.get(cle, 0) + 1
    cle = max(votes, key=votes.get)          # à égalité : la principale, puis la plus récente

    # Forme la plus complète d'un même prénom ou nom (« Sophie » / « Sophie-Anne »,
    # « Nevers » / « Nevers-Brunel ») ; un nom complet saisi dans le seul champ nom compte.
    prenoms = [p for _, p, _ in pleines if contient(p, cle[0])]
    noms = [n for _, p, n in completes if contient(n, cle[1]) and contient(p, cle[0])]
    for f in ordre:
        if not f.prenom_net and f.nom_net:
            for prenom in prenoms:
                reste = sans_prenom_en_tete(f.nom_net, prenom)
                if reste and contient(reste, cle[1]):
                    noms.append(reste)
    long_p = max(len(normaliser(p)) for p in prenoms)
    long_n = max(len(normaliser(n)) for n in noms)
    prenoms = [p for p in prenoms if len(normaliser(p)) == long_p]
    noms = [n for n in noms if len(normaliser(n)) == long_n]
    prenom, nom = graphie(prenoms), graphie(noms).upper()

    remarque = ""
    if len(votes) > 1 or (normaliser(prenom), normaliser(nom)) != cle:
        remarque = "prénom/nom différents selon les fiches, retenu : {} {}".format(prenom, nom)
    return prenom, nom, remarque


def meme_boite(email_a, email_b):
    """Même partie locale sur deux domaines très proches (faute de frappe)."""
    if "@" not in email_a or "@" not in email_b:
        return False
    (la, da), (lb, db) = (e.lower().rsplit("@", 1) for e in (email_a, email_b))
    return la == lb and difflib.SequenceMatcher(None, da, db).ratio() >= SEUIL_MEME_BOITE


def choisir_entreprise(fiches):
    """Fiche dont on garde l'entreprise : la plus à jour qui en a une vraie."""
    ordre = plus_a_jour(fiches)
    return (next((f for f in ordre if f.entreprise and not ressemble_domaine(f.entreprise)), None)
            or next((f for f in ordre if f.entreprise or f.id_entreprise), None))


def meme_entreprise(fiche, reference):
    if fiche is reference:
        return True
    if fiche.id_entreprise and fiche.id_entreprise == reference.id_entreprise:
        return True
    if fiche.entreprise and normaliser(fiche.entreprise) == normaliser(reference.entreprise):
        return True
    return meme_boite(fiche.email, reference.email)


def choisir_email(fiches, reference):
    """Fiche dont l'adresse devient l'email principal : celle de l'entreprise retenue si
    possible ; puis l'adresse du dernier échange, la racine suggérée, la plus à jour."""
    candidates = [f for f in fiches if f.email and email_valide(f.email) and not f.en_echec]
    if not candidates:
        candidates = [f for f in fiches if f.email] or list(fiches)
    if reference is not None:
        candidates = [f for f in candidates if meme_entreprise(f, reference)] or candidates
    return max(candidates, key=lambda f: (f.dernier_echange, f.racine, actualite(f), f.creation))


def choisir_telephones(fiches):
    """(fixe, mobile, numéros non repris) : le plus récent de chaque, sans rien perdre."""
    recentes = plus_a_jour(fiches)
    fixe = next((f.telephone for f in recentes if f.telephone), "")
    mobile = next((f.mobile for f in recentes if f.mobile), "")
    gardes = {chiffres(fixe), chiffres(mobile)} - {""}
    restants = []
    for f in recentes:
        for numero in (f.telephone, f.mobile):
            c = chiffres(numero)
            if c and c not in gardes:
                if not mobile and est_mobile(numero):
                    mobile = numero
                else:
                    restants.append(numero)
                gardes.add(c)
    return fixe, mobile, restants


def choisir_proprietaire(fiches, principale):
    candidats = [principale] + plus_a_jour([f for f in fiches if f is not principale])
    actif = next((f for f in candidats if f.proprietaire and f.proprietaire_actif), None)
    if actif:
        return actif.proprietaire, ""
    present = next((f for f in candidats if f.proprietaire), None)
    if present and present.proprietaire_actif is None:
        return present.proprietaire, "statut des propriétaires inconnu"
    if present:
        return present.proprietaire, "aucun propriétaire actif : propriétaire désactivé conservé"
    return "", ""


def planifier(groupe, fiches):
    """Valeurs cibles de la fiche fusionnée, ou statut « À VÉRIFIER »."""
    plan = {"groupe": groupe, "fiches": fiches, "remarques": []}
    for i, a in enumerate(fiches):
        for b in fiches[i + 1:]:
            if not prenoms_compatibles(a, b):
                plan["statut"] = "À VÉRIFIER"
                plan["remarques"].append("prénoms différents : « {} » / « {} »"
                                         .format(a.prenom, b.prenom))
                return plan

    attribuer_echanges(fiches)
    source_entreprise = choisir_entreprise(fiches)
    principale = choisir_email(fiches, source_entreprise)
    prenom, nom, remarque = choisir_nom(fiches, principale)
    fixe, mobile, restants = choisir_telephones(fiches)
    recentes = plus_a_jour(fiches)
    poste = next((f.poste for f in recentes if f.poste), "")
    id_entreprise = source_entreprise.id_entreprise if source_entreprise else ""
    if source_entreprise and not id_entreprise:
        # Même entreprise (nom identique) associée sur une autre fiche : on la reprend.
        id_entreprise = next((f.id_entreprise for f in recentes if f.id_entreprise and
                              normaliser(f.entreprise) == normaliser(source_entreprise.entreprise)),
                             "")
    proprietaire, remarque_proprio = choisir_proprietaire(fiches, principale)

    plan.update({
        "statut": "À FUSIONNER",
        "principale": principale,
        "autres": [f for f in fiches if f is not principale],
        "prenom": prenom, "nom": nom,
        "email": principale.email,
        "autres_emails": [f.email for f in fiches if f.email and f.email != principale.email],
        "telephone": fixe, "mobile": mobile, "non_repris": restants,
        "poste": poste,
        "entreprise": source_entreprise.entreprise if source_entreprise else "",
        "id_entreprise": id_entreprise,
        "proprietaire": proprietaire,
        "reference": source_entreprise,
        "dernier_echange": max((f.dernier_echange for f in fiches), default=""),
    })
    plan["remarques"] += [r for r in (remarque, remarque_proprio) if r]
    if source_entreprise and not meme_entreprise(principale, source_entreprise):
        plan["remarques"].append("pas d'adresse email pour l'entreprise retenue : "
                                 "email d'une autre entreprise conservé")
    if principale.en_echec or (principale.email and not email_valide(principale.email)):
        plan["remarques"].append("aucune adresse sûre : email à vérifier")
    return plan


# --------------------------------------------------------------------------- #
# HubSpot
# --------------------------------------------------------------------------- #

class ErreurHubSpot(Exception):
    def __init__(self, statut, message):
        super().__init__("HTTP {} : {}".format(statut, message))
        self.statut = statut


class ClientHubSpot:
    def __init__(self, jeton, delai=DELAI_ENTRE_REQUETES, timeout=30):
        self.jeton = jeton
        self.delai = delai
        self.timeout = timeout
        self._dernier = 0.0
        self._noms_entreprises = {}
        self._proprietaires_actifs = None
        self._echanges_lisibles = True

    def requete(self, methode, chemin, corps=None, essais=4):
        for essai in range(essais):
            attente = self.delai - (time.time() - self._dernier)
            if attente > 0:
                time.sleep(attente)
            self._dernier = time.time()
            donnees = json.dumps(corps).encode("utf-8") if corps is not None else None
            req = urllib.request.Request(API_URL + chemin, data=donnees, method=methode)
            req.add_header("Authorization", "Bearer " + self.jeton)
            req.add_header("Content-Type", "application/json")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as rep:
                    texte = rep.read().decode("utf-8")
                    return json.loads(texte) if texte else {}
            except urllib.error.HTTPError as e:
                texte = e.read().decode("utf-8", "replace")
                if e.code == 429 or e.code >= 500:
                    time.sleep(float(e.headers.get("Retry-After") or 2 ** (essai + 1)))
                    continue
                try:
                    texte = json.loads(texte).get("message", texte)
                except ValueError:
                    pass
                raise ErreurHubSpot(e.code, texte)
            except urllib.error.URLError as e:
                if essai == essais - 1:
                    raise ErreurHubSpot(0, str(e.reason))
                time.sleep(2 ** (essai + 1))
        raise ErreurHubSpot(429, "trop de requêtes, réessayer plus tard")

    def proprietaires_actifs(self, strict=False):
        """IDs des propriétaires actifs (ensemble vide si le droit owners.read manque)."""
        if self._proprietaires_actifs is None:
            actifs, apres = set(), None
            try:
                while True:
                    chemin = "/crm/v3/owners?limit=500&archived=false"
                    if apres:
                        chemin += "&after=" + urllib.parse.quote(apres)
                    rep = self.requete("GET", chemin)
                    actifs.update(str(o["id"]) for o in rep.get("results", []))
                    apres = rep.get("paging", {}).get("next", {}).get("after")
                    if not apres:
                        break
            except ErreurHubSpot as e:
                if strict:
                    raise
                print("  ! propriétaires non lus ({}) : propriétaires actifs inconnus".format(e),
                      file=sys.stderr)
                actifs = set()
            self._proprietaires_actifs = actifs
        return self._proprietaires_actifs

    def nom_entreprise(self, id_entreprise):
        if id_entreprise not in self._noms_entreprises:
            try:
                rep = self.requete("GET", "/crm/v3/objects/companies/{}?properties=name"
                                   .format(id_entreprise))
                nom = rep.get("properties", {}).get("name") or ""
            except ErreurHubSpot:
                nom = ""
            self._noms_entreprises[id_entreprise] = nom
        return self._noms_entreprises[id_entreprise]

    def dernier_email_recu(self, id_contact):
        """(date, adresse d'envoi) du dernier email reçu de ce contact, ou ("", "")."""
        if not self._echanges_lisibles:
            return "", ""
        corps = {
            "filterGroups": [{"filters": [
                {"propertyName": "associations.contact", "operator": "EQ",
                 "value": str(id_contact)},
                {"propertyName": "hs_email_direction", "operator": "EQ",
                 "value": "INCOMING_EMAIL"}]}],
            "sorts": [{"propertyName": "hs_timestamp", "direction": "DESCENDING"}],
            "properties": ["hs_timestamp", "hs_email_from_email"],
            "limit": 1,
        }
        try:
            rep = self.requete("POST", "/crm/v3/objects/emails/search", corps)
        except ErreurHubSpot as e:
            if e.statut in (401, 403):
                print("  ! emails non lisibles ({}) : entreprise choisie sur la date de "
                      "création".format(e), file=sys.stderr)
                self._echanges_lisibles = False
                return "", ""
            raise
        for email in rep.get("results", []):
            p = email.get("properties", {})
            return date_iso(p.get("hs_timestamp")), p.get("hs_email_from_email") or ""
        return "", ""

    def lire_contact(self, id_contact):
        """Brut HubSpot du contact, ou None s'il n'existe plus.
        Un ID déjà fusionné renvoie la fiche issue de la fusion (autre ID)."""
        chemin = "/crm/v3/objects/contacts/{}?properties={}&associations=companies".format(
            id_contact, ",".join(PROPRIETES))
        try:
            return self.requete("GET", chemin)
        except ErreurHubSpot as e:
            if e.statut == 404:
                return None
            raise

    def fiche(self, id_contact, racine=False):
        brut = self.lire_contact(id_contact)
        if brut is None:
            return None
        p = brut.get("properties", {})
        id_entreprise = p.get("associatedcompanyid") or ""
        for assoc in brut.get("associations", {}).get("companies", {}).get("results", []):
            if assoc.get("type") == "contact_to_company":      # association principale
                id_entreprise = str(assoc["id"])
        entreprise = (p.get("company") or "").strip()
        if not entreprise and id_entreprise:
            entreprise = self.nom_entreprise(id_entreprise)
        actifs = self.proprietaires_actifs()
        proprietaire = p.get("hubspot_owner_id") or ""
        dernier_echange, adresse_echange = self.dernier_email_recu(brut["id"])
        return Fiche(
            id=brut["id"], prenom=p.get("firstname"), nom=p.get("lastname"),
            email=p.get("email"), telephone=p.get("phone"), mobile=p.get("mobilephone"),
            poste=p.get("jobtitle"), entreprise=entreprise, id_entreprise=id_entreprise,
            proprietaire=proprietaire,
            proprietaire_actif=(proprietaire in actifs) if actifs else None,
            creation=date_iso(p.get("createdate") or brut.get("createdAt")),
            en_echec=bool(p.get("hs_email_hard_bounce_reason_enum")),
            racine=racine, emails_secondaires=p.get("hs_additional_emails"),
            dernier_echange=dernier_echange, adresse_echange=adresse_echange,
        )

    def fusionner(self, id_principal, id_a_fusionner):
        rep = self.requete("POST", "/crm/v3/objects/contacts/merge",
                           {"primaryObjectId": str(id_principal),
                            "objectIdToMerge": str(id_a_fusionner)})
        return str(rep.get("id") or id_principal)

    def modifier(self, id_contact, proprietes):
        self.requete("PATCH", "/crm/v3/objects/contacts/{}".format(id_contact),
                     {"properties": proprietes})

    def entreprise_principale(self, id_contact, id_entreprise):
        self.requete("PUT", "/crm/v4/objects/contact/{}/associations/company/{}"
                     .format(id_contact, id_entreprise),
                     [{"associationCategory": "HUBSPOT_DEFINED",
                       "associationTypeId": TYPE_ASSOCIATION_PRINCIPALE}])


def corrections(plan, fiche):
    """Propriétés à écrire sur la fiche fusionnée : uniquement les écarts."""
    cibles = {"firstname": (plan["prenom"], fiche.prenom),
              "lastname": (plan["nom"], fiche.nom),
              "phone": (plan["telephone"], fiche.telephone),
              "mobilephone": (plan["mobile"], fiche.mobile),
              "jobtitle": (plan["poste"], fiche.poste),
              "company": (plan["entreprise"], fiche.entreprise),
              "hubspot_owner_id": (plan["proprietaire"], fiche.proprietaire)}
    return {k: v for k, (v, actuel) in cibles.items() if v and v != actuel}


def lire_fiche_fusionnee(client, id_contact, essais=5):
    """La fiche issue d'une fusion peut mettre quelques secondes à être lisible."""
    for essai in range(essais):
        fiche = client.fiche(id_contact)
        if fiche is not None:
            return fiche
        time.sleep(2 * (essai + 1))
    raise ErreurHubSpot(404, "fiche fusionnée {} introuvable".format(id_contact))


def executer(client, plan):
    """Fusionne le groupe puis corrige la fiche obtenue. Renvoie l'ID final."""
    id_final = plan["principale"].id
    for autre in plan["autres"]:
        id_final = client.fusionner(id_final, autre.id)
    plan["statut"] = "FUSIONNÉ"
    try:
        fiche = lire_fiche_fusionnee(client, id_final)
        a_ecrire = corrections(plan, fiche)
        if a_ecrire:
            client.modifier(id_final, a_ecrire)
        if plan["id_entreprise"] and plan["id_entreprise"] != fiche.id_entreprise:
            client.entreprise_principale(id_final, plan["id_entreprise"])
        if plan["email"] and fiche.email and fiche.email.lower() != plan["email"].lower():
            plan["remarques"].append("HubSpot a gardé {} en email principal".format(fiche.email))
    except ErreurHubSpot as e:
        plan["statut"] = "FUSIONNÉ - CORRECTIONS À FAIRE"
        plan["remarques"].append(str(e))
    return id_final


# --------------------------------------------------------------------------- #
# CSV et rapport
# --------------------------------------------------------------------------- #

def lire_csv(chemin):
    with open(chemin, "rb") as f:
        brut = f.read()
    for encodage in ("utf-8-sig", "cp1252"):
        try:
            texte = brut.decode(encodage)
            break
        except UnicodeDecodeError:
            continue
    separateur = ";" if texte.splitlines()[0].count(";") > texte.splitlines()[0].count(",") else ","
    lignes = list(csv.DictReader(io.StringIO(texte), delimiter=separateur))
    manquantes = [c for c in ("groupe", "id") if COLONNES[c] not in (lignes[0] if lignes else {})]
    if manquantes:
        raise SystemExit("Colonnes absentes du CSV : " + ", ".join(COLONNES[c] for c in manquantes))
    return lignes


def grouper(lignes, filtre=None):
    groupes = {}
    for ligne in lignes:
        g = ligne[COLONNES["groupe"]].strip()
        if g and (not filtre or g in filtre):
            groupes.setdefault(g, []).append(ligne)
    return groupes


def ligne_rapport(plan, portail, id_final=""):
    fiches = plan["fiches"]
    ligne = {
        "Groupe": plan["groupe"],
        "Statut": plan["statut"],
        "Fiches du groupe": " ; ".join(f.id for f in fiches),
        "Remarques": " ; ".join(plan["remarques"]),
    }
    if "principale" in plan:
        id_lien = id_final or plan["principale"].id
        ligne.update({
            "Fiche principale": plan["principale"].id,
            "Fiche la plus à jour": plan["reference"].id if plan["reference"] else "",
            "Dernier email reçu": plan["dernier_echange"],
            "ID final": id_final,
            "Lien HubSpot": LIEN_FICHE.format(portail=portail, id=id_lien),
            "Prénom": plan["prenom"], "Nom": plan["nom"],
            "Email principal": plan["email"],
            "Autres emails": " ; ".join(plan["autres_emails"]),
            "Téléphone": plan["telephone"], "Mobile": plan["mobile"],
            "Intitulé du poste": plan["poste"], "Entreprise": plan["entreprise"],
            "ID entreprise principale": plan["id_entreprise"],
            "Propriétaire": plan["proprietaire"],
            "Numéros non repris": " ; ".join(plan["non_repris"]),
        })
    return ligne


def ecrire_rapport(chemin, lignes):
    with open(chemin, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ENTETES_RAPPORT, delimiter=";")
        w.writeheader()
        w.writerows(lignes)


# --------------------------------------------------------------------------- #
# Programme principal
# --------------------------------------------------------------------------- #

def fiches_du_groupe(lignes, client):
    """Fiches du groupe, sans doublon d'ID (un ID déjà fusionné renvoie la fiche finale)."""
    fiches, vues, absentes = [], set(), []
    for ligne in lignes:
        racine = ligne.get(COLONNES["racine"], "").strip().lower() == "oui"
        if client is None:
            fiche = fiche_depuis_csv(ligne)
        else:
            fiche = client.fiche(ligne[COLONNES["id"]].strip(), racine=racine)
        if fiche is None:
            absentes.append(ligne[COLONNES["id"]].strip())
        elif fiche.id in vues:
            existante = next(f for f in fiches if f.id == fiche.id)
            existante.racine = existante.racine or racine
        else:
            vues.add(fiche.id)
            fiches.append(fiche)
    return fiches, absentes


def traiter(chemin, chemin_rapport, client=None, reel=False, filtre=None, limite=None,
            portail=PORTAIL_DEFAUT, journal=print):
    groupes = grouper(lire_csv(chemin), filtre)
    rapport, compteur = [], {}
    for n, (groupe, lignes) in enumerate(sorted(groupes.items())):
        if limite is not None and n >= limite:
            break
        try:
            fiches, absentes = fiches_du_groupe(lignes, client)
            if len(fiches) < 2:
                plan = {"groupe": groupe, "fiches": fiches, "statut": "DÉJÀ FUSIONNÉ",
                        "remarques": ["fiches absentes : " + ", ".join(absentes)] if absentes
                        else ["les fiches ne forment déjà plus qu'une"]}
                if not fiches:
                    plan["statut"] = "INTROUVABLE"
                    plan["remarques"] = ["fiches introuvables (supprimées ?) : " + ", ".join(absentes)]
            else:
                plan = planifier(groupe, fiches)
                if absentes:
                    plan["remarques"].append("fiches absentes : " + ", ".join(absentes))
            id_final = ""
            if plan["statut"] == "À FUSIONNER":
                if reel:
                    id_final = executer(client, plan)
                else:
                    plan["statut"] = "SIMULATION"
        except ErreurHubSpot as e:
            plan = {"groupe": groupe, "fiches": [], "statut": "ERREUR", "remarques": [str(e)]}
            id_final = ""
        ligne = ligne_rapport(plan, portail, id_final)
        rapport.append(ligne)
        compteur[plan["statut"]] = compteur.get(plan["statut"], 0) + 1
        journal("{} {:<30} {} {}".format(groupe, plan["statut"],
                                         ligne.get("Prénom", ""), ligne.get("Nom", "")).rstrip())
    ecrire_rapport(chemin_rapport, rapport)
    return compteur


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Fusionne les contacts HubSpot en doublon certain (liste par groupe).")
    parser.add_argument("csv", help="CSV « Doublons certains » (colonnes Groupe, ID HubSpot...)")
    parser.add_argument("--executer", action="store_true",
                        help="fusionner réellement dans HubSpot (irréversible)")
    parser.add_argument("--oui", action="store_true",
                        help="ne pas demander de confirmation avant de fusionner")
    parser.add_argument("--hors-ligne", action="store_true",
                        help="aperçu à partir du seul CSV, sans appeler HubSpot")
    parser.add_argument("--groupes", help="groupes à traiter, ex. G-001,G-002")
    parser.add_argument("--limite", type=int, help="nombre maximum de groupes à traiter")
    parser.add_argument("--rapport", help="chemin du rapport (défaut : <csv>_fusion_rapport.csv)")
    parser.add_argument("--portail", default=PORTAIL_DEFAUT, help="ID du portail HubSpot")
    args = parser.parse_args(argv)

    if args.executer and args.hors_ligne:
        parser.error("--executer et --hors-ligne sont incompatibles")
    client = None
    if not args.hors_ligne:
        jeton = os.environ.get("HUBSPOT_TOKEN")
        if not jeton:
            parser.error("définir HUBSPOT_TOKEN (jeton d'application privée), "
                         "ou utiliser --hors-ligne pour un aperçu")
        client = ClientHubSpot(jeton)

    if args.executer:
        # Le propriétaire actif doit pouvoir être reconnu avant toute fusion.
        try:
            client.proprietaires_actifs(strict=True)
        except ErreurHubSpot as e:
            parser.error("propriétaires HubSpot illisibles ({}) : ajouter le droit "
                         "crm.objects.owners.read au jeton".format(e))

    filtre = {g.strip() for g in args.groupes.split(",")} if args.groupes else None
    rapport = args.rapport or os.path.splitext(args.csv)[0] + "_fusion_rapport.csv"

    if args.executer and not args.oui:
        quoi = "les groupes " + args.groupes if args.groupes else "tous les groupes"
        print("Les fusions HubSpot sont IRRÉVERSIBLES ({}).".format(quoi))
        if input("Taper FUSIONNER pour confirmer : ").strip() != "FUSIONNER":
            print("Annulé.")
            return 1

    mode = "FUSION" if args.executer else "SIMULATION" + (" hors ligne" if args.hors_ligne else "")
    print("Mode : {}".format(mode))
    compteur = traiter(args.csv, rapport, client=client, reel=args.executer, filtre=filtre,
                       limite=args.limite, portail=args.portail)
    print("\nBilan : " + ", ".join("{} {}".format(v, k) for k, v in sorted(compteur.items())))
    print("Rapport : {}".format(rapport))
    if not args.executer:
        print("Rien n'a été modifié. Relancer avec --executer pour fusionner.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
