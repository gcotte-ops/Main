#!/usr/bin/env python3
"""
Enrichissement SIREN / SIRET des entreprises HubSpot via l'Annuaire des Entreprises.

Source : https://annuaire-entreprises.data.gouv.fr/ — le script interroge l'API
publique officielle qui alimente ce site (https://recherche-entreprises.api.gouv.fr),
ce qui renvoie exactement les mêmes résultats, dans le même ordre, que la recherche
sur le site, sans avoir à analyser les pages HTML.

Arbre de décision (lignes dont le SIREN ou le SIRET est vide ; les autres sont ignorées) :
  0. SIRET déjà renseigné (clé de contrôle valide) : recherche par SIRET.
     Adresse identique -> TROUVÉ ; adresse différente -> ADRESSE À VÉRIFIER ; cessée -> FERMÉE.
  1. Recherche du NOM SEUL : la ville n'est jamais ajoutée à la requête, elle sert à trier les
     résultats. 25 résultats, 100 établissements par entreprise ; noms trop différents écartés.
  2. Tri par lieu des entreprises du nom (si aucune n'est à cet endroit, 2e requête filtrée sur
     le ou les départements de la ville, obtenus par géocodage) :
     une seule entreprise à l'adresse                  -> TROUVÉ                « Trouvé »
     une seule dans la ville (pas d'adresse HubSpot)   -> TROUVÉ (VILLE)        « À vérifier »
     une seule dans la ville, à une autre adresse      -> ADRESSE CORRIGÉE      « À vérifier »
     plusieurs au même endroit (filiales, SCI, CSE...) -> départage selon le « Type de décideur »
        Centralisé   : SIREN du groupe (nom identique, puis holding / « groupe », NAF 64.20Z
                       ou 70.10Z, puis taille) ;
        Décentralisé : SIREN de l'entité locale (nom identique, puis pas une holding, puis
                       taille) ; vide ou « Ne sais pas encore » : --defaut-decideur (local).
        SIREN proposé dans le rapport, NON écrit (« À ARBITRER ») ; --ecrire-incertains.
     aucune à cet endroit, une seule entreprise du nom -> son siège, NON écrit (« À ARBITRER »).
  3. Ni adresse ni ville : une seule structure porte ce nom -> TROUVÉ (NOM UNIQUE) « À vérifier »
     (« Trouvé » avec --nom-unique-trouve).
  4. Sinon -> RECHERCHE INTERNET (rien n'est écrit).
  Société cessée trouvée par le nom : souvent une ancienne filiale d'une entreprise active ;
  SIREN NON écrit (« À ARBITRER »), jamais de suppression de fiche sans contrôle.
  SIREN / SIRET HubSpot à clé de contrôle fausse -> CLÉ INVALIDE (signalé, non modifié).
  Entreprise étrangère -> HORS FRANCE (non recherchée).
  Optionnel : envoyer le CSV complété par email (par défaut à gcotte@alter-watt.fr).

Colonne « Statut enrichissement » du CSV complété : Trouvé, À vérifier ou Fermée (SIRET connu
d'une entreprise cessée) ; vide quand rien n'est écrit. Mesure du 23/10/2026 sur 2 000 fiches
HubSpot dont le SIREN était connu : « Trouvé » juste à 97 %, « À vérifier » à 78 %, cas « À
ARBITRER » à 47 % (voir README).

Aucune dépendance externe : uniquement la bibliothèque standard Python (3.8+).

Exemples :
  python enrichissement_siren_siret.py entreprises.csv
  python enrichissement_siren_siret.py entreprises.csv -o entreprises_completees.csv
  python enrichissement_siren_siret.py entreprises.csv --envoyer
  python enrichissement_siren_siret.py entreprises.csv --col-nom "Company name"
  python enrichissement_siren_siret.py entreprises.csv --cache cache_api   # réponses gardées

Envoi d'email (--envoyer) : configurer les variables d'environnement
  SMTP_HOST, SMTP_PORT (défaut 587), SMTP_USER, SMTP_PASSWORD, SMTP_FROM (défaut SMTP_USER)
Pour Google Workspace : SMTP_HOST=smtp.gmail.com et un « mot de passe d'application ».
"""

import argparse
import base64
import collections
import csv
import difflib
import hashlib
import http.client
import io
import json
import os
import re
import smtplib
import ssl
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from email.message import EmailMessage

API_HOTE = "recherche-entreprises.api.gouv.fr"      # API de l'Annuaire des Entreprises
GEO_HOTE = "data.geopf.fr"                          # géocodeur de la Géoplateforme (IGN)
ANNUAIRE_URL = "https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}"
DESTINATAIRE_DEFAUT = "gcotte@alter-watt.fr"

# L'API autorise 7 requêtes / seconde : on reste largement en dessous.
DELAI_ENTRE_REQUETES = 0.25
PAR_PAGE = 25                  # maximum autorisé par l'API
LIMITE_ETABLISSEMENTS = 100    # établissements renvoyés par entreprise (maximum de l'API)
SEUIL_GEOCODAGE = 0.6

