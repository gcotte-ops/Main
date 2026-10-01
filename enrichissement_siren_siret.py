#!/usr/bin/env python3
"""
Enrichissement SIREN / SIRET des entreprises HubSpot via l'Annuaire des Entreprises.

Source : https://annuaire-entreprises.data.gouv.fr/ — le script interroge l'API
publique officielle qui alimente ce site (https://recherche-entreprises.api.gouv.fr),
ce qui renvoie exactement les mêmes résultats, dans le même ordre, que la recherche
sur le site, sans avoir à analyser les pages HTML.

Arbre de décision (lignes dont le SIREN ou le SIRET est vide ; les autres sont ignorées) :
  0. SIRET déjà renseigné : recherche par SIRET, qui désigne l'établissement à coup sûr.
     Adresse identique                             -> TROUVÉ : SIREN écrit.
     Adresse différente                            -> ADRESSE À VÉRIFIER : SIREN écrit,
                                                      adresse HubSpot laissée telle quelle.
  1. Recherche du nom (ou du SIREN s'il est connu) ; résultats examinés dans l'ordre.
     Nom + adresse identiques                      -> TROUVÉ : SIREN + SIRET écrits.
  2. Sinon, recherche « nom + ville du CSV ».
     Nom + adresse identiques                      -> TROUVÉ : SIREN + SIRET écrits.
     Pas d'adresse dans HubSpot, une seule entreprise de ce nom dans la ville
                                                   -> TROUVÉ (VILLE) : SIREN + SIRET écrits
                                                      (adresse vide remplie si 1er résultat).
     1er résultat = même entreprise, en activité, autre adresse
                                                   -> ADRESSE CORRIGÉE : SIREN + SIRET écrits,
                                                      adresse et ville HubSpot remplacées.
  3. Sinon                                         -> RECHERCHE INTERNET (rien n'est écrit).
  L'adresse n'est modifiée que dans le cas ADRESSE CORRIGÉE.
  Entreprise cessée                                -> FERMÉE : fiche à supprimer ou
                                                      entreprise radiée (INPI).
  Entreprise étrangère                             -> HORS FRANCE (non recherchée).
  Optionnel : envoyer le CSV complété par email (par défaut à gcotte@alter-watt.fr).

Aucune dépendance externe : uniquement la bibliothèque standard Python (3.8+).

Exemples :
  python enrichissement_siren_siret.py entreprises.csv
  python enrichissement_siren_siret.py entreprises.csv -o entreprises_completees.csv
  python enrichissement_siren_siret.py entreprises.csv --envoyer
  python enrichissement_siren_siret.py entreprises.csv --col-nom "Company name"

Envoi d'email (--envoyer) : configurer les variables d'environnement
  SMTP_HOST, SMTP_PORT (défaut 587), SMTP_USER, SMTP_PASSWORD, SMTP_FROM (défaut SMTP_USER)
Pour Google Workspace : SMTP_HOST=smtp.gmail.com et un « mot de passe d'application ».
"""

import argparse
import csv
import difflib
import io
import json
import os
import re
import smtplib
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage

API_URL = "https://recherche-entreprises.api.gouv.fr/search"
ANNUAIRE_URL = "https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}"
DESTINATAIRE_DEFAUT = "gcotte@alter-watt.fr"

# L'API autorise 7 requêtes / seconde : on reste largement en dessous.
DELAI_ENTRE_REQUETES = 0.25

PAYS_FRANCE = {"", "france", "fr", "fra", "france metropolitaine", "reunion", "la reunion",
               "guadeloupe", "martinique", "guyane", "mayotte"}

SEUIL_NOM = 0.80
SEUIL_NOM_CORRECTION = 0.90   # nom quasi identique exigé avant de corriger une adresse
SEUIL_VOIE = 0.75

# Noms de colonnes reconnus automatiquement (comparés sans accents ni casse).
ALIAS_COLONNES = {
    "id": ["record id", "id", "id hubspot", "hubspot id", "company id", "id entreprise",
           "id de la fiche", "id fiche",
           "id de fiche d'informations", "id de fiche d informations"],
    "nom": ["nom de l'entreprise", "nom entreprise", "nom", "company name", "name",
            "raison sociale", "entreprise"],
    "secteur": ["secteur d'activite", "secteur", "industry", "activite"],
    "categorie": ["sous-categorie d'actifs majoritaires", "categorie d'actifs majoritaires",
                  "sous-categorie", "categorie", "type d'entreprise", "type"],
    "adresse": ["adresse postale", "adresse", "street address", "address", "adresse 1",
                "rue"],
    "ville": ["ville", "city", "commune"],
    "pays": ["pays/region", "pays", "country", "country/region", "pays region"],
    "code_postal": ["code postal", "postal code", "zip", "cp"],
    "siren": ["siren", "numero siren", "n siren"],
    "siret": ["siret", "numero siret", "n siret"],
}

FORMES_JURIDIQUES = {
    "sa", "sas", "sasu", "sarl", "eurl", "sci", "snc", "scop", "scic", "sca", "scs",
    "selarl", "selas", "gie", "ei", "eirl", "sem", "spl", "cooperative",
    "societe", "ste", "groupe", "group", "france", "holding", "et", "de", "du", "des",
    "la", "le", "les", "l", "d", "and", "the",
}

TYPES_VOIE = {
    "av": "avenue", "ave": "avenue", "bd": "boulevard", "bld": "boulevard",
    "blvd": "boulevard", "boul": "boulevard", "ch": "chemin", "chem": "chemin",
    "crs": "cours", "imp": "impasse", "all": "allee", "pl": "place", "pce": "place",
    "rte": "route", "rt": "route", "sq": "square", "qu": "quai", "qua": "quai",
    "fg": "faubourg", "fbg": "faubourg", "za": "zone", "zi": "zone", "zac": "zone",
    "lot": "lotissement", "res": "residence", "r": "rue", "pass": "passage",
    "prom": "promenade", "sen": "sente", "espl": "esplanade", "hameau": "hameau",
    "che": "chemin", "tsse": "terrasse", "mte": "montee", "ham": "hameau",
    "chs": "chaussee", "prv": "parvis", "vla": "villa", "cite": "cite", "ld": "lieu",
    "st": "saint", "ste": "sainte",
}
MOTS_VIDES_ADRESSE = {"de", "du", "des", "la", "le", "les", "l", "d", "a", "au", "aux", "et",
                      "bis", "ter", "quater", "b", "t", "cedex", "bp", "cs"}


