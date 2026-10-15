#!/usr/bin/env python3
"""
Outils de la routine hebdomadaire de dédoublonnage HubSpot (voir DEDOUBLONNAGE_RECURRENT.md).

Les connecteurs Google Drive et Google Sheets répondent en JSON ; quand la réponse est longue,
Claude Code l'enregistre dans un fichier. Ces commandes transforment ce JSON (fichier enregistré,
ou réponse courte recopiée dans un fichier) en fichiers utilisables par les scripts :

  python outils_routine.py fichier REPONSE.json SORTIE        # Drive (download_file_content) :
                                                              # contenu base64 -> fichier
  python outils_routine.py valeurs REPONSE.json SORTIE.csv    # Sheets (get_values) : valeurs ->
                                                              # CSV « ; » (mémoire, GT 3.0)
  python outils_routine.py lignes DECISIONS.csv               # CSV écrit par --memoriser ->
                                                              # lignes JSON à ajouter à la feuille

Aucune dépendance externe : uniquement la bibliothèque standard Python (3.8+).
"""

import argparse
import base64
import csv
import json
import sys
import zipfile


def charger(chemin):
    """Réponse JSON d'un connecteur, telle qu'enregistrée par Claude Code (objet JSON, ou liste
    de blocs [{"type": "text", "text": "<json>"}])."""
    with open(chemin, encoding="utf-8") as f:
        donnees = json.load(f)
    if isinstance(donnees, list):
        textes = [b.get("text", "") for b in donnees if isinstance(b, dict)]
        donnees = json.loads("".join(textes))
    if isinstance(donnees, dict) and "result" in donnees and isinstance(donnees["result"], str):
        donnees = json.loads(donnees["result"])
    return donnees


def fichier(reponse, sortie):
    """Contenu base64 d'un fichier Drive écrit sur le disque ; un classeur .xlsx est vérifié
    (une copie abîmée est refusée plutôt que lue de travers)."""
    donnees = charger(reponse)
    contenu = base64.b64decode(donnees["content"])
    with open(sortie, "wb") as f:
        f.write(contenu)
    if sortie.lower().endswith(".xlsx"):
        with zipfile.ZipFile(sortie) as z:
            abime = z.testzip()
        if abime:
            raise SystemExit("classeur abîmé ({}) : ne pas l'utiliser".format(abime))
    return donnees.get("title", "")


def valeurs(reponse, sortie):
    """Valeurs d'une plage Google Sheets -> CSV « ; » (1re ligne = en-têtes)."""
    lignes = charger(reponse).get("values", [])
    largeur = max((len(l) for l in lignes), default=0)
    with open(sortie, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        for l in lignes:
            w.writerow([str(v) for v in l] + [""] * (largeur - len(l)))
    return max(len(lignes) - 1, 0)


def lignes(decisions):
    """Lignes d'un CSV écrit par --memoriser (sans l'en-tête), en JSON, pour
    sheets_append_values."""
    with open(decisions, encoding="utf-8-sig", newline="") as f:
        rangs = list(csv.reader(f, delimiter=";"))
    return rangs[1:]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Outils de la routine de dédoublonnage.")
    sous = parser.add_subparsers(dest="commande", required=True)
    p = sous.add_parser("fichier", help="réponse Drive -> fichier")
    p.add_argument("reponse")
    p.add_argument("sortie")
    p = sous.add_parser("valeurs", help="réponse Sheets -> CSV")
    p.add_argument("reponse")
    p.add_argument("sortie")
    p = sous.add_parser("lignes", help="CSV de décisions -> lignes JSON")
    p.add_argument("decisions")
    args = parser.parse_args(argv)
    if args.commande == "fichier":
        print("{} écrit ({})".format(args.sortie, fichier(args.reponse, args.sortie)))
    elif args.commande == "valeurs":
        print("{} écrit : {} lignes".format(args.sortie, valeurs(args.reponse, args.sortie)))
    else:
        print(json.dumps(lignes(args.decisions), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
