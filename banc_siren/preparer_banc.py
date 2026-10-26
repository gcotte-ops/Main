#!/usr/bin/env python3
"""
Prépare un banc de test à partir d'un export HubSpot d'entreprises dont le SIREN est connu :
les lignes [debut, debut + n[ sont copiées avec SIREN et SIRET vidés (test_<n>.csv), les SIREN
d'origine mis de côté sans être affichés (reference_<n>.csv).

  python banc_siren/preparer_banc.py export.csv --debut 300 -n 2000 --dossier banc_siren/
  python banc_siren/preparer_banc.py export.csv -n 300 --hubspot     # + « Type de décideur »

--hubspot lit le « Type de décideur » de chaque fiche dans HubSpot (lecture seule, variable
HUBSPOT_TOKEN, droit crm.objects.companies.read) si l'export ne contient pas cette colonne.
Ne jamais versionner les fichiers produits : ils contiennent des données du CRM.
"""
import argparse
import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import enrichissement_siren_siret as enr  # noqa: E402

COLONNE_DECIDEUR = "Type de décideur"


def decideurs_hubspot(ids):
    """{id: type de décideur} lu par lots de 100 (API HubSpot, lecture seule)."""
    connexion = enr.Connexion("api.hubapi.com", timeout=30)
    resultat = {}
    for k in range(0, len(ids), 100):
        corps = json.dumps({"properties": ["type_de_decideur"],
                            "inputs": [{"id": i} for i in ids[k:k + 100]]})
        for tentative in range(20):
            try:
                if connexion.c is None:
                    connexion.c = connexion._ouvrir()
                connexion.c.request("POST", "/crm/v3/objects/companies/batch/read", body=corps,
                                    headers={"Authorization": "Bearer " + os.environ["HUBSPOT_TOKEN"],
                                             "Content-Type": "application/json"})
                r = connexion.c.getresponse()
                donnees = json.loads(r.read() or b"{}")
            except OSError:
                connexion.fermer()
                time.sleep(1)
                continue
            if r.status == 429 or r.status >= 500:
                time.sleep(2)
                continue
            if r.status not in (200, 207):
                raise SystemExit("HubSpot HTTP {} : {}".format(r.status, str(donnees)[:300]))
            break
        for objet in donnees.get("results", []):
            resultat[objet["id"]] = (objet.get("properties") or {}).get("type_de_decideur") or ""
    return resultat


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("export", help="export HubSpot d'entreprises dont le SIREN est connu")
    parser.add_argument("--debut", type=int, default=0, help="première ligne (0 = la 1re)")
    parser.add_argument("-n", type=int, default=300, help="nombre de lignes (défaut 300)")
    parser.add_argument("--dossier", default=".", help="dossier des fichiers produits")
    parser.add_argument("--hubspot", action="store_true",
                        help="lire le « Type de décideur » dans HubSpot")
    args = parser.parse_args()

    entetes, lignes, separateur, _ = enr.lire_csv(args.export)
    lignes = lignes[args.debut:args.debut + args.n]
    colonnes = enr.detecter_colonnes(entetes, {})
    i_id, i_siren, i_siret = colonnes["id"], colonnes["siren"], colonnes["siret"]
    if args.hubspot and "decideur" not in colonnes:
        decideur = decideurs_hubspot([l[i_id] for l in lignes])
        entetes = entetes + [COLONNE_DECIDEUR]
        lignes = [l + [decideur.get(l[i_id], "")] for l in lignes]

    os.makedirs(args.dossier, exist_ok=True)
    reference = os.path.join(args.dossier, "reference_{}.csv".format(args.n))
    test = os.path.join(args.dossier, "test_{}.csv".format(args.n))
    enr.ecrire_csv(reference, ["ID", "SIREN référence"],
                   [[l[i_id], l[i_siren]] for l in lignes], ",")
    for l in lignes:
        l[i_siren] = l[i_siret] = ""
    enr.ecrire_csv(test, entetes, lignes, separateur)
    print("{} lignes ({} à {} de l'export) : {} et {}".format(
        len(lignes), args.debut + 1, args.debut + len(lignes), test, reference))


if __name__ == "__main__":
    main()