# --------------------------------------------------------------------------- #
# Normalisation
# --------------------------------------------------------------------------- #

def sans_accents(texte):
    texte = unicodedata.normalize("NFKD", texte or "")
    return "".join(c for c in texte if not unicodedata.combining(c))


def normaliser(texte):
    texte = sans_accents(texte).lower()
    texte = re.sub(r"[^a-z0-9]+", " ", texte)
    return re.sub(r"\s+", " ", texte).strip()


def normaliser_nom(nom):
    # Retire les formes juridiques et le contenu entre parenthèses « (SIGLE) ».
    nom = re.sub(r"\(.*?\)", " ", nom or "")
    mots = [m for m in normaliser(nom).split() if m not in FORMES_JURIDIQUES]
    return " ".join(mots)


def normaliser_ville(ville):
    ville = normaliser(ville)
    ville = re.sub(r"\bcedex\b.*$", "", ville)
    ville = re.sub(r"\b\d+\b", "", ville)              # « Paris 8 », « Lyon 3e »...
    ville = re.sub(r"\b(\d+)(e|er|eme)\b", "", ville)
    ville = re.sub(r"\bst\b", "saint", ville)
    ville = re.sub(r"\bste\b", "sainte", ville)
    return re.sub(r"\s+", " ", ville).strip()


def decomposer_adresse(adresse):
    """Renvoie (numéro, mots significatifs de la voie, code postal) d'une adresse."""
    texte = normaliser(adresse)
    code_postal = None
    m = re.search(r"\b(\d{5})\b", texte)
    if m:
        code_postal = m.group(1)
        texte = texte[:m.start()]                       # on ignore la ville qui suit
    numero = None
    m = re.match(r"^(\d+)\s*(bis|ter|quater|[a-d])?\b", texte)
    if m:
        numero = m.group(1)
        texte = texte[m.end():]
    mots = []
    for mot in texte.split():
        mot = TYPES_VOIE.get(mot, mot)
        if mot not in MOTS_VIDES_ADRESSE and not mot.isdigit():
            mots.append(mot)
    return numero, mots, code_postal


def retirer_ville(adresse, ville):
    """« 1 rue des Telliers  Crécy-sur-Serre » -> « 1 rue des Telliers »."""
    if not adresse or not ville:
        return adresse or ""
    mots_ville = normaliser(ville).split()
    mots = normaliser(adresse).split()
    n = len(mots_ville)
    if mots == mots_ville:
        return ""                        # « Paris » saisi comme adresse
    if n and len(mots) > n and mots[-n:] == mots_ville:
        # On retire autant de mots dans le texte d'origine (accents et tirets conservés).
        brut = re.split(r"[\s,;]+", adresse.strip())
        compte, i = 0, len(brut)
        while i > 0 and compte < n:
            i -= 1
            compte += len(normaliser(brut[i]).split())
        return " ".join(brut[:i]).strip(" ,;-")
    return adresse


def similarite(a, b):
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def nettoyer_numero(valeur, longueur):
    chiffres = re.sub(r"\D", "", str(valeur or ""))
    return chiffres if len(chiffres) == longueur else ""


# --------------------------------------------------------------------------- #
# Comparaison nom / adresse
# --------------------------------------------------------------------------- #

# Mots qui décrivent le type d'établissement scolaire ou sa structure de gestion, et non
# l'établissement lui-même : « OGEC École Sainte-Anne » et « Organisme de gestion de
# l'enseignement catholique Sainte Anne » ont en commun « sainte anne ».
GENERIQUES_ECOLE = {
    "ogec", "ogeec", "ogecap", "aogec", "organisme", "organismes", "gestion", "enseignement",
    "catholique", "catholiques", "prive", "privee", "prives", "privees", "ecole", "ecoles",
    "college", "colleges", "lycee", "lycees", "ensemble", "scolaire", "scolaires", "groupe",
    "institution", "institut", "association", "associations", "aep", "apel", "udogec",
    "urogec", "cours", "maternelle", "maternelles", "primaire", "primaires", "elementaire",
    "elementaires", "general", "generale", "technologique", "professionnel", "professionnelle",
    "polyvalent", "agricole", "internat", "externat", "centre", "cfa", "lp", "lgt", "lpo",
    "etablissement", "etablissements", "sous", "contrat", "mixte", "populaire", "familiale",
    "gestionnaire", "comite", "pour", "en", "sur", "a", "au", "aux", "et", "de", "du", "des",
    "la", "le", "les", "l", "d",
}
MOTS_SAINT = {"saint", "sainte", "saints", "saintes"}
RE_ECOLE = re.compile(r"\b(ogec|ogeec|ecole|college|lycee|ensemble scolaire|groupe scolaire|"
                      r"institution|maternelle|enseignement|scolaire|cneap|ddec|udogec|urogec)\b")
RE_PREFIXE = re.compile(r"^\s*(dah|ddec|cneap)\s*[-:/]\s*", re.I)


def est_ecole(nom, categorie=""):
    return bool(RE_ECOLE.search(normaliser(nom))) or normaliser(categorie).startswith("enseignement")


def parties_nom(nom, ville=""):
    """
    Variantes de recherche d'un nom HubSpot, de la plus complète à la plus courte :
    « DAH - OGEC Saint Martin - Collège Immaculée Conception (fermé) »
      -> ["OGEC Saint Martin - Collège Immaculée Conception", "OGEC Saint Martin",
          "Collège Immaculée Conception"]
    Les parties qui ne sont que le nom de la ville sont écartées.
    """
    nom = re.sub(r"\(.*?\)|\[.*?\]", " ", nom or "")
    while RE_PREFIXE.match(nom):
        nom = RE_PREFIXE.sub("", nom, count=1)
    nom = re.sub(r"\s+", " ", nom).strip(" -–/,;")
    if not nom:
        return []
    ville_n = normaliser_ville(ville)
    parties = [p.strip() for p in re.split(r"\s[-–/]\s|\s[-–]|[-–]\s", nom) if p.strip()]
    variantes = [nom]
    for partie in sorted(parties, key=len, reverse=True):
        norm = normaliser(partie)
        if (len(parties) > 1 and norm and norm != ville_n
                and normaliser_ville(partie) != ville_n and partie not in variantes):
            variantes.append(partie)
    return variantes