PAYS_FRANCE = {"", "france", "fr", "fra", "france metropolitaine", "reunion", "la reunion",
               "guadeloupe", "martinique", "guyane", "mayotte"}

SEUIL_NOM = 0.80
SEUIL_NOM_CORRECTION = 0.90   # nom quasi identique exigé avant de corriger une adresse
SEUIL_VOIE = 0.75

# Fiabilité d'un résultat : « trouvé » (écrit, « Trouvé »), « à vérifier » (écrit,
# « À vérifier »), « à arbitrer » (proposé dans le rapport, non écrit sauf --ecrire-incertains).
TROUVE, A_VERIFIER, A_ARBITRER = "trouvé", "à vérifier", "à arbitrer"

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
    "statut_enrichissement": ["statut enrichissement"],
    "decideur": ["type de decideur", "type_de_decideur"],
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


SIREN_LA_POSTE = "356000000"


def cle_valide(numero):
    """Clé de contrôle d'un SIREN (9 chiffres) ou d'un SIRET (14 chiffres) : algorithme de
    Luhn ; les SIRET de La Poste suivent une autre règle (somme des chiffres multiple de 5)."""
    if not numero or not numero.isdigit() or len(numero) not in (9, 14):
        return False
    if len(numero) == 14 and numero.startswith(SIREN_LA_POSTE):
        return sum(int(c) for c in numero) % 5 == 0
    total = 0
    for i, c in enumerate(reversed(numero)):
        d = int(c) * (2 if i % 2 else 1)
        total += d - 9 if d > 9 else d
    return total % 10 == 0


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
    # « Alter Watt » vs « Alter Watt Energies » : l'un contient l'autre mot pour mot. Un nom
    # réduit à un seul mot du nom HubSpot ne suffit pas : « GENERALE » n'est pas « Générale
    # des Eaux du Nord ».
    mots_c, mots_n = set(cible.split()), set(candidat.split())
    if mots_c <= mots_n and (len(mots_c) >= 2 or len(cible) >= 5):
        score = max(score, 0.9)
    elif mots_n < mots_c and len(mots_n) >= 2:
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


RE_MAIRIE = re.compile(r"^\s*(mairie|ville|h[oô]tel de ville)\b\s*(-\s*|de\s+|d'|d’|du\s+)?", re.I)


def nom_officiel(nom):
    """« Mairie de X », « Ville de X », « Mairie - X » -> « Commune de X » (nom INSEE)."""
    return RE_MAIRIE.sub("Commune de ", nom or "", count=1)


def score_nom(nom_crm, resultat, ecole=False, ville=""):
    """Meilleure similarité entre le nom HubSpot (et ses parties) et les noms de l'entreprise."""
    parties = parties_nom(nom_officiel(nom_crm), ville) or [nom_crm]
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

class Connexion:
    """Connexion HTTPS persistante vers un hôte, par le proxy HTTPS s'il y en a un. Réutiliser
    une connexion ouverte est plus rapide, et plus fiable derrière certains proxys, que d'en
    ouvrir une à chaque requête."""

    def __init__(self, hote, timeout=20):
        self.hote, self.timeout = hote, timeout
        self.c = None

    def _ouvrir(self):
        contexte = ssl.create_default_context()
        proxy = urllib.request.getproxies().get("https")
        if proxy and not urllib.request.proxy_bypass(self.hote):
            p = urllib.parse.urlparse(proxy if "://" in proxy else "http://" + proxy)
            entetes = {}
            if p.username:
                ident = "{}:{}".format(urllib.parse.unquote(p.username),
                                       urllib.parse.unquote(p.password or ""))
                entetes["Proxy-Authorization"] = "Basic " + base64.b64encode(ident.encode()).decode()
            c = http.client.HTTPSConnection(p.hostname, p.port or 8080, timeout=self.timeout,
                                            context=contexte)
            c.set_tunnel(self.hote, 443, headers=entetes)
            return c
        return http.client.HTTPSConnection(self.hote, 443, timeout=self.timeout, context=contexte)

    def get(self, chemin):
        """(statut HTTP, corps). Lève OSError / HTTPException si la connexion tombe."""
        if self.c is None:
            self.c = self._ouvrir()
        try:
            self.c.request("GET", chemin, headers={"Accept": "application/json",
                                                   "User-Agent": "AlterWatt-enrichissement-CRM/2.0"})
            r = self.c.getresponse()
            return r.status, r.read()
        except (OSError, http.client.HTTPException):
            self.fermer()
            raise

    def fermer(self):
        if self.c is not None:
            try:
                self.c.close()
            except OSError:
                pass
        self.c = None


