#!/usr/bin/env python3
"""
Fusion des entreprises HubSpot en doublon certain, à partir de l'onglet « Doublons » du
classeur doublons_potentiels_entreprises_hubspot.xlsx (lignes de niveau « Certain »).

Les fiches d'un même groupe (G-001, G-002...) sont fusionnées en une seule, puis la fiche
obtenue est complétée pour garder le plus d'information possible, la plus à jour :

  Fiche racine   celle qui a une ou plusieurs transactions associées ; sinon (ou si plusieurs
                 en ont) celle qui a le plus de contacts associés ; à égalité, la « Racine
                 suggérée » du classeur, puis la plus complète, puis la plus ancienne.
  Nom            celui de la racine, sauf s'il n'est qu'un nom de domaine ou vide : on prend
                 alors celui de la racine suggérée, sinon le vrai nom le plus récent (cette
                 fiche donne aussi le domaine).
  Propriétaire   toujours un utilisateur actif quand une des fiches en a un (celui de la
                 racine en priorité) ; sinon celui de la racine tel quel (un propriétaire
                 désactivé n'est jamais ajouté).
  Domaine, site  ceux de la racine (ils servent à rattacher les contacts), remplacés seulement
                 s'ils sont vides, factices (« 4313.co »), en punycode (« xn-- ») ou sur une
                 plateforme (e-lyco, wixsite...), ou par le domaine principal du même site
                 (« intranet.apei.fr » -> « apei.fr »).
  Autres champs  (adresse, ville, téléphone, SIREN, SIRET, Type de décideur, secteur,
                 catégorie d'actifs...) : la valeur saisie le plus récemment dans HubSpot
                 (historique de chaque propriété), une fiche vide étant complétée par les
                 autres. Téléphones « 00 00 00 00 00 » ignorés, « Ne sait pas encore »
                 utilisé seulement faute de mieux. Une valeur identique à celle
                 de la racine à la casse ou à la mise en forme près n'est pas réécrite.

Sécurités :
  - par défaut, SIMULATION : rien n'est modifié, le rapport montre ce qui serait fait ;
  - --executer fusionne réellement (irréversible), après confirmation ;
  - un groupe dont les fiches portent des SIREN différents n'est pas fusionné (« À VÉRIFIER ») ;
  - relancer le script est sans risque : les groupes déjà fusionnés sont détectés.

Exemples :
  python fusion_entreprises_hubspot.py doublons_entreprises.xlsx --hors-ligne   # aperçu sans HubSpot
  python fusion_entreprises_hubspot.py doublons_entreprises.xlsx                # simulation
  python fusion_entreprises_hubspot.py doublons_entreprises.xlsx --groupes G-001,G-002 --executer
  python fusion_entreprises_hubspot.py doublons_entreprises.xlsx --executer

Nécessite fusion_doublons_hubspot.py dans le même dossier (connexion HubSpot commune).
Accès HubSpot : variable d'environnement HUBSPOT_TOKEN = jeton d'une application privée avec
les droits crm.objects.companies.read, crm.objects.companies.write et crm.objects.owners.read.
"""

import argparse
import csv
import os
import re
import sys
import time
import zipfile
from xml.etree import ElementTree

from fusion_doublons_hubspot import (PORTAIL_DEFAUT, ClientHubSpot, ErreurHubSpot, chiffres,
                                     date_iso, lire_csv, normaliser, ressemble_domaine,
                                     verifier_jeton)

LIEN_FICHE = "https://app-eu1.hubspot.com/contacts/{portail}/record/0-2/{id}"
FEUILLE = "Doublons"