def distinctifs(texte, ville=""):
    """Mots qui identifient l'établissement (sans les mots génériques ni la ville)."""
    mots_ville = set(normaliser_ville(ville).split())
    mots = []
    for mot in normaliser(re.sub(r"\(.*?\)", " ", texte or "")).split():
        mot = {"st": "saint", "ste": "sainte", "sts": "saints"}.get(mot, mot)
        if mot not in GENERIQUES_ECOLE and mot not in FORMES_JURIDIQUES and mot not in mots_ville:
            mots.append(mot)
    return mots


def noms_resultat(resultat):
    noms = [resultat.get("nom_complet"), resultat.get("nom_raison_sociale"),
            resultat.get("sigle")]
    for etab in [resultat.get("siege") or {}] + (resultat.get("matching_etablissements") or []):
        noms.extend(etab.get("liste_enseignes") or [])
        noms.append(etab.get("nom_commercial"))
    return [n for n in noms if n]


def score_texte(cible, candidat):
    """Similarité de deux noms déjà normalisés (formes juridiques retirées)."""
    if not cible or not candidat:
        return 0.0
    if cible == candidat:
        return 1.0
    score = similarite(cible, candidat)
    # « Alter Watt » vs « Alter Watt Energies » : l'un contient l'autre mot pour mot.
    mots_c, mots_n = set(cible.split()), set(candidat.split())
    petit = mots_c if len(mots_c) <= len(mots_n) else mots_n
    if (mots_c <= mots_n or mots_n <= mots_c) and (len(petit) >= 2 or len(" ".join(petit)) >= 5):
        score = max(score, 0.9)
    return score


def score_distinctif(cible, candidat):
    """Mode école : compare uniquement les mots distinctifs (« sainte anne »)."""
    if not cible or not candidat or set(cible) <= MOTS_SAINT:
        return 0.0
    if set(cible) <= set(candidat) or (set(candidat) <= set(cible)
                                       and not set(candidat) <= MOTS_SAINT
                                       and len(candidat) >= 2):
        return 1.0
    score = similarite(" ".join(cible), " ".join(candidat))
    return 0.9 if score >= 0.85 else score


def score_nom(nom_crm, resultat, ecole=False, ville=""):
    """Meilleure similarité entre le nom HubSpot (et ses parties) et les noms de l'entreprise."""
    parties = parties_nom(nom_crm, ville) or [nom_crm]
    candidats = noms_resultat(resultat)
    meilleur = 0.0
    for partie in parties:
        cible = normaliser_nom(partie)
        cible_d = distinctifs(partie, ville) if ecole else None
        for candidat in candidats:
            meilleur = max(meilleur, score_texte(cible, normaliser_nom(candidat)))
            if ecole:
                meilleur = max(meilleur, score_distinctif(cible_d, distinctifs(candidat, ville)))
            if meilleur >= 1.0:
                return 1.0
    return meilleur


def type_compatible(resultat):
    """Établissement scolaire privé : activité d'enseignement (NAF 85) ou association,
    fondation, congrégation (catégorie juridique 9xxx)."""
    activite = str(resultat.get("activite_principale") or "")
    nature = str(resultat.get("nature_juridique") or "")
    if not activite and not nature:
        return True                      # information absente : on ne bloque pas
    return activite.startswith("85") or nature.startswith("9")


def adresse_etablissement(etab):
    if etab.get("adresse"):
        return etab["adresse"]
    morceaux = [etab.get("numero_voie"), etab.get("indice_repetition"), etab.get("type_voie"),
                etab.get("libelle_voie"), etab.get("code_postal"), etab.get("libelle_commune")]
    return " ".join(str(m) for m in morceaux if m)


def comparer_adresse(adresse_crm, ville_crm, code_postal_crm, etab):
    """
    Renvoie (correspond, détail). L'adresse correspond si la ville est la même et,
    lorsqu'une rue est renseignée dans HubSpot, si le numéro et la voie concordent.
    """
    ville_etab = normaliser_ville(etab.get("libelle_commune") or "")
    cp_etab = etab.get("code_postal") or ""
    num_crm, mots_crm, cp_dans_adresse = decomposer_adresse(retirer_ville(adresse_crm, ville_crm))
    cp_crm = nettoyer_numero(code_postal_crm, 5) or cp_dans_adresse

    ville_ok = None
    if ville_crm:
        v = normaliser_ville(ville_crm)
        ville_ok = bool(v) and (v == ville_etab or similarite(v, ville_etab) >= 0.85
                                or (len(v) > 3 and (v in ville_etab or ville_etab in v)))
    if cp_crm and cp_etab:
        # Un code postal identique suffit à valider la commune (arrondissements, cedex...).
        ville_ok = ville_ok or cp_crm == cp_etab
        if cp_crm[:2] != cp_etab[:2]:
            ville_ok = False
    if ville_ok is False:
        return False, "ville différente ({})".format(etab.get("libelle_commune") or "?")

    if not mots_crm:
        # Pas de rue dans HubSpot : seule la ville peut être vérifiée.
        return bool(ville_ok), "ville seule"

    num_etab, mots_etab, _ = decomposer_adresse(
        " ".join(str(m) for m in [etab.get("numero_voie"), etab.get("type_voie"),
                                  etab.get("libelle_voie")] if m)
        or adresse_etablissement(etab))
    score_voie = similarite(" ".join(mots_crm), " ".join(mots_etab))
    communs = set(mots_crm) & set(mots_etab)
    significatifs = {m for m in mots_crm if m not in set(TYPES_VOIE.values())}
    if significatifs and significatifs <= set(mots_etab):
        score_voie = max(score_voie, 0.9)
    elif communs and len(communs) >= max(1, len(significatifs) - 1):
        score_voie = max(score_voie, 0.8)

    if score_voie < SEUIL_VOIE:
        return False, "voie différente ({})".format(adresse_etablissement(etab))
    if num_crm and num_etab and num_crm != num_etab:
        return False, "numéro différent ({})".format(adresse_etablissement(etab))
    return True, "adresse identique"


