#!/usr/bin/env python3
"""
Mesure un passage du script sur un banc : SIREN écrits, justes, faux, par statut, par profil de
fiche et par type de décideur ; écarts détaillés dans ecarts_<test>.csv.

  python enrichissement_siren_siret.py banc_siren/test_2000.csv --cache banc_siren/cache_api
  python banc_siren/analyser_banc.py banc_siren/test_2000.csv banc_siren/reference_2000.csv

Une référence à clé de contrôle fausse est comptée à part (elle ne peut pas être juste). Les
cas « À ARBITRER » (SIREN proposé dans le rapport, non écrit) sont mesurés sur le SIREN proposé.
--noms ajoute aux écarts le nom des deux entreprises (appels à l'API, avec le cache s'il existe).
"""
import argparse
import collections
import csv
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import enrichissement_siren_siret as enr  # noqa: E402


def lire(chemin):
    entetes, lignes, _, _ = enr.lire_csv(chemin)
    return [dict(zip(entetes, l)) for l in lignes]


def siren(valeur):
    chiffres = re.sub(r"\D", "", valeur or "")
    return chiffres if len(chiffres) == 9 else ""


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("test", help="CSV de test (SIREN vidés) passé au script")
    parser.add_argument("reference", help="CSV de référence (ID, SIREN référence)")
    parser.add_argument("--complete", help="CSV complété (défaut : <test>_complete.csv)")
    parser.add_argument("--rapport", help="rapport (défaut : <test>_rapport.csv)")
    parser.add_argument("--noms", action="store_true", help="noms des entreprises des écarts")
    parser.add_argument("--cache", help="cache de l'API pour --noms")
    args = parser.parse_args()
    base = os.path.splitext(args.test)[0]
    test = {l["ID de fiche d'informations"]: l for l in lire(args.test)}
    ref = {l["ID"]: siren(l["SIREN référence"]) for l in lire(args.reference)}
    complete = {l["ID de fiche d'informations"]: l for l in lire(args.complete or base + "_complete.csv")}
    rapport = {l["ID HubSpot"]: l for l in lire(args.rapport or base + "_rapport.csv")}

    def resultat(i):
        """(SIREN écrit ou proposé, catégorie de statut) ; catégorie None si rien."""
        ecrit = siren(complete[i]["SIREN"])
        if ecrit:
            return ecrit, complete[i].get(enr.COLONNE_STATUT) or "?"
        r = rapport.get(i, {})
        if r.get("Statut") == "À ARBITRER" and siren(r.get("SIREN trouvé")):
            return siren(r["SIREN trouvé"]), "À arbitrer (non écrit)"
        return "", None

    def etat(i):
        s, _ = resultat(i)
        if not s:
            return "vide"
        if not enr.cle_valide(ref[i]):
            return "réf. invalide"
        return "juste" if s == ref[i] else "faux"

    def ligne(titre, ids, ecrits_seulement=False):
        """ecrits_seulement : les SIREN proposés mais non écrits (À arbitrer) sont ignorés."""
        c = collections.Counter("vide" if ecrits_seulement and resultat(i)[1] == "À arbitrer (non écrit)"
                                else etat(i) for i in ids)
        ecrits = sum(1 for i in ids if resultat(i)[1] and resultat(i)[1] != "À arbitrer (non écrit)")
        n = c["juste"] + c["faux"]
        print("  {:<36} {:>5} lignes | écrits {:>5} | justes {:>5} | faux {:>4} | réf. inval. {:>3} "
              "| précision {}".format(titre, len(ids), ecrits, c["juste"], c["faux"],
                                     c["réf. invalide"], "{:.1f} %".format(100 * c["juste"] / n) if n else "-"))

    ids = list(ref)
    print("=== {} : {} lignes ===".format(args.test, len(ids)))
    ligne("Toutes les lignes (SIREN écrits)", ids, ecrits_seulement=True)
    print("\nPar statut enrichissement :")
    for cat in ("Trouvé", "À vérifier", "Fermée", "À arbitrer (non écrit)"):
        ligne(cat, [i for i in ids if resultat(i)[1] == cat])
    print("\nPar statut du rapport :")
    for st, nb in collections.Counter(rapport.get(i, {}).get("Statut", "?") for i in ids).most_common():
        ligne(st, [i for i in ids if rapport.get(i, {}).get("Statut") == st])

    def profil(i):
        t = test[i]
        adresse, ville = t.get("Adresse postale", "").strip(), t.get("Ville", "").strip()
        return "adresse" if adresse else ("ville seule" if ville else "ni adresse ni ville")
    print("\nPar profil de fiche (SIREN écrits) :")
    for p in ("adresse", "ville seule", "ni adresse ni ville"):
        ligne(p, [i for i in ids if profil(i) == p], ecrits_seulement=True)
    if any("Type de décideur" in t for t in test.values()):
        print("\nPar type de décideur (SIREN écrits) :")
        for d in ("Centralisé", "Décentralisé", "Ne sais pas encore", ""):
            ligne(d or "(vide)", [i for i in ids if test[i].get("Type de décideur", "") == d],
                  ecrits_seulement=True)

    client = enr.ClientAnnuaire(cache=args.cache) if args.noms else None
    noms = {}

    def nom(s):
        if not client or not s:
            return ""
        if s not in noms:
            r = [x for x in client.rechercher(s, par_page=1) if x.get("siren") == s]
            noms[s] = (r[0].get("nom_complet") or "") if r else "(introuvable)"
        return noms[s]

    sortie = base + "_ecarts.csv"
    with open(sortie, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["ID", "Nom HubSpot", "Ville", "Statut", "Catégorie", "SIREN écrit ou proposé",
                    "Nom Annuaire", "SIREN référence", "Nom référence", "Référence valide", "Détail"])
        for i in ids:
            if etat(i) in ("faux", "réf. invalide"):
                s, cat = resultat(i)
                r = rapport.get(i, {})
                w.writerow([i, test[i].get("Nom de l'entreprise", ""), test[i].get("Ville", ""),
                            r.get("Statut", ""), cat, s, nom(s), ref[i], nom(ref[i]),
                            "oui" if enr.cle_valide(ref[i]) else "non", r.get("Détail", "")[:250]])
    print("\nÉcarts : " + sortie)


if __name__ == "__main__":
    main()