class ClientAnnuaire:
    """API de l'Annuaire des Entreprises et géocodeur de la Géoplateforme : connexions
    persistantes, reprises sur coupure réseau, cache disque facultatif (`cache` = dossier où
    chaque réponse est gardée, pour relancer un fichier à l'identique et sans appel)."""

    def __init__(self, delai=DELAI_ENTRE_REQUETES, timeout=20, tentatives=20, cache=None):
        self.delai, self.timeout, self.tentatives, self.cache = delai, timeout, tentatives, cache
        self._dernier_appel = 0.0
        self.connexions = {}
        self.dernier_total = 0
        self.appels = 0
        if cache:
            os.makedirs(cache, exist_ok=True)

    def _lire_json(self, hote, chemin):
        fichier = None
        if self.cache:
            cle = hashlib.sha1((hote + chemin).encode("utf-8")).hexdigest()
            fichier = os.path.join(self.cache, cle + ".json")
            if os.path.exists(fichier):
                with open(fichier, encoding="utf-8") as f:
                    return json.load(f)
        connexion = self.connexions.setdefault(hote, Connexion(hote, self.timeout))
        for tentative in range(self.tentatives):
            attente = self.delai - (time.time() - self._dernier_appel)
            if attente > 0:
                time.sleep(attente)
            self._dernier_appel = time.time()
            try:
                statut, corps = connexion.get(chemin)
            except (OSError, http.client.HTTPException):
                time.sleep(min(0.5 * (tentative + 1), 5))     # coupure : nouvelle connexion
                continue
            self.appels += 1
            if statut == 429 or statut >= 500:
                time.sleep(min(2 ** tentative, 30))
                continue
            if statut in (400, 404):
                donnees = {}                                  # requête refusée (nom < 3 lettres...)
            elif statut != 200:
                raise RuntimeError("HTTP {} sur https://{}{}".format(statut, hote, chemin))
            else:
                donnees = json.loads(corps.decode("utf-8"))
            if fichier:
                with open(fichier, "w", encoding="utf-8") as f:
                    json.dump(donnees, f, ensure_ascii=False)
            return donnees
        raise RuntimeError("L'API de l'Annuaire des Entreprises ne répond pas "
                           "(https://{}{})".format(hote, chemin))

    def rechercher(self, texte, par_page=5, page=1, **filtres):
        """Résultats de la recherche ; self.dernier_total = nombre total de résultats."""
        params = {"q": texte, "per_page": par_page, "page": page}
        params.update({k: v for k, v in filtres.items() if v})
        reponse = self._lire_json(API_HOTE, "/search?" + urllib.parse.urlencode(params))
        self.dernier_total = reponse.get("total_results", 0)
        return reponse.get("results") or []

    def departements(self, ville):
        """Départements possibles d'une ville (« Saint-Denis » -> 974, 93, 11), par géocodage."""
        ville = normaliser_ville(ville)
        if len(ville) < 3:
            return []
        chemin = "/geocodage/search?" + urllib.parse.urlencode(
            {"q": ville, "type": "municipality", "limit": 5})
        try:
            return departements_geocodage(self._lire_json(GEO_HOTE, chemin))
        except RuntimeError:
            return []


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


def reponse(statut, resultat, etab, rang, detail, recherche, niveau=TROUVE):
    return {"siren": resultat.get("siren"), "siret": etab.get("siret"), "statut": statut,
            "detail": detail, "rang": rang, "recherche": recherche, "niveau": niveau,
            "nom_trouve": resultat.get("nom_complet") or "",
            "adresse_trouvee": adresse_etablissement(etab), "etablissement": etab}


MESSAGE_FERMEE = ("entreprise cessée : vérifier si elle a un successeur actif avant de supprimer "
                  "la fiche ou de la marquer radiée (INPI)")
MESSAGE_FERMEE_NOM = ("société cessée trouvée par le nom : souvent une ancienne entité d'une "
                      "entreprise active (successeur, filiale) ; SIREN proposé non écrit")


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
                return reponse("FERMÉE", resultat, etab, rang, MESSAGE_FERMEE, requete, TROUVE)
            ok, detail = comparer_adresse(ligne["adresse"], ligne["ville"],
                                          ligne["code_postal"], etab)
            if ok and detail != "ville seule":
                return reponse("TROUVÉ", resultat, etab, rang,
                               "adresse vérifiée par le SIRET", requete, TROUVE)
            detail = "adresse HubSpot différente de celle du SIRET dans l'Annuaire"
            if not ligne["adresse"]:
                detail = "pas d'adresse dans HubSpot : adresse de l'Annuaire à reporter"
            if etab.get("etat_administratif") == "F":
                detail += " ; cet établissement est fermé"
            return reponse("ADRESSE À VÉRIFIER", resultat, etab, rang, detail, requete, A_VERIFIER)
    # Le SIREN est toujours les 9 premiers chiffres du SIRET : on l'écrit, à vérifier.
    return {"statut": "À VÉRIFIER", "siren": siren, "siret": siret, "niveau": A_VERIFIER,
            "detail": "SIRET introuvable dans l'Annuaire : SIREN déduit du SIRET, "
                      "adresse non vérifiée"}


