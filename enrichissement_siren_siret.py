#!/usr/bin/env python3
"""
Enrichissement SIREN / SIRET des entreprises HubSpot via l'Annuaire des Entreprises.

Source : https://annuaire-entreprises.data.gouv.fr/ — le script interroge l'API
publique officielle qui alimente ce site (https://recherche-entreprises.api.gouv.fr),
ce qui renvoie exactement les mêmes résultats, dans le même ordre, que la recherche
sur le site, sans avoir à analyser les pages HTML.

Démarche (identique aux consignes données à un humain) :
  1. Pour chaque ligne du CSV dont le SIREN ou le SIRET est vide, rechercher le nom
     de l'entreprise.
  2. Parcourir les résultats dans l'ordre (1er, puis 2e, ...) et, pour chacun,
     vérifier que le nom correspond ET que l'adresse postale est la bonne.
  3. Au premier résultat qui correspond, récupérer le SIREN et le SIRET de
     l'établissement situé à cette adresse et les écrire dans le CSV.
  4. Les lignes où SIREN et SIRET sont déjà remplis sont ignorées.
  5. Optionnel : envoyer le CSV complété par email (par défaut à gcotte@alter-watt.fr).

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

SEUIL_NOM = 0.80
SEUIL_VOIE = 0.75

# Noms de colonnes reconnus automatiquement (comparés sans accents ni casse).
ALIAS_COLONNES = {
    "id": ["record id", "id", "id hubspot", "hubspot id", "company id", "id entreprise",
           "id de la fiche", "id fiche"],
    "nom": ["nom de l'entreprise", "nom entreprise", "nom", "company name", "name",
            "raison sociale", "entreprise"],
    "secteur": ["secteur d'activite", "secteur", "industry", "activite"],
    "adresse": ["adresse postale", "adresse", "street address", "address", "adresse 1",
                "rue"],
    "ville": ["ville", "city", "commune"],
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

def score_nom(nom_crm, resultat):
    """Meilleure similarité entre le nom HubSpot et les noms connus de l'entreprise."""
    cible = normaliser_nom(nom_crm)
    if not cible:
        return 0.0
    candidats = [resultat.get("nom_complet"), resultat.get("nom_raison_sociale"),
                 resultat.get("sigle")]
    for etab in [resultat.get("siege") or {}] + (resultat.get("matching_etablissements") or []):
        candidats.extend(etab.get("liste_enseignes") or [])
        candidats.append(etab.get("nom_commercial"))
    meilleur = 0.0
    for candidat in candidats:
        nom = normaliser_nom(candidat)
        if not nom:
            continue
        if nom == cible:
            return 1.0
        score = similarite(cible, nom)
        # « Alter Watt » vs « Alter Watt Energies » : l'un contient l'autre mot pour mot.
        mots_c, mots_n = set(cible.split()), set(nom.split())
        if mots_c and mots_n and (mots_c <= mots_n or mots_n <= mots_c):
            score = max(score, 0.9)
        meilleur = max(meilleur, score)
    return meilleur


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
    num_crm, mots_crm, cp_dans_adresse = decomposer_adresse(adresse_crm)
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
    """Siège + établissements correspondant à la recherche, actifs d'abord."""
    etabs, vus = [], set()
    for etab in (resultat.get("matching_etablissements") or []) + [resultat.get("siege") or {}]:
        siret = etab.get("siret")
        if siret and siret not in vus:
            vus.add(siret)
            etabs.append(etab)
    etabs.sort(key=lambda e: (e.get("etat_administratif") == "F", not e.get("est_siege")))
    return etabs