# --------------------------------------------------------------------------- #
# Appels à l'API de l'Annuaire des Entreprises
# --------------------------------------------------------------------------- #

class ClientAnnuaire:
    def __init__(self, delai=DELAI_ENTRE_REQUETES, timeout=20):
        self.delai = delai
        self.timeout = timeout
        self._dernier_appel = 0.0

    def rechercher(self, texte, par_page=5, page=1):
        params = {"q": texte, "per_page": par_page, "page": page}
        url = API_URL + "?" + urllib.parse.urlencode(params)
        for tentative in range(5):
            attente = self.delai - (time.time() - self._dernier_appel)
            if attente > 0:
                time.sleep(attente)
            self._dernier_appel = time.time()
            requete = urllib.request.Request(url, headers={
                "Accept": "application/json",
                "User-Agent": "AlterWatt-enrichissement-CRM/1.0",
            })
            try:
                with urllib.request.urlopen(requete, timeout=self.timeout) as reponse:
                    return json.loads(reponse.read().decode("utf-8")).get("results") or []
            except urllib.error.HTTPError as err:
                if err.code == 429 or err.code >= 500:
                    time.sleep(2 ** tentative)
                    continue
                if err.code in (400, 404):
                    return []
                raise
            except (urllib.error.URLError, TimeoutError):
                time.sleep(2 ** tentative)
        raise RuntimeError("L'API de l'Annuaire des Entreprises ne répond pas ({})".format(url))


def etablissements_candidats(resultat):
    """Établissements correspondant à la recherche + siège, actifs d'abord."""
    etabs, vus = [], set()
    for etab in (resultat.get("matching_etablissements") or []) + [resultat.get("siege") or {}]:
        siret = etab.get("siret")
        if siret and siret not in vus:
            vus.add(siret)
            etabs.append(etab)
    etabs.sort(key=lambda e: (e.get("etat_administratif") == "F", not e.get("est_siege")))
    return etabs


def entreprise_fermee(resultat):
    return resultat.get("etat_administratif") == "C"


def reponse(statut, resultat, etab, rang, detail, recherche):
    return {"siren": resultat.get("siren"), "siret": etab.get("siret"), "statut": statut,
            "detail": detail, "rang": rang, "recherche": recherche,
            "nom_trouve": resultat.get("nom_complet") or "",
            "adresse_trouvee": adresse_etablissement(etab), "etablissement": etab}


def etablissement_le_plus_proche(etabs, nom_crm, ville):
    """Parmi les établissements d'une même ville, celui dont l'enseigne ressemble le plus
    au nom HubSpot (une association gère souvent école + collège dans la même commune)."""
    if len(etabs) == 1:
        return etabs[0], False
    cible = distinctifs(nom_crm, ville)

    def score(e):
        noms = (e.get("liste_enseignes") or []) + [e.get("nom_commercial") or ""]
        return max([score_distinctif(cible, distinctifs(n, ville)) for n in noms if n] or [0.0])

    classes = sorted(etabs, key=lambda e: (-score(e), not e.get("est_siege")))
    ambigu = score(classes[0]) < 1.0
    return classes[0], ambigu


def examiner(resultats, ligne, max_resultats, siren_connu=None, seuil_nom=SEUIL_NOM):
    """
    Parcourt les résultats dans l'ordre (1er, 2e, ...) et renvoie un dict :
      - adresse : (rang, résultat, établissement, détail) du premier résultat dont le nom ET
        l'adresse correspondent (actifs d'abord) ;
      - ville : [(rang, résultat, établissement, ambigu)] des résultats dont le nom correspond
        et qui ont un établissement actif dans la ville du CSV (fiches sans adresse) ;
      - homonymes : [(rang, résultat, score_nom)] des résultats dont seul le nom correspond ;
      - rejets : explications pour le rapport.
    """
    ex = {"adresse": None, "ville": [], "homonymes": [], "rejets": []}
    adresse_fermee = None
    ecole = ligne.get("ecole", False)
    for rang, resultat in enumerate(resultats[:max_resultats], start=1):
        nom_trouve = resultat.get("nom_complet") or ""
        if siren_connu:
            if resultat.get("siren") != siren_connu:
                continue
            s_nom = 1.0
        else:
            s_nom = score_nom(ligne["nom"], resultat, ecole, ligne["ville"])
            if s_nom < seuil_nom:
                ex["rejets"].append("#{} {} : nom différent".format(rang, nom_trouve))
                continue
            if ecole and not type_compatible(resultat):
                ex["rejets"].append("#{} {} : pas un établissement d'enseignement / association"
                                    .format(rang, nom_trouve))
                continue
        dans_la_ville, trouve = [], False
        for etab in etablissements_candidats(resultat):
            ok, detail = comparer_adresse(ligne["adresse"], ligne["ville"],
                                          ligne["code_postal"], etab)
            if not ok:
                continue
            trouve = True
            if detail == "ville seule":
                if etab.get("etat_administratif") != "F":
                    dans_la_ville.append(etab)
                continue
            actif = etab.get("etat_administratif") != "F" and not entreprise_fermee(resultat)
            if actif and ex["adresse"] is None:
                ex["adresse"] = (rang, resultat, etab, detail)
            elif not actif and adresse_fermee is None:
                adresse_fermee = (rang, resultat, etab, detail)
            break
        if dans_la_ville:
            etab, ambigu = etablissement_le_plus_proche(dans_la_ville, ligne["nom"], ligne["ville"])
            ex["ville"].append((rang, resultat, etab, ambigu))
        if not trouve:
            ex["homonymes"].append((rang, resultat, s_nom))
            ex["rejets"].append("#{} {} : {} différente ({})".format(
                rang, nom_trouve, "adresse" if ligne["adresse"] else "ville",
                adresse_etablissement(resultat.get("siege") or {})))
    ex["adresse"] = ex["adresse"] or adresse_fermee
    return ex


MESSAGE_FERMEE = "entreprise cessée : fiche à supprimer ou entreprise radiée (INPI)"