def departements_geocodage(reponse):
    """Départements des communes les mieux classées par le géocodeur (homonymes compris)."""
    communes = [f.get("properties") or {} for f in (reponse or {}).get("features") or []]
    communes = [c for c in communes if c.get("citycode") and (c.get("score") or 0) >= SEUIL_GEOCODAGE]
    if not communes:
        return []
    meilleur = max(c["score"] for c in communes)
    deps = []
    for c in communes:
        if c["score"] >= meilleur - 0.05:
            code = c["citycode"]
            dep = code[:3] if code.startswith("97") else code[:2]
            if dep not in deps:
                deps.append(dep)
    return deps


def regime(decideur, defaut="local"):
    """« Centralisé » -> groupe, « Décentralisé » -> local, sinon la règle par défaut."""
    valeur = normaliser(decideur)
    if valeur == "centralise":
        return "groupe"
    if valeur == "decentralise":
        return "local"
    return defaut


NAF_TETE_DE_GROUPE = {"64.20Z": 3, "70.10Z": 2}    # holdings ; sièges sociaux


def profil_groupe(resultat):
    """Indices qu'une unité légale est une tête de groupe (0 = aucun)."""
    nom = normaliser(resultat.get("nom_complet") or "")
    score = NAF_TETE_DE_GROUPE.get(resultat.get("activite_principale") or "", 0)
    if re.search(r"\bholding\b", nom):
        score += 4
    if re.search(r"\bgroupe?\b", nom):
        score += 1
    return score


FORMES_STRICTES = {"sa", "sas", "sasu", "sarl", "eurl", "sci", "snc", "scop", "scic", "sca", "scs",
                   "selarl", "selas", "gie", "ei", "eirl", "sem", "spl", "se", "societe", "ste",
                   "de", "du", "des", "la", "le", "les", "et", "and", "the"}


def nom_court(nom):
    """Nom sans forme juridique ni lettres isolées (« ACME S.E. » -> « acme »), mais avec
    « groupe », « holding », « France » et les numéros, qui distinguent les entités d'un groupe."""
    mots = normaliser(re.sub(r"\(.*?\)", " ", nom or "")).split()
    return " ".join(m for m in mots if m not in FORMES_STRICTES and not (len(m) == 1 and m.isalpha()))


def nom_identique(nom_crm, resultat):
    """Le nom légal (raison sociale, nom complet ou sigle, sans les enseignes) est celui de HubSpot."""
    cibles = {nom_court(p) for p in parties_nom(nom_crm) or [nom_crm]} - {""}
    noms = [resultat.get("nom_raison_sociale"), resultat.get("nom_complet"), resultat.get("sigle")]
    return any(nom_court(n) in cibles for n in noms if n)


CATEGORIES_ENTREPRISE = {"GE": 3, "ETI": 2, "PME": 1}


def taille(resultat):
    return (CATEGORIES_ENTREPRISE.get(resultat.get("categorie_entreprise") or "", 0),
            resultat.get("nombre_etablissements_ouverts") or 0)


def departager(choix, nom_crm, regime_decideur):
    """
    Plusieurs SIREN du même nom au même endroit (filiales domiciliées au siège, SCI, CSE...).
    Centralisé : nom identique, puis tête de groupe (holding, NAF 64.20Z / 70.10Z), puis taille ;
    Décentralisé : nom identique, puis entité qui n'est pas une holding, puis taille.
    Renvoie (choix, règle) ou (None, None) si rien ne départage.
    """
    def cle(c):
        resultat = c[1]
        groupe = profil_groupe(resultat)
        profil = groupe if regime_decideur == "groupe" else -min(groupe, 1)
        # En dernier recours, l'ordre de l'API (pertinence puis taille), comme la v1.
        return nom_identique(nom_crm, resultat), profil, taille(resultat), -c[0]
    classes = sorted(choix, key=cle, reverse=True)
    if cle(classes[0]) == cle(classes[1]):
        return None, None
    regle = ("tête de groupe retenue (Centralisé)" if regime_decideur == "groupe"
             else "entité locale retenue (Décentralisé)")
    return classes[0], "{} parmi {} entités du même nom".format(regle, len(choix))


def candidats_du_nom(resultats, ligne, siren_connu, rejets):
    """Entreprises dont le nom correspond : [(rang, résultat)]."""
    candidats = []
    for rang, resultat in enumerate(resultats, start=1):
        if siren_connu:
            if resultat.get("siren") == siren_connu:
                candidats.append((rang, resultat))
            continue
        if score_nom(ligne["nom"], resultat, ligne.get("ecole", False), ligne["ville"]) < SEUIL_NOM:
            rejets.append("#{} {} : nom différent".format(rang, resultat.get("nom_complet") or ""))
            continue
        if ligne.get("ecole") and not type_compatible(resultat):
            rejets.append("#{} {} : pas un établissement d'enseignement / association"
                          .format(rang, resultat.get("nom_complet") or ""))
            continue
        candidats.append((rang, resultat))
    return candidats


