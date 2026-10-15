"""
Normalisation commune à la détection des doublons HubSpot (entreprises et contacts).

Toutes les comparaisons se font sur des valeurs normalisées ; les valeurs brutes ne servent
qu'à l'affichage.

  Valeurs neutralisées  domaines factices (« 4313.co »), punycode (« xn-- »), plateformes
                        (e-lyco, wixsite...), téléphones « 00 00 00 00 00 », enveloppe Excel
                        ="…", « Ne sait pas encore », « NC », « inconnu », « n/a », « - ».
  Noms d'entreprise     nom_norm (« St » -> « Saint », « œ » -> « oe »), nom_sans_parentheses,
                        nom_equivalent (sans forme juridique, type d'établissement ni mots
                        vides), nom_distinctif (sans la ville).
  Villes                sans « cedex », sans arrondissement, « st » -> « saint »,
                        « lez » -> « les ».
  Téléphones            format national à 10 chiffres (chiffres() du script contacts).
  Domaines              hôte, domaine principal (suffixes publics à deux niveaux : gouv.fr,
                        asso.fr, ac-nantes.fr...), même domaine / même hôte / domaine proche.
  SIREN                 champ SIREN de 9 chiffres, sinon les 9 premiers chiffres du SIRET.
  Emails                webmails et adresses génériques (contact@, accueil@...).

Aucune dépendance externe : uniquement la bibliothèque standard Python (3.8+).
"""

import difflib
import re

from fusion_doublons_hubspot import (chiffres, email_valide, normaliser, ressemble_domaine,
                                     sans_accents)

__all__ = ["chiffres", "email_valide", "normaliser", "ressemble_domaine", "sans_accents"]

# --------------------------------------------------------------------------- #
# Valeurs neutralisées (traitées comme vides)
# --------------------------------------------------------------------------- #

INCONNUES = {"ne sait pas encore", "ne sais pas encore", "nc", "inconnu", "inconnue", "n/a",
             "na", "-", "--"}

# Domaines de plateformes : ils ne servent jamais de lien.
PLATEFORMES = ("e-lyco.fr", "wixsite.com", "google.com", "sites.google", "blogspot.",
               "wordpress.com", "jimdo", "free.fr", "orange.fr", "wanadoo.fr", "facebook.com")

DOMAINE_FACTICE = re.compile(r"(https?://)?(www\.)?\d+\.co/?")

# Suffixes publics à deux niveaux : le domaine principal garde alors trois labels
# (« loire-atlantique.gouv.fr » et « loire-atlantique.fr » sont deux domaines différents).
SUFFIXES_DEUX_NIVEAUX = {"gouv.fr", "asso.fr", "com.fr", "co.uk", "com.au", "org.uk", "ac.uk",
                         "gov.uk"}
SUFFIXE_ACADEMIE = re.compile(r"ac-[a-z0-9-]+\.fr")      # ac-nantes.fr, ac-lyon.fr...

SEUIL_DOMAINE_PROCHE = 0.85


def nettoyer(valeur):
    """Valeur brute débarrassée de l'enveloppe Excel ="…" ; "" si elle ne dit rien."""
    valeur = str(valeur if valeur is not None else "").strip()
    m = re.fullmatch(r'="(.*)"', valeur, re.S)
    if m:
        valeur = m.group(1).strip()
    if sans_accents(valeur).lower().strip() in INCONNUES:
        return ""
    return valeur


LIGATURES = str.maketrans({"œ": "oe", "Œ": "OE", "æ": "ae", "Æ": "AE", "ß": "ss"})


def sans_accents_ni_ligatures(texte):
    """« Sœurs » -> « Soeurs », « Tréviers » -> « Treviers »."""
    return sans_accents((texte or "").translate(LIGATURES))


def saint(texte):
    """« st » -> « saint », « ste » -> « sainte » (mots entiers, texte en minuscules)."""
    texte = re.sub(r"\bst\b", "saint", texte)
    return re.sub(r"\bste\b", "sainte", texte)


def compact(texte):
    """Forme sans espaces : « apm 22 » et « apm22 » se comparent égales."""
    return (texte or "").replace(" ", "")


# --------------------------------------------------------------------------- #
# Domaines et sites
# --------------------------------------------------------------------------- #

def hote(valeur):
    """« https://www.etu.univ-amu.fr/x » -> « etu.univ-amu.fr »."""
    v = nettoyer(valeur).lower()
    v = re.sub(r"^[a-z][a-z0-9+.-]*://", "", v)
    v = re.split(r"[/?#\s]", v)[0]
    v = v.split("@")[-1].split(":")[0]
    v = re.sub(r"^www\d*\.", "", v)
    return v.strip(".")


def plateforme(h):
    for p in PLATEFORMES:
        if p.endswith(".") or "." not in p or p == "sites.google":
            if p in h:
                return True
        elif h == p or h.endswith("." + p):
            return True
    return False