def trouver_par_siret(client, ligne, siret, max_resultats=5):
    """
    SIRET déjà renseigné : recherche par SIRET, ce qui désigne l'établissement à coup sûr,
    puis comparaison de son adresse avec celle du CSV. L'adresse n'est jamais modifiée.
    """
    siren = siret[:9]
    for requete in (siret, siren):
        for rang, resultat in enumerate(client.rechercher(requete, par_page=max_resultats), 1):
            if resultat.get("siren") != siren:
                continue
            etab = next((e for e in etablissements_candidats(resultat)
                         if e.get("siret") == siret), None)
            if etab is None:
                continue
            if entreprise_fermee(resultat):
                return reponse("FERMÉE", resultat, etab, rang, MESSAGE_FERMEE, requete)
            ok, detail = comparer_adresse(ligne["adresse"], ligne["ville"],
                                          ligne["code_postal"], etab)
            if ok and detail != "ville seule":
                return reponse("TROUVÉ", resultat, etab, rang,
                               "adresse vérifiée par le SIRET", requete)
            detail = "adresse HubSpot différente de celle du SIRET dans l'Annuaire"
            if not ligne["adresse"]:
                detail = "pas d'adresse dans HubSpot : adresse de l'Annuaire à reporter"
            if etab.get("etat_administratif") == "F":
                detail += " ; cet établissement est fermé"
            return reponse("ADRESSE À VÉRIFIER", resultat, etab, rang, detail, requete)
    return {"statut": "À VÉRIFIER", "detail": "SIRET introuvable dans l'Annuaire des Entreprises"}


def trouver_entreprise(client, ligne, max_resultats=5):
    """
    Arbre de décision :
      0. SIRET déjà renseigné -> recherche par SIRET (voir trouver_par_siret).
      1. Recherche du nom (ou du SIREN s'il est connu), résultats examinés dans l'ordre :
         nom + adresse identiques                                 -> TROUVÉ
      2. Sinon, recherche « nom + ville du CSV » (puis chaque partie du nom) :
         nom + adresse identiques                                 -> TROUVÉ
         pas d'adresse dans HubSpot : une seule entreprise du nom
         avec un établissement actif dans la ville                -> TROUVÉ (VILLE)
         1er résultat = même entreprise, active, autre adresse    -> ADRESSE CORRIGÉE
      3. Sinon                                                    -> RECHERCHE INTERNET
    L'adresse HubSpot n'est écrite que pour une entreprise trouvée en 1er résultat avec
    « nom + ville » (ADRESSE CORRIGÉE, ou TROUVÉ (VILLE) quand l'adresse était vide).
    Une entreprise cessée donne FERMÉE (fiche à supprimer / entreprise radiée INPI).
    """
    nom = ligne["nom"]
    siret_connu = ligne.get("siret")
    if siret_connu:
        return trouver_par_siret(client, ligne, siret_connu, max_resultats)
    siren_connu = ligne["siren"]
    if not (nom or siren_connu):
        return {"statut": "RECHERCHE INTERNET", "detail": "nom de l'entreprise vide"}
    ecole = ligne.get("ecole", False)
    # Les noms d'écoles ont beaucoup d'homonymes : on regarde plus de résultats.
    par_page = max(max_resultats, 10) if ecole else max_resultats
    variantes = parties_nom(nom, ligne["ville"]) or ([nom] if nom else [])
    rejets = []

    def conclure(correspondance, recherche):
        """Nom + adresse trouvés. None si l'établissement est fermé mais l'entreprise active."""
        rang, resultat, etab, detail = correspondance
        if entreprise_fermee(resultat):
            return reponse("FERMÉE", resultat, etab, rang, MESSAGE_FERMEE, recherche)
        if etab.get("etat_administratif") == "F":
            return None
        return reponse("TROUVÉ", resultat, etab, rang, detail, recherche)

    def conclure_ville(ex, recherche, nom_ville=False):
        """Fiche sans adresse : une seule entreprise du nom présente dans la ville."""
        actives = {}
        for rang, resultat, etab, ambigu in ex["ville"]:
            actives.setdefault(resultat.get("siren"), (rang, resultat, etab, ambigu))
        if len(actives) > 1:
            rejets.append("« {} » : {} entreprises du même nom dans cette ville".format(
                recherche, len(actives)))
            return "ambigu"
        if not actives:
            return None
        rang, resultat, etab, ambigu = next(iter(actives.values()))
        if entreprise_fermee(resultat):
            return reponse("FERMÉE", resultat, etab, rang, MESSAGE_FERMEE, recherche)
        detail = "pas d'adresse dans HubSpot : nom et ville vérifiés"
        if ligne.get("adresse_generique"):
            detail = "adresse HubSpot générique ignorée : nom et ville vérifiés"
        if ambigu:
            detail += " ; plusieurs établissements dans la ville, à contrôler"
        res = reponse("TROUVÉ (VILLE)", resultat, etab, rang, detail, recherche)
        res["remplir_adresse"] = nom_ville and rang == 1
        return res

    # 1. Recherche du nom seul (ou du SIREN).
    requete_1 = siren_connu or variantes[0]
    if siren_connu or ligne["adresse"]:
        resultats = client.rechercher(requete_1, par_page=par_page)
        ex = examiner(resultats, ligne, par_page, siren_connu)
        rejets += ex["rejets"]
        if ex["adresse"]:
            res = conclure(ex["adresse"], requete_1)
            if res:
                return res
        if siren_connu:
            unite = next((r for r in resultats if r.get("siren") == siren_connu), None)
            if unite and entreprise_fermee(unite):
                return reponse("FERMÉE", unite, unite.get("siege") or {}, 1, MESSAGE_FERMEE,
                               requete_1)
            res = conclure_ville(ex, requete_1) if not ligne["adresse"] else None
            if isinstance(res, dict):
                return res
            siege = (unite or {}).get("siege") or {}
            if (unite and unite.get("nombre_etablissements_ouverts") == 1
                    and siege.get("etat_administratif") != "F" and siege.get("siret")):
                return reponse("TROUVÉ", unite, siege, 1,
                               "SIREN connu, un seul établissement ouvert", requete_1)

    # 2. Recherche « nom + ville du CSV », puis avec chaque partie du nom.
    if ligne["ville"]:
        for variante in variantes:
            requete_2 = "{} {}".format(variante, ligne["ville"])
            resultats_2 = client.rechercher(requete_2, par_page=par_page)
            ex = examiner(resultats_2, ligne, par_page, siren_connu)
            rejets += ex["rejets"]
            if ex["adresse"]:
                res = conclure(ex["adresse"], requete_2)
                if res:
                    return res
            if not ligne["adresse"]:
                res = conclure_ville(ex, requete_2, nom_ville=True)
                if res == "ambigu":
                    break
                if res:
                    return res
            elif resultats_2:
                # Trouvée du premier coup (1er résultat) mais à une autre adresse : on corrige.
                premier = resultats_2[0]
                meme = (premier.get("siren") == siren_connu if siren_connu
                        else score_nom(nom, premier, ecole, ligne["ville"]) >= SEUIL_NOM_CORRECTION
                        and (not ecole or type_compatible(premier)))
                if meme:
                    if entreprise_fermee(premier):
                        return reponse("FERMÉE", premier, premier.get("siege") or {}, 1,
                                       MESSAGE_FERMEE, requete_2)
                    ville = normaliser_ville(ligne["ville"])
                    actifs = [e for e in etablissements_candidats(premier)
                              if e.get("etat_administratif") != "F"]
                    dans_la_ville = [e for e in actifs
                                     if normaliser_ville(e.get("libelle_commune")) == ville]
                    etab = (dans_la_ville or [premier.get("siege") or {}])[0]
                    if etab.get("siret"):
                        detail = ("trouvée en 1er résultat avec « nom + ville », "
                                  "adresse HubSpot différente")
                        if ligne.get("adresse_generique"):
                            detail = ("trouvée en 1er résultat avec « nom + ville », "
                                      "adresse HubSpot générique remplacée")
                        if not dans_la_ville:
                            detail += " ; aucun établissement actif dans cette ville : siège retenu"
                        return reponse("ADRESSE CORRIGÉE", premier, etab, 1, detail, requete_2)
            if ex["ville"] or ex["homonymes"]:
                break                       # le nom a été trouvé : inutile d'essayer plus court

    # 3. Rien de sûr dans l'Annuaire.
    if not ligne["ville"] and not ligne["adresse"] and not rejets:
        rejets.append("ni adresse ni ville dans HubSpot : impossible de vérifier")
    return {"statut": "RECHERCHE INTERNET",
            "detail": " | ".join(dict.fromkeys(rejets)) or
                      "aucun résultat dans l'Annuaire des Entreprises"}