def localiser(candidats, ligne):
    """
    Trie les entreprises du nom par lieu : {"adresse": {siren: (rang, résultat, étab)},
    "ville": {...}}. Seuls les établissements actifs comptent, sauf pour une entreprise cessée
    (pour la signaler FERMÉE).
    """
    lieux = {"adresse": {}, "ville": {}}
    for rang, resultat in candidats:
        fermee = entreprise_fermee(resultat)
        for etab in etablissements_candidats(resultat):
            if not fermee and etab.get("etat_administratif") == "F":
                continue
            if ligne["adresse"]:
                ok, detail = comparer_adresse(ligne["adresse"], ligne["ville"],
                                              ligne["code_postal"], etab)
                if ok and detail != "ville seule":
                    lieux["adresse"].setdefault(resultat.get("siren"), (rang, resultat, etab))
                    continue
            if ligne["ville"] or ligne["code_postal"]:
                ok, _ = comparer_adresse("", ligne["ville"], ligne["code_postal"], etab)
                if ok:
                    lieux["ville"].setdefault(resultat.get("siren"), (rang, resultat, etab))
    for niveau in lieux:
        # Des entreprises actives au même endroit : les entreprises cessées sont ignorées.
        actives = {s: c for s, c in lieux[niveau].items() if not entreprise_fermee(c[1])}
        if actives:
            lieux[niveau] = actives
    return lieux