# Propriétés consolidées si la liste des propriétés HubSpot ne peut pas être lue.
PROPRIETES_DEFAUT = [
    "name", "domain", "website", "phone", "address", "address2", "city", "zip", "state",
    "country", "industry", "description", "about_us", "type", "numberofemployees",
    "annualrevenue", "founded_year", "linkedin_company_page", "facebook_company_page",
    "twitterhandle", "email", "hubspot_owner_id", "hs_lead_status",
    "siren", "siret", "code_naf", "type_de_decideur", "type_de_prospect",
    "categorie_d_actifs_majoritaires", "activite_et_positionnement",
    "nombre_d_hab__collectivites_uniquement_", "derniere_surface_connue",
    "reference_client_202x", "satisfaction_client", "passation", "type_d_ao",
    "email_du_pack_operat", "autres_emails_du_pack_operat", "statut_de_declaration_dt_2022",
    "sites_declares_sur_operat_en_2022_sur_l_ensemble_des_sites", "potentiel_grd__",
    "commentaire_grande_relance_operat", "commentaire_conso_2023", "lien_contrat_acoach",
    "lien_offre_202x_et_acoach__cat_1_", "lien_acoach_post_202x__cat_4_et_5_",
    "nombre_de_compteur_202x_contrat", "objectif_mutualise_2030",
]
# Propriétés HubSpot standard reprises (les propriétés propres au portail le sont toutes).
STANDARD = set(PROPRIETES_DEFAUT[:23])
# Gérées par HubSpot lors de la fusion, ou à ne jamais réécrire.
EXCLUES = {"lifecyclestage", "createdate", "hs_object_id", "hs_merged_object_ids",
           "num_associated_contacts", "num_associated_deals", "hs_parent_company_id"}
LECTURE_SEULE = {"num_associated_contacts", "num_associated_deals", "createdate"}

# Valeurs qui ne disent rien : gardées seulement si aucune fiche n'a mieux.
INCONNUES = {"ne sais pas encore", "ne sait pas encore", "nc", "inconnu", "n/a", "na", "-"}

# Domaines de plateformes : gardés seulement faute de mieux.
PLATEFORMES = ("e-lyco.fr", "wixsite.com", "google.com", "sites.google", "blogspot.",
               "wordpress.com", "jimdo", "free.fr", "orange.fr", "wanadoo.fr", "facebook.com")

ENTETES_RAPPORT = [
    "Groupe", "Statut", "Fiches du groupe", "Transactions par fiche", "Contacts par fiche",
    "Fiche racine", "ID final",
    "Lien HubSpot", "Nom", "Domaine", "Téléphone", "Ville", "SIREN", "SIRET",
    "Type de décideur", "Propriétaire", "Champs complétés ou mis à jour", "Remarques",
]


# --------------------------------------------------------------------------- #
# Lecture du classeur
# --------------------------------------------------------------------------- #

def _colonne(reference):
    """« AB12 » -> 27 (index de colonne à partir de 0)."""
    n = 0
    for c in re.match(r"[A-Z]+", reference).group(0):
        n = n * 26 + ord(c) - 64
    return n - 1


def _nombre(texte):
    """Valeur numérique d'Excel en texte : « 14939896642.0 » ou « 1.49E10 » -> entier."""
    try:
        f = float(texte)
    except ValueError:
        return texte
    return str(int(f)) if f == int(f) else texte