def trouver_entreprise(client, ligne, max_resultats=5):
    """
    Applique la démarche « 1er résultat, sinon 2e, ... » et renvoie un dict
    {siren, siret, statut, detail, rang, nom_trouve}.
    """
    nom = ligne["nom"]
    siren_connu = ligne["siren"]
    requete = siren_connu or nom
    if not requete:
        return {"statut": "NON TROUVÉ", "detail": "nom de l'entreprise vide"}

    resultats = client.rechercher(requete, par_page=max_resultats)
    if not resultats and ligne["ville"] and not siren_connu:
        # Deuxième essai : nom + ville, utile pour les noms très courants.
        resultats = client.rechercher("{} {}".format(nom, ligne["ville"]), par_page=max_resultats)
    if not resultats:
        return {"statut": "NON TROUVÉ", "detail": "aucun résultat pour « {} »".format(requete)}

    rejets = []
    for rang, resultat in enumerate(resultats[:max_resultats], start=1):
        nom_trouve = resultat.get("nom_complet") or ""
        if siren_connu:
            if resultat.get("siren") != siren_connu:
                continue
        else:
            s_nom = score_nom(nom, resultat)
            if s_nom < SEUIL_NOM:
                rejets.append("#{} {} : nom différent".format(rang, nom_trouve))
                continue

        for etab in etablissements_candidats(resultat):
            ok, detail = comparer_adresse(ligne["adresse"], ligne["ville"],
                                          ligne["code_postal"], etab)
            if ok:
                statut = "TROUVÉ"
                if detail == "ville seule":
                    statut = "À VÉRIFIER"
                    detail = "pas d'adresse dans HubSpot, seule la ville a été vérifiée"
                if etab.get("etat_administratif") == "F":
                    statut = "À VÉRIFIER"
                    detail += " ; établissement fermé"
                if resultat.get("etat_administratif") == "C":
                    statut = "À VÉRIFIER"
                    detail += " ; entreprise cessée"
                return {"siren": resultat.get("siren"), "siret": etab.get("siret"),
                        "statut": statut, "detail": detail, "rang": rang,
                        "nom_trouve": nom_trouve,
                        "adresse_trouvee": adresse_etablissement(etab)}
        rejets.append("#{} {} : adresse différente ({})".format(
            rang, nom_trouve, adresse_etablissement(resultat.get("siege") or {})))

    return {"statut": "NON TROUVÉ", "detail": " | ".join(rejets) or "aucune correspondance"}


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
    lignes = list(csv.reader(texte.splitlines(), delimiter=separateur))
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
        "ligne.\n\n{}\n\nLes lignes marquées « À VÉRIFIER » ou « NON TROUVÉ » dans le "
        "rapport demandent un contrôle manuel.\n\nBonne journée".format(resume))
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

def traiter(chemin_entree, chemin_sortie, chemin_rapport, forcees, max_resultats,
            remplir_a_verifier, client=None):
    entetes, lignes, separateur, _ = lire_csv(chemin_entree)
    colonnes = detecter_colonnes(entetes, forcees)
    client = client or ClientAnnuaire()

    rapport = []
    compteurs = {"TROUVÉ": 0, "À VÉRIFIER": 0, "NON TROUVÉ": 0, "DÉJÀ RENSEIGNÉ": 0}
    total = len(lignes)

    for numero, ligne in enumerate(lignes, start=1):
        if not any(c.strip() for c in ligne):
            continue
        while len(ligne) < len(entetes):
            ligne.append("")
        donnees = {cle: valeur(ligne, colonnes, cle) for cle in ALIAS_COLONNES}
        siren = nettoyer_numero(donnees["siren"], 9)
        siret = nettoyer_numero(donnees["siret"], 14)
        if siren and siret:
            compteurs["DÉJÀ RENSEIGNÉ"] += 1
            continue
        if not siren and siret:
            siren = siret[:9]
        donnees["siren"] = siren

        try:
            res = trouver_entreprise(client, donnees, max_resultats=max_resultats)
        except RuntimeError as err:
            res = {"statut": "NON TROUVÉ", "detail": str(err)}

        statut = res["statut"]
        compteurs[statut] += 1
        ecrit = statut == "TROUVÉ" or (statut == "À VÉRIFIER" and remplir_a_verifier)
        if ecrit:
            if not nettoyer_numero(ligne[colonnes["siren"]], 9):
                ligne[colonnes["siren"]] = res["siren"]
            if not siret:
                ligne[colonnes["siret"]] = res["siret"]

        rapport.append([
            valeur(ligne, colonnes, "id"), donnees["nom"], donnees["adresse"], donnees["ville"],
            statut, res.get("siren", ""), res.get("siret", ""), res.get("nom_trouve", ""),
            res.get("adresse_trouvee", ""), res.get("rang", ""), res.get("detail", ""),
            "oui" if ecrit else "non",
            ANNUAIRE_URL.format(siren=res["siren"]) if res.get("siren") else "",
        ])
        print("[{}/{}] {:<40.40} {:<12} {} {}".format(
            numero, total, donnees["nom"], statut, res.get("siren", "") or "",
            res.get("siret", "") or ""), flush=True)

    ecrire_csv(chemin_sortie, entetes, lignes, separateur)
    ecrire_csv(chemin_rapport, [
        "ID HubSpot", "Nom HubSpot", "Adresse HubSpot", "Ville HubSpot", "Statut",
        "SIREN trouvé", "SIRET trouvé", "Nom Annuaire", "Adresse Annuaire",
        "Rang du résultat", "Détail", "Écrit dans le CSV", "Lien Annuaire",
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
                             "établissement fermé) dans le CSV")
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
                        args.remplir_a_verifier)
    resume = ("Résultat : {TROUVÉ} trouvée(s), {À VÉRIFIER} à vérifier, {NON TROUVÉ} non "
              "trouvée(s), {DÉJÀ RENSEIGNÉ} déjà renseignée(s).").format(**compteurs)
    print("\n" + resume)
    print("CSV complété : " + sortie)
    print("Rapport      : " + rapport)

    if args.envoyer:
        envoyer_email(args.destinataire, [sortie, rapport], resume)
        print("Email envoyé à " + args.destinataire)
    return 0


if __name__ == "__main__":
    sys.exit(main())