def trouver_entreprise(client, ligne, max_resultats=5):
    """
    Arbre de décision :
      0. SIRET déjà renseigné -> recherche par SIRET (voir trouver_par_siret).
      1. Recherche du nom seul (ou du SIREN s'il est connu), puis de chaque partie du nom ;
         la ville n'est jamais dans la requête.
      2. Tri par lieu des entreprises du nom : adresse, puis ville (2e requête filtrée sur les
         départements de la ville si aucune n'y est). Plusieurs SIREN au même endroit :
         départage selon le « Type de décideur » (voir departager), à arbitrer.
      3. Ni adresse ni ville : une seule structure du nom -> TROUVÉ (NOM UNIQUE).
      4. Sinon -> RECHERCHE INTERNET.
    Chaque résultat porte un niveau de fiabilité (TROUVE, A_VERIFIER, A_ARBITRER), mesuré sur
    2 000 fiches dont le SIREN était connu (voir README).
    """
    nom = ligne["nom"]
    siret_connu = ligne.get("siret")
    if siret_connu:
        return trouver_par_siret(client, ligne, siret_connu, max_resultats)
    siren_connu = ligne["siren"]
    if not (nom or siren_connu):
        return {"statut": "RECHERCHE INTERNET", "detail": "nom de l'entreprise vide"}
    regime_decideur = ligne.get("regime", "local")
    rejets = []

    # 1. Le nom seul : la ville ne sert qu'à trier les résultats.
    candidats, requete, total = [], None, 0
    for variante in [siren_connu] if siren_connu else (parties_nom(nom, ligne["ville"]) or [nom]):
        resultats = client.rechercher(variante, par_page=PAR_PAGE,
                                      limite_matching_etablissements=LIMITE_ETABLISSEMENTS)
        total = getattr(client, "dernier_total", len(resultats))
        candidats = candidats_du_nom(resultats, ligne, siren_connu, rejets)
        requete = variante
        if candidats:
            break
    if not candidats:
        return {"statut": "RECHERCHE INTERNET",
                "detail": " | ".join(dict.fromkeys(rejets)) or
                          "aucun résultat dans l'Annuaire des Entreprises"}

    def conclure(choix, statut, detail, recherche, niveau):
        """Une société cessée trouvée par le nom est toujours à arbitrer."""
        rang, resultat, etab = choix
        if entreprise_fermee(resultat):
            res = reponse("À ARBITRER", resultat, etab, rang,
                          MESSAGE_FERMEE_NOM + " (" + detail + ")", recherche, A_ARBITRER)
        elif niveau == A_ARBITRER:
            res = reponse("À ARBITRER", resultat, etab, rang,
                          "{} ; SIREN proposé non écrit ({})".format(detail, statut), recherche,
                          A_ARBITRER)
        else:
            res = reponse(statut, resultat, etab, rang, detail, recherche, niveau)
        res["total_api"] = total
        return res

    # 2. Tri par lieu.
    if ligne["adresse"] or ligne["ville"] or ligne["code_postal"]:
        lieux = localiser(candidats, ligne)
        recherche = requete
        if not lieux["adresse"] and not lieux["ville"] and ligne["ville"]:
            deps = client.departements(ligne["ville"])
            if deps:
                resultats = client.rechercher(requete, par_page=PAR_PAGE,
                                              limite_matching_etablissements=LIMITE_ETABLISSEMENTS,
                                              departement=",".join(deps))
                lieux = localiser(candidats_du_nom(resultats, ligne, siren_connu, []), ligne)
                recherche = "{} [départements {}]".format(requete, ",".join(deps))
        for lieu in ("adresse", "ville"):
            trouves = lieux[lieu]
            if not trouves:
                continue
            if lieu == "adresse":
                statut, detail, niveau = "TROUVÉ", "nom et adresse vérifiés", TROUVE
            elif ligne["adresse"] and not ligne.get("adresse_generique"):
                statut, detail, niveau = ("ADRESSE CORRIGÉE",
                                          "nom et ville vérifiés, adresse HubSpot différente",
                                          A_VERIFIER)
            else:
                statut, detail, niveau = ("TROUVÉ (VILLE)",
                                          "pas d'adresse dans HubSpot : nom et ville vérifiés",
                                          A_VERIFIER)
                if ligne.get("adresse_generique"):
                    detail = "adresse HubSpot générique ignorée : nom et ville vérifiés"
            if len(trouves) == 1:
                return conclure(next(iter(trouves.values())), statut, detail, recherche, niveau)
            choix, regle = departager(list(trouves.values()), nom, regime_decideur)
            if choix:
                return conclure(choix, statut, detail + " ; " + regle, recherche, A_ARBITRER)
            rejets.append("« {} » : {} entreprises du même nom {}".format(
                requete, len(trouves), "à cette adresse" if lieu == "adresse" else "dans cette ville"))
            return {"statut": "RECHERCHE INTERNET", "detail": " | ".join(dict.fromkeys(rejets))}
        # Aucun établissement à cet endroit : une seule entreprise de ce nom (nom quasi
        # identique), en activité -> son siège, à arbitrer.
        sirens = {r.get("siren"): (rang, r) for rang, r in candidats}
        if len(sirens) == 1:
            rang, resultat = next(iter(sirens.values()))
            if (not entreprise_fermee(resultat) and (resultat.get("siege") or {}).get("siret")
                    and score_nom(nom, resultat, ligne.get("ecole", False),
                                  ligne["ville"]) >= SEUIL_NOM_CORRECTION):
                return conclure((rang, resultat, resultat["siege"]), "ADRESSE CORRIGÉE",
                                "seule entreprise de ce nom, aucun établissement dans cette "
                                "ville : siège retenu", recherche, A_ARBITRER)
        rejets.append("« {} » : nom trouvé, mais aucun établissement à cette adresse ou dans "
                      "cette ville (ville différente)".format(requete))
        return {"statut": "RECHERCHE INTERNET", "detail": " | ".join(dict.fromkeys(rejets))}

    # 3. Ni adresse ni ville : il faut une seule structure de ce nom.
    sirens = {resultat.get("siren"): (rang, resultat) for rang, resultat in candidats}
    if len(sirens) == 1:
        rang, resultat = next(iter(sirens.values()))
        etab = (resultat.get("siege") or {})
        detail = "ni adresse ni ville : seule structure de ce nom ({} résultat(s) API)".format(total)
        return conclure((rang, resultat, etab), "TROUVÉ (NOM UNIQUE)", detail, requete,
                        TROUVE if ligne.get("nom_unique_trouve") else A_VERIFIER)
    return {"statut": "RECHERCHE INTERNET",
            "detail": "ni adresse ni ville : {} structures du même nom".format(len(sirens))}


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
        "ligne.\n\n{}\n\nLa colonne « Statut enrichissement » du CSV indique les SIREN sûrs "
        "(Trouvé) et ceux à contrôler (À vérifier). La colonne « Action à mener » du rapport "
        "indique les SIREN proposés mais non écrits (À ARBITRER), les entreprises cessées "
        "(FERMÉE, à vérifier avant toute suppression) et les fiches à chercher sur Internet "
        "(RECHERCHE INTERNET).\n\nBonne journée".format(resume))
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