def lire_xlsx(chemin, feuille=FEUILLE):
    """Lignes de la feuille sous forme de dictionnaires (bibliothèque standard seule)."""
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    rel = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    with zipfile.ZipFile(chemin) as z:
        partages = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ElementTree.fromstring(z.read("xl/sharedStrings.xml")).iter(ns + "si"):
                partages.append("".join(t.text or "" for t in si.iter(ns + "t")))
        classeur = ElementTree.fromstring(z.read("xl/workbook.xml"))
        cibles = {r.get("Id"): r.get("Target") for r in
                  ElementTree.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        noms = {s.get("name"): cibles[s.get(rel)] for s in classeur.iter(ns + "sheet")}
        if feuille not in noms:
            raise SystemExit("Onglet « {} » absent du classeur (onglets : {})".format(
                feuille, ", ".join(noms)))
        cible = noms[feuille]
        cible = cible.lstrip("/") if cible.startswith("/") else "xl/" + cible
        racine = ElementTree.fromstring(z.read(cible))
    lignes = []
    for row in racine.iter(ns + "row"):
        valeurs = {}
        for c in row.iter(ns + "c"):
            v, t = c.find(ns + "v"), c.get("t")
            if t == "s":
                valeur = partages[int(v.text)]
            elif t == "inlineStr":
                valeur = "".join(x.text or "" for x in c.iter(ns + "t"))
            elif v is None or v.text is None:
                valeur = ""
            elif t in ("str", "b", "e"):
                valeur = v.text
            else:
                valeur = _nombre(v.text)
            valeurs[_colonne(c.get("r"))] = valeur
        lignes.append([valeurs.get(i, "") for i in range(max(valeurs, default=-1) + 1)])
    if not lignes:
        return []
    entetes = [str(e).strip() for e in lignes[0]]
    return [{e: (l[i] if i < len(l) else "") for i, e in enumerate(entetes)} for l in lignes[1:]]


def lire_liste(chemin, niveau="Certain"):
    """Lignes du niveau voulu, depuis le classeur (onglet Doublons) ou un CSV exporté."""
    if chemin.lower().endswith((".xlsx", ".xlsm")):
        lignes = lire_xlsx(chemin)
    else:
        lignes = lire_csv(chemin)
    if lignes and "ID HubSpot" not in lignes[0]:
        raise SystemExit("Colonne « ID HubSpot » absente de la liste")
    return [l for l in lignes if str(l.get("Niveau", "")).strip().lower() == niveau.lower()]


# --------------------------------------------------------------------------- #
# Nettoyage des valeurs
# --------------------------------------------------------------------------- #

def nettoyer(propriete, valeur):
    """Valeur utile, ou "" si elle est vide ou factice."""
    valeur = str(valeur if valeur is not None else "").strip()
    m = re.fullmatch(r'="(.*)"', valeur)                 # export Excel : ="0123"
    if m:
        valeur = m.group(1).strip()
    if not valeur:
        return ""
    if propriete in ("domain", "website") and re.fullmatch(r"(https?://)?(www\.)?\d+\.co/?",
                                                           valeur.lower()):
        return ""
    if propriete == "phone" and set(re.sub(r"\D", "", valeur)) <= {"0"}:
        return ""
    return valeur


def qualite_domaine(valeur):
    """0 : punycode (adresse abîmée), 1 : plateforme d'hébergement, 2 : vrai domaine."""
    if "xn--" in valeur.lower():
        return 0
    return 1 if any(p in valeur.lower() for p in PLATEFORMES) else 2


def hote(valeur):
    """« https://www.etu.univ-amu.fr/x » -> « etu.univ-amu.fr »."""
    valeur = re.sub(r"^(https?://)?(www\.)?", "", valeur.lower().strip())
    return valeur.split("/")[0]


def meme_site(a, b):
    """Même domaine principal : « univ-amu.fr » et « etu.univ-amu.fr »."""
    return hote(a).split(".")[-2:] == hote(b).split(".")[-2:]


def comparable(propriete, valeur):
    """Forme de comparaison : deux valeurs égales ici ne justifient pas une réécriture."""
    if propriete == "phone":
        return chiffres(valeur)
    if propriete in ("siren", "siret"):
        return re.sub(r"\D", "", valeur)
    if propriete in ("domain", "website"):
        return hote(valeur)
    return normaliser(valeur)


def siren_de(entreprise):
    """SIREN de la fiche (lu dans SIREN, sinon déduit du SIRET), ou ""."""
    siren = re.sub(r"\D", "", entreprise.valeurs.get("siren", ""))
    if len(siren) == 9:
        return siren
    siret = re.sub(r"\D", "", entreprise.valeurs.get("siret", ""))
    return siret[:9] if len(siret) == 14 else ""


# --------------------------------------------------------------------------- #
# Fiches entreprises
# --------------------------------------------------------------------------- #

class Entreprise:
    """Une fiche entreprise : valeurs utiles et date à laquelle chacune a été saisie."""

    def __init__(self, id, valeurs, dates=None, nb_contacts=0, creation="", racine=False,
                 proprietaire_actif=None, nb_transactions=0):
        self.id = str(id)
        self.valeurs = {}
        for p, v in valeurs.items():
            v = nettoyer(p, v)
            if v:
                self.valeurs[p] = v
        self.creation = creation or ""
        # Sans historique (mode hors ligne), chaque valeur est datée de la création.
        self.dates = {p: (dates or {}).get(p) or self.creation for p in self.valeurs}
        self.nb_contacts = int(nb_contacts or 0)
        # None : inconnu (le classeur ne donne pas les transactions).
        self.nb_transactions = None if nb_transactions is None else int(nb_transactions or 0)
        self.racine = racine
        self.proprietaire_actif = proprietaire_actif

    @property
    def nom(self):
        return self.valeurs.get("name", "")

    def __repr__(self):
        return "Entreprise({} {!r}, {} contacts)".format(self.id, self.nom, self.nb_contacts)


def vrai_nom(nom):
    return bool(nom) and not ressemble_domaine(nom.replace("www.", "").replace("https://", ""))


def entreprise_depuis_ligne(ligne):
    """Fiche construite à partir du seul classeur (mode --hors-ligne)."""
    proprietaire = str(ligne.get("Propriétaire") or "").strip()
    actif = None
    if proprietaire:
        actif = "deactivated" not in proprietaire.lower()
    valeurs = {
        "name": ligne.get("Nom de l’entreprise") or ligne.get("Nom de l'entreprise"),
        "city": ligne.get("Ville"), "siren": ligne.get("SIREN"), "siret": ligne.get("SIRET"),
        "phone": ligne.get("Téléphone"), "domain": ligne.get("Nom de domaine"),
        "type_de_decideur": ligne.get("Type de décideur"), "hubspot_owner_id": proprietaire,
    }
    return Entreprise(
        id=str(ligne["ID HubSpot"]).strip(), valeurs=valeurs,
        nb_contacts=str(ligne.get("Contacts associés") or 0).strip() or 0,
        nb_transactions=(str(ligne.get("Transactions associées") or 0).strip() or 0
                         if "Transactions associées" in ligne else None),
        creation=date_iso(str(ligne.get("Date de création") or "")),
        racine=str(ligne.get("Racine suggérée") or "").strip().lower() == "oui",
        proprietaire_actif=actif)


# --------------------------------------------------------------------------- #
# Règles de fusion
# --------------------------------------------------------------------------- #

def choisir_racine(fiches):
    """Une fiche avec transactions ; puis le plus de contacts associés, la racine suggérée,
    la plus complète, la plus ancienne."""
    return max(fiches, key=lambda f: ((f.nb_transactions or 0) > 0, f.nb_contacts, f.racine,
                                      vrai_nom(f.nom), len(f.valeurs),
                                      [-ord(c) for c in f.creation]))


def fiche_identite(fiches, racine):
    """Fiche qui donne le nom et le domaine : la racine si elle a un vrai nom ; sinon la
    racine suggérée, puis la fiche au vrai nom le plus récent (fiche créée depuis un domaine
    d'email mais portant plus de contacts, par exemple)."""
    if vrai_nom(racine.nom):
        return racine
    suggeree = next((f for f in fiches if f.racine and vrai_nom(f.nom)), None)
    if suggeree:
        return suggeree
    reels = sorted((f for f in fiches if vrai_nom(f.nom)), key=lambda f: f.dates["name"],
                   reverse=True)
    return reels[0] if reels else racine


def choisir_proprietaire(fiches, racine):
    """Un propriétaire actif si une fiche en a un (celui de la racine d'abord) ; sinon celui
    de la racine tel quel : un propriétaire désactivé n'est jamais ajouté."""
    ordre = [racine] + sorted((f for f in fiches if f is not racine),
                              key=lambda f: f.dates.get("hubspot_owner_id", ""), reverse=True)
    avec = [f for f in ordre if f.valeurs.get("hubspot_owner_id")]
    actif = next((f for f in avec if f.proprietaire_actif), None)
    if actif:
        return actif.valeurs["hubspot_owner_id"], ""
    if avec and all(f.proprietaire_actif is None for f in avec):
        return avec[0].valeurs["hubspot_owner_id"], "statut des propriétaires inconnu"
    actuel = racine.valeurs.get("hubspot_owner_id", "")
    if actuel:
        return actuel, "aucun propriétaire actif : propriétaire désactivé conservé"
    return "", ""


def choisir_domaine(propriete, fiches, racine):
    """Domaine (ou site) de la fiche qui donne le nom, en général la racine : il sert à
    rattacher les contacts. Remplacé seulement
    s'il est vide, factice, en punycode ou sur une plateforme, ou par le domaine principal
    du même site (« intranet.apei.fr » -> « apei.fr »)."""
    identite = fiche_identite(fiches, racine)
    premieres = [identite] + ([racine] if racine is not identite else [])
    autres = sorted((f for f in fiches if f not in premieres and f.valeurs.get(propriete)),
                    key=lambda f: f.dates[propriete], reverse=True)
    valeurs = [f.valeurs[propriete] for f in premieres + autres if f.valeurs.get(propriete)]
    if not valeurs:
        return ""
    meilleure = max(qualite_domaine(v) for v in valeurs)
    bonnes = [v for v in valeurs if qualite_domaine(v) == meilleure]
    meme = [v for v in bonnes if meme_site(v, bonnes[0])]
    choisie = min(meme, key=lambda v: len(hote(v).split(".")))   # 1re en cas d'égalité
    actuelle = racine.valeurs.get(propriete, "")
    if actuelle and comparable(propriete, actuelle) == comparable(propriete, choisie):
        return actuelle
    return choisie


def choisir_valeur(propriete, fiches, racine):
    """Valeur la plus récente parmi les fiches ; celle de la racine si elle est équivalente."""
    candidates = [f for f in fiches if f.valeurs.get(propriete)]
    if not candidates:
        return ""
    connues = [f for f in candidates if normaliser(f.valeurs[propriete]) not in INCONNUES]
    candidates = connues or candidates           # « Ne sait pas encore » : faute de mieux
    if propriete in ("domain", "website"):
        return choisir_domaine(propriete, fiches, racine)
    choisie = max(candidates, key=lambda f: (f.dates[propriete], f is racine))
    valeur = choisie.valeurs[propriete]
    actuelle = racine.valeurs.get(propriete, "")
    if actuelle and comparable(propriete, actuelle) == comparable(propriete, valeur):
        return actuelle
    return valeur


def planifier(groupe, fiches, proprietes):
    """Valeurs cibles de la fiche fusionnée, ou statut « À VÉRIFIER »."""
    plan = {"groupe": groupe, "fiches": fiches, "remarques": []}
    sirens = {siren_de(f) for f in fiches} - {""}
    if len(sirens) > 1:
        plan["statut"] = "À VÉRIFIER"
        plan["remarques"].append("SIREN différents : " + ", ".join(sorted(sirens)))
        return plan

    racine = choisir_racine(fiches)
    if sum(1 for f in fiches if (f.nb_transactions or 0) > 0) > 1:
        plan["remarques"].append("transactions sur plusieurs fiches : racine = celle qui a le "
                                 "plus de contacts")
    cibles = {}
    for p in proprietes:
        if p in ("name", "hubspot_owner_id"):
            continue
        valeur = choisir_valeur(p, fiches, racine)
        if valeur:
            cibles[p] = valeur
    cibles["name"] = fiche_identite(fiches, racine).nom or racine.nom
    proprietaire, remarque = choisir_proprietaire(fiches, racine)
    if proprietaire:
        cibles["hubspot_owner_id"] = proprietaire
    if remarque:
        plan["remarques"].append(remarque)
    plan.update({
        "statut": "À FUSIONNER",
        "racine": racine,
        "autres": [f for f in fiches if f is not racine],
        "cibles": cibles,
        # Ce que la fusion ajoute ou change par rapport à la racine.
        "changements": {p: (racine.valeurs.get(p, ""), v) for p, v in cibles.items()
                        if v != racine.valeurs.get(p, "")},
    })
    return plan


# --------------------------------------------------------------------------- #
# HubSpot
# --------------------------------------------------------------------------- #

class ClientEntreprises(ClientHubSpot):

    def proprietes_modifiables(self):
        """Propriétés à consolider : standard utiles + toutes celles propres au portail."""
        try:
            rep = self.requete("GET", "/crm/v3/properties/companies?archived=false")
        except ErreurHubSpot as e:
            print("  ! liste des propriétés non lue ({}) : liste par défaut".format(e),
                  file=sys.stderr)
            return list(PROPRIETES_DEFAUT)
        noms = []
        for p in rep.get("results", []):
            meta = p.get("modificationMetadata") or {}
            if (meta.get("readOnlyValue") or p.get("calculated") or p.get("hidden")
                    or str(p.get("fieldType", "")).startswith("calculation")
                    or p["name"] in EXCLUES):
                continue
            if p["name"] in STANDARD or not p.get("hubspotDefined"):
                noms.append(p["name"])
        return noms or list(PROPRIETES_DEFAUT)

    def entreprise(self, id_entreprise, proprietes, racine=False):
        """Fiche lue dans HubSpot (avec la date de chaque valeur), ou None si absente.
        Un ID déjà fusionné renvoie la fiche issue de la fusion (autre ID)."""
        liste = ",".join(proprietes)
        chemin = ("/crm/v3/objects/companies/{}?properties={},{}&propertiesWithHistory={}"
                  .format(id_entreprise, liste, ",".join(LECTURE_SEULE), liste))
        try:
            brut = self.requete("GET", chemin)
        except ErreurHubSpot as e:
            if e.statut == 404:
                return None
            raise
        p = brut.get("properties", {})
        dates = {}
        for nom, historique in (brut.get("propertiesWithHistory") or {}).items():
            if historique:
                dates[nom] = date_iso(historique[0].get("timestamp"))
        actifs = self.proprietaires_actifs()
        proprietaire = p.get("hubspot_owner_id") or ""
        return Entreprise(
            id=brut["id"], valeurs={k: p.get(k) for k in proprietes}, dates=dates,
            nb_contacts=p.get("num_associated_contacts") or 0,
            nb_transactions=p.get("num_associated_deals") or 0,
            creation=date_iso(p.get("createdate") or brut.get("createdAt")), racine=racine,
            proprietaire_actif=(proprietaire in actifs) if actifs else None)

    def fusionner_entreprises(self, id_principal, id_a_fusionner):
        rep = self.requete("POST", "/crm/v3/objects/companies/merge",
                           {"primaryObjectId": str(id_principal),
                            "objectIdToMerge": str(id_a_fusionner)})
        return str(rep.get("id") or id_principal)

    def modifier_entreprise(self, id_entreprise, proprietes):
        """Écrit les propriétés ; renvoie celles que HubSpot a refusées."""
        chemin = "/crm/v3/objects/companies/{}".format(id_entreprise)
        try:
            self.requete("PATCH", chemin, {"properties": proprietes})
            return []
        except ErreurHubSpot as e:
            if e.statut != 400 or len(proprietes) == 1:
                raise
        refusees = []                       # une valeur refusée : on passe champ par champ
        for nom, valeur in proprietes.items():
            try:
                self.requete("PATCH", chemin, {"properties": {nom: valeur}})
            except ErreurHubSpot as e:
                if e.statut != 400:
                    raise
                refusees.append(nom)
        return refusees


def lire_fiche_fusionnee(client, id_entreprise, proprietes, essais=5):
    for essai in range(essais):
        fiche = client.entreprise(id_entreprise, proprietes)
        if fiche is not None:
            return fiche
        time.sleep(2 * (essai + 1))
    raise ErreurHubSpot(404, "fiche fusionnée {} introuvable".format(id_entreprise))


def executer(client, plan, proprietes):
    """Fusionne le groupe dans la racine puis complète la fiche obtenue. Renvoie l'ID final."""
    id_final = plan["racine"].id
    for autre in plan["autres"]:
        id_final = client.fusionner_entreprises(id_final, autre.id)
    plan["statut"] = "FUSIONNÉ"
    try:
        fiche = lire_fiche_fusionnee(client, id_final, proprietes)
        a_ecrire = {p: v for p, v in plan["cibles"].items()
                    if comparable(p, v) != comparable(p, fiche.valeurs.get(p, ""))}
        if a_ecrire:
            refusees = client.modifier_entreprise(id_final, a_ecrire)
            if refusees:
                plan["remarques"].append("valeurs refusées par HubSpot : " + ", ".join(refusees))
    except ErreurHubSpot as e:
        plan["statut"] = "FUSIONNÉ - CORRECTIONS À FAIRE"
        plan["remarques"].append(str(e))
    return id_final


# --------------------------------------------------------------------------- #
# Rapport et programme principal
# --------------------------------------------------------------------------- #

def ligne_rapport(plan, portail, id_final=""):
    fiches = plan["fiches"]
    ligne = {
        "Groupe": plan["groupe"], "Statut": plan["statut"],
        "Fiches du groupe": " ; ".join(f.id for f in fiches),
        "Transactions par fiche": " ; ".join(
            "?" if f.nb_transactions is None else str(f.nb_transactions) for f in fiches),
        "Contacts par fiche": " ; ".join(str(f.nb_contacts) for f in fiches),
        "Remarques": " ; ".join(plan["remarques"]),
    }
    if "racine" in plan:
        c = plan["cibles"]
        ligne.update({
            "Fiche racine": plan["racine"].id, "ID final": id_final,
            "Lien HubSpot": LIEN_FICHE.format(portail=portail, id=id_final or plan["racine"].id),
            "Nom": c.get("name", ""), "Domaine": c.get("domain", ""),
            "Téléphone": c.get("phone", ""), "Ville": c.get("city", ""),
            "SIREN": c.get("siren", ""), "SIRET": c.get("siret", ""),
            "Type de décideur": c.get("type_de_decideur", ""),
            "Propriétaire": c.get("hubspot_owner_id", ""),
            "Champs complétés ou mis à jour": " ; ".join(
                "{} : {} -> {}".format(p, a or "(vide)", n)
                for p, (a, n) in plan["changements"].items()),
        })
    return ligne


def ecrire_rapport(chemin, lignes):
    with open(chemin, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ENTETES_RAPPORT, delimiter=";")
        w.writeheader()
        w.writerows(lignes)


def fiches_du_groupe(lignes, client, proprietes):
    """Fiches du groupe, sans doublon d'ID (un ID déjà fusionné renvoie la fiche finale)."""
    fiches, absentes = [], []
    for ligne in lignes:
        id_hubspot = str(ligne["ID HubSpot"]).strip()
        racine = str(ligne.get("Racine suggérée") or "").strip().lower() == "oui"
        if client is None:
            fiche = entreprise_depuis_ligne(ligne)
        else:
            fiche = client.entreprise(id_hubspot, proprietes, racine=racine)
        if fiche is None:
            absentes.append(id_hubspot)
            continue
        existante = next((f for f in fiches if f.id == fiche.id), None)
        if existante:
            existante.racine = existante.racine or racine
        else:
            fiches.append(fiche)
    return fiches, absentes


def traiter(chemin, chemin_rapport, client=None, reel=False, filtre=None, limite=None,
            portail=PORTAIL_DEFAUT, niveau="Certain", journal=print):
    groupes = {}
    for ligne in lire_liste(chemin, niveau):
        g = str(ligne.get("Groupe") or "").strip()
        if g and (not filtre or g in filtre):
            groupes.setdefault(g, []).append(ligne)
    proprietes = client.proprietes_modifiables() if client else list(PROPRIETES_DEFAUT)
    rapport, compteur = [], {}
    for n, (groupe, lignes) in enumerate(sorted(groupes.items())):
        if limite is not None and n >= limite:
            break
        id_final = ""
        try:
            fiches, absentes = fiches_du_groupe(lignes, client, proprietes)
            if len(fiches) < 2:
                plan = {"groupe": groupe, "fiches": fiches,
                        "statut": "DÉJÀ FUSIONNÉ" if fiches else "INTROUVABLE",
                        "remarques": ["fiches absentes : " + ", ".join(absentes)] if absentes
                        else ["les fiches ne forment déjà plus qu'une"]}
            else:
                plan = planifier(groupe, fiches, proprietes)
                if absentes:
                    plan["remarques"].append("fiches absentes : " + ", ".join(absentes))
            if plan["statut"] == "À FUSIONNER":
                if reel:
                    id_final = executer(client, plan, proprietes)
                else:
                    plan["statut"] = "SIMULATION"
        except ErreurHubSpot as e:
            if e.statut == 403 and reel:
                ecrire_rapport(chemin_rapport, rapport)
                raise SystemExit("HubSpot refuse la fusion (HTTP 403) : ajouter le droit "
                                 "crm.objects.companies.write à l'application privée. "
                                 "Groupes déjà traités : voir {}".format(chemin_rapport))
            plan = {"groupe": groupe, "fiches": [], "statut": "ERREUR", "remarques": [str(e)]}
        ligne = ligne_rapport(plan, portail, id_final)
        rapport.append(ligne)
        compteur[plan["statut"]] = compteur.get(plan["statut"], 0) + 1
        journal("{} {:<30} {}".format(groupe, plan["statut"], ligne.get("Nom", "")).rstrip())
    ecrire_rapport(chemin_rapport, rapport)
    return compteur


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Fusionne les entreprises HubSpot en doublon certain (liste par groupe).")
    parser.add_argument("liste", help="classeur .xlsx (onglet « Doublons ») ou CSV exporté")
    parser.add_argument("--executer", action="store_true",
                        help="fusionner réellement dans HubSpot (irréversible)")
    parser.add_argument("--oui", action="store_true",
                        help="ne pas demander de confirmation avant de fusionner")
    parser.add_argument("--hors-ligne", action="store_true",
                        help="aperçu à partir du seul classeur, sans appeler HubSpot")
    parser.add_argument("--groupes", help="groupes à traiter, ex. G-001,G-002")
    parser.add_argument("--limite", type=int, help="nombre maximum de groupes à traiter")
    parser.add_argument("--rapport",
                        help="chemin du rapport (défaut : <liste>_fusion_rapport.csv)")
    parser.add_argument("--portail", default=PORTAIL_DEFAUT, help="ID du portail HubSpot")
    args = parser.parse_args(argv)

    if args.executer and args.hors_ligne:
        parser.error("--executer et --hors-ligne sont incompatibles")
    if not os.path.isfile(args.liste):
        dossier = os.path.dirname(os.path.abspath(args.liste))
        presents = sorted(f for f in os.listdir(dossier)
                          if f.lower().endswith((".xlsx", ".csv"))
                          and not f.lower().endswith("_rapport.csv"))
        parser.error("fichier introuvable : « {} ». Fichiers présents dans le dossier : {}"
                     .format(args.liste, ", ".join(presents) or "aucun"))
    client = None
    if not args.hors_ligne:
        jeton = os.environ.get("HUBSPOT_TOKEN")
        if not jeton:
            parser.error("définir HUBSPOT_TOKEN (jeton d'application privée), "
                         "ou utiliser --hors-ligne pour un aperçu")
        client = ClientEntreprises(jeton.strip())
        probleme = verifier_jeton(client, jeton)
        if not probleme:
            try:
                client.requete("GET", "/crm/v3/objects/companies?limit=1")
            except ErreurHubSpot as e:
                probleme = ("Le jeton ne peut pas lire les entreprises ({}) : ajouter "
                            "crm.objects.companies.read à l'application privée.".format(e))
        if probleme:
            parser.error(probleme)

    if args.executer:
        try:
            client.proprietaires_actifs(strict=True)
        except ErreurHubSpot as e:
            parser.error("propriétaires HubSpot illisibles ({}) : ajouter le droit "
                         "crm.objects.owners.read à l'application privée".format(e))

    filtre = {g.strip() for g in args.groupes.split(",")} if args.groupes else None
    rapport = args.rapport or os.path.splitext(args.liste)[0] + "_fusion_rapport.csv"

    if args.executer and not args.oui:
        quoi = "les groupes " + args.groupes if args.groupes else "tous les groupes"
        print("Les fusions HubSpot sont IRRÉVERSIBLES ({}).".format(quoi))
        if input("Taper FUSIONNER pour confirmer : ").strip() != "FUSIONNER":
            print("Annulé.")
            return 1

    mode = "FUSION" if args.executer else "SIMULATION" + (" hors ligne" if args.hors_ligne else "")
    print("Mode : {}".format(mode))
    compteur = traiter(args.liste, rapport, client=client, reel=args.executer, filtre=filtre,
                       limite=args.limite, portail=args.portail)
    print("\nBilan : " + ", ".join("{} {}".format(v, k) for k, v in sorted(compteur.items())))
    print("Rapport : {}".format(rapport))
    if not args.executer:
        print("Rien n'a été modifié. Relancer avec --executer pour fusionner.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