# --------------------------------------------------------------------------- #
# Lecture / écriture CSV
# --------------------------------------------------------------------------- #

def lire_csv(chemin):
    with open(chemin, "rb") as f:
        brut = f.read()
    for encodage in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            texte = brut.decode(encodage)
            break
        except UnicodeDecodeError:
            continue
    echantillon = texte[:5000]
    try:
        dialecte = csv.Sniffer().sniff(echantillon, delimiters=",;\t|")
        separateur = dialecte.delimiter
    except csv.Error:
        separateur = ";" if echantillon.count(";") > echantillon.count(",") else ","
    lignes = list(csv.reader(io.StringIO(texte, newline=""), delimiter=separateur))
    if not lignes:
        raise SystemExit("Le fichier CSV est vide.")
    return lignes[0], lignes[1:], separateur, encodage


def detecter_colonnes(entetes, forcees):
    normalisees = [normaliser(e) for e in entetes]
    colonnes = {}
    for cle, alias in ALIAS_COLONNES.items():
        if forcees.get(cle):
            cible = normaliser(forcees[cle])
            if cible not in normalisees:
                raise SystemExit("Colonne « {} » introuvable. Colonnes disponibles : {}".format(
                    forcees[cle], ", ".join(entetes)))
            colonnes[cle] = normalisees.index(cible)
            continue
        for a in alias:
            a = normaliser(a)
            if a in normalisees:
                colonnes[cle] = normalisees.index(a)
                break
    for obligatoire in ("nom", "siren", "siret"):
        if obligatoire not in colonnes:
            raise SystemExit(
                "Impossible de trouver la colonne « {} ». Utilisez l'option --col-{}. "
                "Colonnes disponibles : {}".format(obligatoire, obligatoire.replace("_", "-"),
                                                   ", ".join(entetes)))
    return colonnes


def valeur(ligne, colonnes, cle):
    index = colonnes.get(cle)
    if index is None or index >= len(ligne):
        return ""
    return ligne[index].strip()