COLONNE_STATUT = "Statut enrichissement"
ACTIONS = {
    "TROUVÉ": "SIREN/SIRET ajoutés",
    "TROUVÉ (VILLE)": "SIREN/SIRET ajoutés (nom et ville vérifiés) ; à contrôler",
    "TROUVÉ (NOM UNIQUE)": "SIREN/SIRET ajoutés (seule structure de ce nom)",
    "ADRESSE CORRIGÉE": "SIREN/SIRET ajoutés + adresse corrigée ; à contrôler",
    "ADRESSE À VÉRIFIER": "SIREN ajouté ; comparer l'adresse HubSpot à celle de l'Annuaire",
    "FERMÉE": "Entreprise cessée : chercher un successeur avant de supprimer la fiche",
    "À ARBITRER": "Choisir : SIREN proposé dans le rapport, non écrit (voir Détail)",
    "CLÉ INVALIDE": "Corriger le SIREN/SIRET HubSpot (clé de contrôle fausse) ; voir Détail",
    "INCOHÉRENT": "Corriger : le SIRET ne commence pas par le SIREN",
    "À VÉRIFIER": "SIREN/SIRET ajoutés ; contrôler manuellement",
    "RECHERCHE INTERNET": "Chercher sur Internet",
    "HORS FRANCE": "Aucune (entreprise étrangère)",
}
ORDRE_STATUTS = ["TROUVÉ", "TROUVÉ (VILLE)", "TROUVÉ (NOM UNIQUE)", "ADRESSE CORRIGÉE",
                 "ADRESSE À VÉRIFIER", "À VÉRIFIER", "FERMÉE", "À ARBITRER", "CLÉ INVALIDE",
                 "INCOHÉRENT", "RECHERCHE INTERNET", "HORS FRANCE", "DÉJÀ RENSEIGNÉ"]


def statut_rendu(res):
    """Valeur de la colonne « Statut enrichissement » du CSV complété."""
    if res["statut"] == "FERMÉE":
        return "Fermée"
    return "Trouvé" if res.get("niveau") == TROUVE else "À vérifier"


def a_ecrire(res, ecrire_incertains=False):
    """Le SIREN trouvé est-il écrit dans le CSV ?"""
    if not res.get("siren"):
        return False
    niveau = res.get("niveau")
    return niveau in (TROUVE, A_VERIFIER) or (niveau == A_ARBITRER and ecrire_incertains)