def domaine_neutralise(valeur):
    """Vrai pour un domaine vide, factice, en punycode ou sur une plateforme."""
    brut = nettoyer(valeur).lower()
    if not brut or DOMAINE_FACTICE.fullmatch(brut):
        return True
    h = hote(brut)
    return not h or "." not in h or "xn--" in h or plateforme(h)


def hote_utile(valeur):
    """Hôte d'un domaine non neutralisé, sinon ""."""
    return "" if domaine_neutralise(valeur) else hote(valeur)


def domaine_principal(valeur):
    """Deux derniers labels de l'hôte ; trois pour un suffixe public à deux niveaux.
    Un hôte réduit au suffixe (« ac-nantes.fr ») n'identifie personne : ""."""
    labels = hote(valeur).split(".")
    if len(labels) < 2 or not all(labels[-2:]):
        return ""
    suffixe = ".".join(labels[-2:])
    if suffixe in SUFFIXES_DEUX_NIVEAUX or SUFFIXE_ACADEMIE.fullmatch(suffixe):
        return ".".join(labels[-3:]) if len(labels) >= 3 else ""
    return suffixe


def _radical(domaine):
    """« loire-atlantique.gouv.fr » -> « loire-atlantique »."""
    return domaine.split(".")[0]


def comparer_domaines(hote_a, hote_b):
    """Liens et contradiction entre deux hôtes utiles (voir hote_utile) :
    meme_domaine, meme_hote, domaine_proche, domaines_differents."""
    resultat = set()
    if not hote_a or not hote_b:
        return resultat
    da, db = domaine_principal(hote_a), domaine_principal(hote_b)
    if not da or not db:
        return resultat
    if da == db:
        # Sous-domaines différents d'un même domaine principal (« celc.caisse-epargne.fr » /
        # « cecaz.caisse-epargne.fr ») : domaine proche, jamais un lien fort ni une contradiction.
        resultat.add("meme_domaine" if hote_a == hote_b else "domaine_proche")
        if hote_a == hote_b:
            resultat.add("meme_hote")
        return resultat
    resultat.add("domaines_differents")
    ra, rb = _radical(da), _radical(db)
    contenu = (len(ra) >= 4 and ra in rb) or (len(rb) >= 4 and rb in ra) or da in db or db in da
    if contenu or difflib.SequenceMatcher(None, da, db).ratio() >= SEUIL_DOMAINE_PROCHE:
        resultat.add("domaine_proche")
    return resultat


# --------------------------------------------------------------------------- #
# Téléphones, villes, SIREN
# --------------------------------------------------------------------------- #

def telephone(valeur):
    """Numéro au format national à 10 chiffres, ou "" (vide, factice ou étranger)."""
    d = chiffres(nettoyer(valeur))
    if len(d) != 10 or set(d) <= {"0"}:
        return ""
    return d


def ville(valeur):
    """« Lyon-9E-Arrondissement » -> « lyon », « ST JUST EN CHAUSSEE » -> « saint just en
    chaussee », « Laval Cedex » -> « laval »."""
    v = sans_accents_ni_ligatures(nettoyer(valeur)).lower()
    v = re.sub(r"\bcedex\b.*$", "", v)
    v = re.sub(r"[^a-z0-9]+", " ", v).strip()
    v = re.sub(r"\s+\d+\s*(er|e|eme|em)?(\s+arrondissement)?$", "", v)
    v = re.sub(r"\s+arrondissement$", "", v)
    v = re.sub(r"^\d{5}\s+", "", v)                      # code postal saisi dans la ville
    v = re.sub(r"\blez\b", "les", saint(v))           # Saint-André-lez-Lille
    return re.sub(r"\s+", " ", v).strip()


def villes_identiques(a, b):
    """Villes normalisées égales, ou l'une début de l'autre à une frontière de mot
    (« segre » et « segre en anjou bleu »)."""
    if not a or not b:
        return False
    return a == b or b.startswith(a + " ") or a.startswith(b + " ")


def siren_depuis(siren, siret):
    """SIREN de la fiche (champ SIREN de 9 chiffres, sinon déduit d'un SIRET de 14), ou ""."""
    s = re.sub(r"\D", "", nettoyer(siren))
    if len(s) == 9:
        return s
    t = re.sub(r"\D", "", nettoyer(siret))
    return t[:9] if len(t) == 14 else ""


# --------------------------------------------------------------------------- #
# Noms d'entreprise
# --------------------------------------------------------------------------- #

FORMES_JURIDIQUES = {"sarl", "eurl", "sas", "sasu", "sa", "snc", "sci", "association",
                     "fondation"}
TYPES_ETABLISSEMENT = ["groupe scolaire", "ogec", "ecole", "institution", "lycee", "college",
                       "ehpad"]
