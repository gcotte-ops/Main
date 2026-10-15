"""
Règle des familles : ne jamais fusionner deux entreprises dont les noms contiennent chacun un
qualificatif appartenant à des champs lexicaux différents (OGEC / Mairie, Foncière /
Association...).

Deux dimensions, évaluées séparément :
  Activité          enseignement, collectivité, État, médico-social, religieux, immobilier...
  Nature juridique  asso_fondation, societe, public (association et fondation : même nature).

Pour chaque nom : les familles d'activité des marqueurs trouvés, et les natures explicites
(marqueurs de nature) ; à défaut seulement, les natures implicites des marqueurs d'activité
(« Association immobilière » est asso_fondation, pas societe).

Une paire est incompatible si, pour au moins une dimension, les deux ensembles sont non vides
et n'ont aucun élément commun. Un nom sans marqueur dans une dimension ne bloque pas.

Les marqueurs sont lus dans lexique_familles.csv (séparateur « ; », colonnes dimension, famille,
marqueur, position, nature_implicite), que l'équipe peut enrichir sans toucher au code. Ils sont
cherchés sur le nom normalisé, par mot ou expression entière, pluriel toléré (s ou x final) ;
position « debut » : reconnu seulement en tête de nom. Les mots ambigus (institut, résidence,
maison, groupe, centre, communauté, MAS) ne sont jamais marqueurs seuls.
"""

import csv
import os
import sys

from normalisation import nom_norm

LEXIQUE_DEFAUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lexique_familles.csv")
DIMENSIONS = ("activite", "nature")
MOTS_AMBIGUS = {"institut", "residence", "maison", "groupe", "centre", "communaute", "mas"}


def singulier(mot):
    """Pluriel toléré : « ecoles » -> « ecole », « hopitaux » -> « hopitau »."""
    return mot[:-1] if len(mot) >= 4 and mot[-1] in "sx" else mot


class Marqueur:

    def __init__(self, dimension, famille, marqueur, debut=False, nature_implicite=""):
        self.dimension = dimension
        self.famille = famille
        self.marqueur = marqueur
        self.mots = tuple(singulier(m) for m in nom_norm(marqueur).split())
        self.debut = debut
        self.nature_implicite = nature_implicite

    def __repr__(self):
        return "Marqueur({} {} {!r})".format(self.dimension, self.famille, self.marqueur)

    def present(self, mots):
        n = len(self.mots)
        if not n or n > len(mots):
            return False
        positions = [0] if self.debut else range(len(mots) - n + 1)
        return any(tuple(mots[i:i + n]) == self.mots for i in positions)


def charger_lexique(chemin=LEXIQUE_DEFAUT, avertir=True):
    """Marqueurs du lexique ; les lignes invalides sont ignorées avec un avertissement."""
    marqueurs = []
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        lignes = [l for l in f.read().splitlines() if l.strip() and not l.startswith("#")]
    for n, ligne in enumerate(csv.DictReader(lignes, delimiter=";"), 2):
        ligne = {(k or "").strip().lower(): (v or "").strip() for k, v in ligne.items()}
        dimension = nom_norm(ligne.get("dimension")).replace(" ", "_")
        famille = ligne.get("famille", "").strip()
        marqueur = nom_norm(ligne.get("marqueur"))
        probleme = ""
        if dimension not in DIMENSIONS:
            probleme = "dimension « {} » inconnue".format(ligne.get("dimension"))
        elif not famille or not marqueur:
            probleme = "famille ou marqueur vide"
        elif marqueur in MOTS_AMBIGUS:
            probleme = "« {} » est ambigu : jamais marqueur seul".format(marqueur)
        if probleme:
            if avertir:
                print("  ! {} ligne {} ignorée : {}".format(os.path.basename(chemin), n, probleme),
                      file=sys.stderr)
            continue
        marqueurs.append(Marqueur(dimension, famille, marqueur,
                                  debut=ligne.get("position", "").lower() == "debut",
                                  nature_implicite=ligne.get("nature_implicite", "")))
    return marqueurs


_LEXIQUE = None


def lexique():
    """Lexique par défaut (lu une seule fois)."""
    global _LEXIQUE
    if _LEXIQUE is None:
        _LEXIQUE = charger_lexique()
    return _LEXIQUE


def etiquettes(nom, marqueurs=None):
    """(activités, natures) du nom."""
    mots = [singulier(m) for m in nom_norm(nom).split()]
    trouves = [m for m in (marqueurs if marqueurs is not None else lexique()) if m.present(mots)]
    activites = {m.famille for m in trouves if m.dimension == "activite"}
    natures = {m.famille for m in trouves if m.dimension == "nature"}
    if not natures:
        natures = {m.nature_implicite for m in trouves
                   if m.dimension == "activite" and m.nature_implicite}
    return activites, natures


def incompatibilite(nom_a, nom_b, marqueurs=None):
    """Motif d'incompatibilité (« activité : enseignement / collectivite »), ou "" si les deux
    noms sont compatibles."""
    return comparer_etiquettes(etiquettes(nom_a, marqueurs), etiquettes(nom_b, marqueurs))


def comparer_etiquettes(etiquettes_a, etiquettes_b):
    """Même règle à partir d'étiquettes déjà calculées (voir etiquettes)."""
    activites_a, natures_a = etiquettes_a
    activites_b, natures_b = etiquettes_b
    motifs = []
    for libelle, a, b in (("activité", activites_a, activites_b),
                          ("nature", natures_a, natures_b)):
        if a and b and not a & b:
            motifs.append("{} : {} / {}".format(libelle, ", ".join(sorted(a)), ", ".join(sorted(b))))
    return " ; ".join(motifs)


def compatibles(nom_a, nom_b, marqueurs=None):
    return not incompatibilite(nom_a, nom_b, marqueurs)