def traiter(chemin_entree, chemin_sortie, chemin_rapport, forcees, max_resultats,
            client=None, corriger_adresse=True, defaut_decideur="local",
            nom_unique_trouve=False, ecrire_incertains=False):
    entetes, lignes, separateur, _ = lire_csv(chemin_entree)
    colonnes = detecter_colonnes(entetes, forcees)
    # Colonne de statut juste à droite de « SIRET » (réutilisée si le fichier en a déjà une,
    # par exemple quand on relance le script sur un CSV déjà complété).
    col_statut = colonnes.get("statut_enrichissement")
    statuts_rendus = {}
    client = client or ClientAnnuaire()

    rapport = []
    compteurs = collections.Counter({statut: 0 for statut in ORDRE_STATUTS})
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
        # Un SIREN / SIRET à clé de contrôle fausse est une erreur de saisie : on cherche sans
        # lui, et on ne le remplace pas (CLÉ INVALIDE).
        invalides = ["{} {}".format(nom, numero_lu) for nom, numero_lu in
                     (("SIREN", siren), ("SIRET", siret)) if numero_lu and not cle_valide(numero_lu)]
        if siren and not cle_valide(siren):
            siren = ""
        if siret and not cle_valide(siret):
            siret = ""
        donnees["siren"], donnees["siret"] = siren, siret
        donnees["ecole"] = est_ecole(donnees["nom"], donnees["categorie"]) or \
            normaliser(donnees["secteur"]).startswith("enseignement")
        donnees["adresse_generique"] = normaliser(donnees["adresse"]) in generiques
        if donnees["adresse_generique"]:
            # Adresse partagée par des fiches de villes différentes : elle est fausse.
            donnees["adresse"] = ""
        donnees["regime"] = regime(donnees["decideur"], defaut_decideur)
        donnees["nom_unique_trouve"] = nom_unique_trouve

        if not invalides and siren and siret and siret[:9] == siren:
            compteurs["DÉJÀ RENSEIGNÉ"] += 1
            continue
        if siren and siret and siret[:9] != siren:
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
        if invalides:
            propose = ("SIREN proposé : {} ({}, {})".format(res["siren"], res["statut"], res["detail"])
                       if res.get("siren") else "rien trouvé dans l'Annuaire ({})".format(
                           res.get("detail", "")))
            res = dict(res, statut="CLÉ INVALIDE", niveau=None,
                       detail="{} : clé de contrôle fausse, non modifié ; {}".format(
                           " / ".join(invalides), propose))

        statut = res["statut"]
        compteurs[statut] += 1
        ecrit = a_ecrire(res, ecrire_incertains)
        nouvelle_adresse = ""
        if ecrit:
            statuts_rendus[numero - 1] = statut_rendu(res)
            if not nettoyer_numero(ligne[colonnes["siren"]], 9):
                ligne[colonnes["siren"]] = res["siren"]
            if not siret:
                ligne[colonnes["siret"]] = res["siret"]
        if ecrit and statut == "ADRESSE CORRIGÉE" and corriger_adresse:
            etab = res["etablissement"]
            nouvelle_adresse = mettre_en_forme(rue_etablissement(etab))
            if "adresse" in colonnes and nouvelle_adresse:
                ligne[colonnes["adresse"]] = nouvelle_adresse
            if "ville" in colonnes and etab.get("libelle_commune"):
                ligne[colonnes["ville"]] = mettre_en_forme(etab["libelle_commune"])
            if "code_postal" in colonnes and etab.get("code_postal"):
                ligne[colonnes["code_postal"]] = etab["code_postal"]

        rapport.append([
            valeur(ligne, colonnes, "id"), donnees["nom"], donnees["adresse"], donnees["ville"],
            statut, ACTIONS.get(statut, ""), res.get("siren", ""), res.get("siret", ""),
            res.get("nom_trouve", ""), res.get("adresse_trouvee", ""), nouvelle_adresse,
            res.get("rang", ""), res.get("recherche", ""), res.get("detail", ""),
            "oui" if ecrit else "non", statut_rendu(res) if ecrit else "",
            ANNUAIRE_URL.format(siren=res["siren"]) if res.get("siren") else "",
        ])
        print("[{}/{}] {:<40.40} {:<19} {} {}".format(
            numero, total, donnees["nom"], statut, res.get("siren", "") or "",
            res.get("siret", "") or ""), flush=True)

    if col_statut is None:
        col_statut = colonnes["siret"] + 1
        entetes.insert(col_statut, COLONNE_STATUT)
        for ligne in lignes:
            if any(c.strip() for c in ligne):
                ligne.insert(col_statut, "")
    for index, rendu in statuts_rendus.items():
        lignes[index][col_statut] = rendu
    ecrire_csv(chemin_sortie, entetes, lignes, separateur)
    ecrire_csv(chemin_rapport, [
        "ID HubSpot", "Nom HubSpot", "Adresse HubSpot", "Ville HubSpot", "Statut",
        "Action à mener", "SIREN trouvé", "SIRET trouvé", "Nom Annuaire", "Adresse Annuaire",
        "Nouvelle adresse écrite", "Rang du résultat", "Recherche effectuée", "Détail",
        "Écrit dans le CSV", "Statut enrichissement", "Lien Annuaire",
    ], rapport, separateur)
    return dict(compteurs)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Complète les SIREN / SIRET d'un export d'entreprises HubSpot à partir "
                    "de l'Annuaire des Entreprises (annuaire-entreprises.data.gouv.fr).")
    parser.add_argument("csv", help="CSV d'entrée (export HubSpot)")
    parser.add_argument("-o", "--sortie", help="CSV de sortie (défaut : <entrée>_complete.csv)")
    parser.add_argument("--rapport", help="Rapport détaillé (défaut : <entrée>_rapport.csv)")
    parser.add_argument("--max-resultats", type=int, default=5,
                        help="Résultats examinés pour une recherche par SIRET (défaut 5) ; la "
                             "recherche par nom en examine toujours 25")
    parser.add_argument("--defaut-decideur", choices=("local", "groupe"), default="local",
                        help="SIREN à retenir quand le « Type de décideur » est vide ou « Ne sais "
                             "pas encore » et que plusieurs entités du nom sont au même endroit "
                             "(défaut : %(default)s)")
    parser.add_argument("--nom-unique-trouve", action="store_true",
                        help="Fiche sans adresse ni ville, une seule structure de ce nom : statut "
                             "« Trouvé » au lieu de « À vérifier »")
    parser.add_argument("--ecrire-incertains", action="store_true",
                        help="Écrire aussi les SIREN « À ARBITRER » (départage entre entités d'un "
                             "même groupe, siège dans une autre ville, société cessée), en "
                             "« À vérifier » ; justes à 47 %% seulement lors du test")
    parser.add_argument("--cache", metavar="DOSSIER",
                        help="Garder chaque réponse de l'API dans ce dossier : une relance du même "
                             "fichier se fait à l'identique et sans appel")
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
                        client=ClientAnnuaire(cache=args.cache),
                        corriger_adresse=not args.sans_correction_adresse,
                        defaut_decideur=args.defaut_decideur,
                        nom_unique_trouve=args.nom_unique_trouve,
                        ecrire_incertains=args.ecrire_incertains)
    resume = ("Résultat : {TROUVÉ} trouvée(s) à la bonne adresse, {TROUVÉ (NOM UNIQUE)} seule(s) "
              "structure(s) de ce nom (sans adresse ni ville), {TROUVÉ (VILLE)} trouvée(s) sur le "
              "nom et la ville, {ADRESSE CORRIGÉE} avec adresse corrigée, {ADRESSE À VÉRIFIER} "
              "adresse(s) à vérifier (SIRET connu), {À VÉRIFIER} à vérifier, {FERMÉE} fermée(s), "
              "{À ARBITRER} à arbitrer (SIREN proposé, non écrit), {CLÉ INVALIDE} SIREN/SIRET à clé "
              "fausse, {INCOHÉRENT} SIREN/SIRET incohérent(s), {RECHERCHE INTERNET} à chercher sur "
              "Internet, {HORS FRANCE} hors France, {DÉJÀ RENSEIGNÉ} déjà renseignée(s)."
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