MOTS_VIDES = {"de", "du", "des", "la", "le", "les", "l", "d", "et"}


def nom_norm(nom):
    """Minuscules, sans accents, apostrophes unifiées, ponctuation et tirets -> espaces,
    « St » -> « Saint »."""
    texte = sans_accents_ni_ligatures(nettoyer(nom)).lower()
    texte = re.sub(r"[’‘`´]", "'", texte)
    texte = re.sub(r"[^a-z0-9]+", " ", texte)
    return saint(texte.strip())


def nom_sans_parentheses(nom):
    return nom_norm(re.sub(r"\([^)]*\)?", " ", nettoyer(nom)))


def _sans_mots(texte, retirer):
    return " ".join(m for m in texte.split() if m not in retirer)


def nom_equivalent(nom):
    """Nom sans parenthèses, forme juridique, type d'établissement ni mots vides."""
    texte = " " + nom_sans_parentheses(nom) + " "
    for expression in (t for t in TYPES_ETABLISSEMENT if " " in t):
        while " " + expression + " " in texte:
            texte = texte.replace(" " + expression + " ", " ")
    mots_types = {t for t in TYPES_ETABLISSEMENT if " " not in t}
    return _sans_mots(texte, FORMES_JURIDIQUES | mots_types | MOTS_VIDES)


def forme_ville(ville_norm):
    """Ville sous la forme des noms équivalents (sans mots vides) : « saint georges gardes »."""
    return _sans_mots(ville_norm, MOTS_VIDES)


def retirer_suite(texte, suite):
    """Retire la suite de mots « suite » de « texte » (mots entiers)."""
    if not suite:
        return texte
    return re.sub(r"\s+", " ", (" " + texte + " ").replace(" " + suite + " ", " ")).strip()


def nom_distinctif(nom_equiv, ville_norm):
    """Nom équivalent sans le nom de la ville de la fiche."""
    return retirer_suite(nom_equiv, forme_ville(ville_norm))


def nom_est_domaine(nom):
    """« abbayedesgardes.fr », « www.marmoutier.org » : fiche nommée par son domaine."""
    nom = nettoyer(nom).lower()
    nom = re.sub(r"^https?://", "", nom).replace("www.", "").rstrip("/")
    return ressemble_domaine(nom)


def vrai_nom(nom):
    return bool(nettoyer(nom)) and not nom_est_domaine(nom)


def contient_suite(a, b):
    """Vrai si les mots de l'un forment une suite de ceux de l'autre (noms différents)."""
    if not a or not b or a == b:
        return False
    return (" " + a + " ") in (" " + b + " ") or (" " + b + " ") in (" " + a + " ")


def distance_un(a, b):
    """Vrai si a et b sont à une distance de Levenshtein de 1 exactement."""
    if a == b or abs(len(a) - len(b)) > 1:
        return False
    if len(a) > len(b):
        a, b = b, a
    i = 0
    while i < len(a) and a[i] == b[i]:
        i += 1
    if len(a) == len(b):
        return a[i + 1:] == b[i + 1:]           # substitution
    return a[i:] == b[i + 1:]                    # insertion


# --------------------------------------------------------------------------- #
# Emails
# --------------------------------------------------------------------------- #

WEBMAILS = {"gmail.com", "yahoo.fr", "yahoo.com", "hotmail.fr", "hotmail.com", "outlook.fr",
            "outlook.com", "live.fr", "orange.fr", "wanadoo.fr", "free.fr", "sfr.fr",
            "laposte.net", "icloud.com", "me.com", "aol.com"}

LOCAUX_GENERIQUES = ["contact", "info", "infos", "accueil", "secretariat", "direction", "admin",
                     "administration", "compta", "comptabilite", "gestion", "mairie", "ecole",
                     "college", "lycee", "ogec", "bureau", "service", "services", "rh",
                     "recrutement", "commercial", "hello", "bonjour", "no-reply", "noreply"]


def email(valeur):
    """Minuscules, espaces retirés."""
    return re.sub(r"\s+", "", nettoyer(valeur)).lower()


def emails_liste(valeur):
    """« a@x.fr;b@y.fr » (hs_additional_emails) -> ["a@x.fr", "b@y.fr"]."""
    return [e for e in (email(x) for x in re.split(r"[;,\s]+", nettoyer(valeur))) if e]


def domaine_email(adresse):
    return adresse.rsplit("@", 1)[1] if "@" in adresse else ""


def local_email(adresse):
    return adresse.rsplit("@", 1)[0] if "@" in adresse else ""


def est_webmail(adresse):
    return domaine_email(adresse) in WEBMAILS


def est_generique(adresse):
    """contact@, info.ecole@, accueil-2@... : adresse de fonction, pas d'une personne."""
    local = sans_accents(local_email(adresse))
    return any(local == g or re.match(re.escape(g) + r"[._+-]", local) for g in LOCAUX_GENERIQUES)