def ecrire_csv(chemin, entetes, lignes, separateur, encodage="utf-8-sig"):
    with open(chemin, "w", newline="", encoding=encodage) as f:
        writer = csv.writer(f, delimiter=separateur, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(entetes)
        writer.writerows(lignes)


# --------------------------------------------------------------------------- #
# Email
# --------------------------------------------------------------------------- #

def envoyer_email(destinataire, fichiers, resume):
    hote = os.environ.get("SMTP_HOST")
    utilisateur = os.environ.get("SMTP_USER")
    mot_de_passe = os.environ.get("SMTP_PASSWORD")
    if not (hote and utilisateur and mot_de_passe):
        raise SystemExit("Envoi impossible : définir SMTP_HOST, SMTP_USER et SMTP_PASSWORD.")
    port = int(os.environ.get("SMTP_PORT", "587"))
    expediteur = os.environ.get("SMTP_FROM", utilisateur)

    message = EmailMessage()
    message["Subject"] = "CSV entreprises HubSpot complété (SIREN / SIRET)"
    message["From"] = expediteur
    message["To"] = destinataire
    message.set_content(
        "Bonjour,\n\nVous trouverez ci-joint le fichier CSV des entreprises HubSpot "
        "complété avec les SIREN et SIRET issus de l'Annuaire des Entreprises "
        "(annuaire-entreprises.data.gouv.fr), ainsi que le rapport détaillé ligne par "
        "ligne.\n\n{}\n\nLa colonne « Action à mener » du rapport "
        "indique les fiches à supprimer (FERMÉE), à contrôler (À VÉRIFIER) ou à chercher "
        "sur Internet (RECHERCHE INTERNET).\n\nBonne journée".format(resume))
    for chemin in fichiers:
        with open(chemin, "rb") as f:
            message.add_attachment(f.read(), maintype="text", subtype="csv",
                                   filename=os.path.basename(chemin))
    if port == 465:
        with smtplib.SMTP_SSL(hote, port) as serveur:
            serveur.login(utilisateur, mot_de_passe)
            serveur.send_message(message)
    else:
        with smtplib.SMTP(hote, port) as serveur:
            serveur.starttls()
            serveur.login(utilisateur, mot_de_passe)
            serveur.send_message(message)


# --------------------------------------------------------------------------- #
# Programme principal
# --------------------------------------------------------------------------- #

def adresses_generiques(lignes, colonnes, seuil=3):
    """Adresses saisies sur au moins `seuil` fiches de villes différentes (siège d'un réseau,
    adresse remplie automatiquement par HubSpot...) : elles ne décrivent pas l'entreprise."""
    if "adresse" not in colonnes:
        return set()
    fiches, villes = {}, {}
    for ligne in lignes:
        adresse = normaliser(valeur(ligne, colonnes, "adresse"))
        if adresse:
            fiches[adresse] = fiches.get(adresse, 0) + 1
            villes.setdefault(adresse, set()).add(normaliser_ville(valeur(ligne, colonnes, "ville")))
    return {a for a, n in fiches.items() if n >= seuil and len(villes[a]) >= 2}


MOTS_MINUSCULES = {"de", "du", "des", "la", "le", "les", "d", "l", "et", "a", "au", "aux",
                   "sur", "sous", "en"}


def mettre_en_forme(texte):
    """« 1 RUE DES TELLIERS » -> « 1 Rue des Telliers » (style des fiches HubSpot)."""
    def mot(m, premier):
        if "'" in m:
            debut, _, fin = m.partition("'")
            return mot(debut, premier) + "'" + mot(fin, False)
        if "-" in m:
            return "-".join(mot(x, premier and i == 0) for i, x in enumerate(m.split("-")))
        bas = m.lower()
        return bas if (bas in MOTS_MINUSCULES and not premier) else bas.capitalize()
    return " ".join(mot(m, i == 0) for i, m in enumerate((texte or "").split()))


def rue_etablissement(etab):
    """Numéro + voie de l'établissement, sans code postal ni commune."""
    adresse = etab.get("adresse") or ""
    cp = etab.get("code_postal")
    if adresse and cp and cp in adresse:
        rue = adresse[:adresse.index(cp)].strip(" ,")
    else:
        rue = " ".join(str(m) for m in [etab.get("complement_adresse"), etab.get("numero_voie"),
                                        etab.get("indice_repetition"), etab.get("type_voie"),
                                        etab.get("libelle_voie")] if m)
    # Type de voie abrégé par l'INSEE (« AV », « BD », « CHE »...) : on l'écrit en entier.
    mots = rue.split()
    for i, mot in enumerate(mots):
        cle = normaliser(mot)
        if cle.isdigit() or cle in ("bis", "ter", "quater", "b", "t"):
            continue
        if cle in TYPES_VOIE and cle not in ("st", "ste"):
            mots[i] = TYPES_VOIE[cle].upper()
        break
    return " ".join(mots)


STATUTS_ECRITS = {"TROUVÉ", "TROUVÉ (VILLE)", "ADRESSE CORRIGÉE", "ADRESSE À VÉRIFIER",
                  "FERMÉE"}
ACTIONS = {
    "TROUVÉ": "SIREN/SIRET ajoutés",
    "TROUVÉ (VILLE)": "SIREN/SIRET ajoutés (vérifiés sur le nom et la ville)",
    "ADRESSE CORRIGÉE": "SIREN/SIRET ajoutés + adresse corrigée",
    "ADRESSE À VÉRIFIER": "SIREN ajouté ; comparer l'adresse HubSpot à celle de l'Annuaire",
    "FERMÉE": "Supprimer la fiche (entreprise cessée / radiée INPI)",
    "INCOHÉRENT": "Corriger : le SIRET ne commence pas par le SIREN",
    "À VÉRIFIER": "Contrôler manuellement",
    "RECHERCHE INTERNET": "Chercher sur Internet",
    "HORS FRANCE": "Aucune (entreprise étrangère)",
}


def traiter(chemin_entree, chemin_sortie, chemin_rapport, forcees, max_resultats,
            remplir_a_verifier, client=None, corriger_adresse=True):
    entetes, lignes, separateur, _ = lire_csv(chemin_entree)
    colonnes = detecter_colonnes(entetes, forcees)
    client = client or ClientAnnuaire()

    rapport = []
    compteurs = {"TROUVÉ": 0, "TROUVÉ (VILLE)": 0, "ADRESSE CORRIGÉE": 0, "ADRESSE À VÉRIFIER": 0, "FERMÉE": 0,
                 "À VÉRIFIER": 0, "RECHERCHE INTERNET": 0, "HORS FRANCE": 0,
                 "DÉJÀ RENSEIGNÉ": 0, "INCOHÉRENT": 0}
    total = len(lignes)
    generiques = adresses_generiques(lignes, colonnes)

    for numero, ligne in enumerate(lignes, start=1):
        if not any(c.strip() for c in ligne):
            continue
        while len(ligne) < len(entetes):
            ligne.append("")
        donnees = {cle: valeur(ligne, colonnes, cle) for cle in ALIAS_COLONNES}
        siren = nettoyer_numero(donnees["siren"], 9)
        siret = nettoyer_numero(donnees["siret"], 14)
        donnees["siren"], donnees["siret"] = siren, siret
        donnees["ecole"] = est_ecole(donnees["nom"], donnees["categorie"]) or \
            normaliser(donnees["secteur"]).startswith("enseignement")
        donnees["adresse_generique"] = normaliser(donnees["adresse"]) in generiques
        if donnees["adresse_generique"]:
            # Adresse partagée par des fiches de villes différentes : elle est fausse.
            donnees["adresse"] = ""

        if siren and siret and siret[:9] == siren:
            compteurs["DÉJÀ RENSEIGNÉ"] += 1
            continue
        if siren and siret:
            res = {"statut": "INCOHÉRENT",
                   "detail": "SIREN {} / SIRET {} : non modifiés".format(siren, siret)}
        elif normaliser(donnees["pays"]) not in PAYS_FRANCE:
            # L'Annuaire des Entreprises ne recense que les entreprises françaises.
            res = {"statut": "HORS FRANCE", "detail": "pays : " + donnees["pays"]}
        else:
            try:
                res = trouver_entreprise(client, donnees, max_resultats=max_resultats)
            except RuntimeError as err:
                res = {"statut": "RECHERCHE INTERNET", "detail": str(err)}

        statut = res["statut"]
        compteurs[statut] += 1
        ecrit = bool(res.get("siren")) and (
            statut in STATUTS_ECRITS or (statut == "À VÉRIFIER" and remplir_a_verifier))
        nouvelle_adresse = ""
        if ecrit:
            if not nettoyer_numero(ligne[colonnes["siren"]], 9):
                ligne[colonnes["siren"]] = res["siren"]
            if not siret:
                ligne[colonnes["siret"]] = res["siret"]
        corrige = statut == "ADRESSE CORRIGÉE" or res.get("remplir_adresse")
        if ecrit and corrige and corriger_adresse:
            etab = res["etablissement"]
            nouvelle_adresse = mettre_en_forme(rue_etablissement(etab))
            if "adresse" in colonnes and nouvelle_adresse:
                ligne[colonnes["adresse"]] = nouvelle_adresse
            if ("ville" in colonnes and etab.get("libelle_commune")
                    and (statut == "ADRESSE CORRIGÉE" or not donnees["ville"])):
                ligne[colonnes["ville"]] = mettre_en_forme(etab["libelle_commune"])
            if "code_postal" in colonnes and etab.get("code_postal"):
                ligne[colonnes["code_postal"]] = etab["code_postal"]

        rapport.append([
            valeur(ligne, colonnes, "id"), donnees["nom"], donnees["adresse"], donnees["ville"],
            statut, ACTIONS.get(statut, ""), res.get("siren", ""), res.get("siret", ""),
            res.get("nom_trouve", ""), res.get("adresse_trouvee", ""), nouvelle_adresse,
            res.get("rang", ""), res.get("recherche", ""), res.get("detail", ""),
            "oui" if ecrit else "non",
            ANNUAIRE_URL.format(siren=res["siren"]) if res.get("siren") else "",
        ])
        print("[{}/{}] {:<40.40} {:<18} {} {}".format(
            numero, total, donnees["nom"], statut, res.get("siren", "") or "",
            res.get("siret", "") or ""), flush=True)

    ecrire_csv(chemin_sortie, entetes, lignes, separateur)
    ecrire_csv(chemin_rapport, [
        "ID HubSpot", "Nom HubSpot", "Adresse HubSpot", "Ville HubSpot", "Statut",
        "Action à mener", "SIREN trouvé", "SIRET trouvé", "Nom Annuaire", "Adresse Annuaire",
        "Nouvelle adresse écrite", "Rang du résultat", "Recherche effectuée", "Détail",
        "Écrit dans le CSV", "Lien Annuaire",
    ], rapport, separateur)
    return compteurs


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Complète les SIREN / SIRET d'un export d'entreprises HubSpot à partir "
                    "de l'Annuaire des Entreprises (annuaire-entreprises.data.gouv.fr).")
    parser.add_argument("csv", help="CSV d'entrée (export HubSpot)")
    parser.add_argument("-o", "--sortie", help="CSV de sortie (défaut : <entrée>_complete.csv)")
    parser.add_argument("--rapport", help="Rapport détaillé (défaut : <entrée>_rapport.csv)")
    parser.add_argument("--max-resultats", type=int, default=5,
                        help="Nombre de résultats de recherche examinés par entreprise (défaut 5)")
    parser.add_argument("--remplir-a-verifier", action="store_true",
                        help="Écrire aussi les correspondances « À VÉRIFIER » (ville seule, "
                             "nom proche) dans le CSV")
    parser.add_argument("--sans-correction-adresse", action="store_true",
                        help="Ne pas remplacer l'adresse HubSpot quand elle diffère de "
                             "l'Annuaire (SIREN/SIRET du siège écrits quand même)")
    parser.add_argument("--envoyer", action="store_true",
                        help="Envoyer le CSV complété et le rapport par email")
    parser.add_argument("--destinataire", default=DESTINATAIRE_DEFAUT,
                        help="Destinataire de l'email (défaut : %(default)s)")
    for cle in ALIAS_COLONNES:
        parser.add_argument("--col-" + cle.replace("_", "-"), dest="col_" + cle,
                            help="Nom exact de la colonne « {} » si non détectée".format(cle))
    args = parser.parse_args(argv)

    base, _ = os.path.splitext(args.csv)
    sortie = args.sortie or base + "_complete.csv"
    rapport = args.rapport or base + "_rapport.csv"
    forcees = {cle: getattr(args, "col_" + cle) for cle in ALIAS_COLONNES}

    compteurs = traiter(args.csv, sortie, rapport, forcees, args.max_resultats,
                        args.remplir_a_verifier,
                        corriger_adresse=not args.sans_correction_adresse)
    resume = ("Résultat : {TROUVÉ} trouvée(s) à la bonne adresse, {TROUVÉ (VILLE)} trouvée(s) "
              "sur le nom et la ville, {ADRESSE CORRIGÉE} avec "
              "adresse corrigée, {ADRESSE À VÉRIFIER} adresse(s) à vérifier (SIRET connu), "
              "{FERMÉE} fermée(s) (fiches à supprimer), {À VÉRIFIER} à vérifier, "
              "{RECHERCHE INTERNET} à chercher sur Internet, {HORS FRANCE} hors France, "
              "{INCOHÉRENT} SIREN/SIRET incohérent(s), {DÉJÀ RENSEIGNÉ} déjà renseignée(s)."
              ).format(**compteurs)
    print("\n" + resume)
    print("CSV complété : " + sortie)
    print("Rapport      : " + rapport)

    if args.envoyer:
        envoyer_email(args.destinataire, [sortie, rapport], resume)
        print("Email envoyé à " + args.destinataire)
    return 0


if __name__ == "__main__":
    sys.exit(main())
