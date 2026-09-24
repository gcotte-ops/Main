"""Tests hors ligne : l'API de l'Annuaire est remplacée par des réponses simulées."""

import csv
import os
import tempfile
import unittest

import enrichissement_siren_siret as enr


def etab(siret, numero, type_voie, voie, cp, commune, siege=True, etat="A"):
    return {"siret": siret, "numero_voie": numero, "type_voie": type_voie,
            "libelle_voie": voie, "code_postal": cp, "libelle_commune": commune,
            "est_siege": siege, "etat_administratif": etat,
            "adresse": "{} {} {} {} {}".format(numero, type_voie, voie, cp, commune)}


RESULTATS = {
    # Le 1er résultat a le bon nom mais pas la bonne adresse : il faut prendre le 2e.
    "Soleil Energie": [
        {"siren": "111111111", "nom_complet": "SOLEIL ENERGIE", "etat_administratif": "A",
         "siege": etab("11111111100011", "3", "RUE", "DU PORT", "13002", "MARSEILLE")},
        {"siren": "222222222", "nom_complet": "SOLEIL ENERGIE (SE)", "etat_administratif": "A",
         "siege": etab("22222222200015", "8", "RUE", "DE LA REPUBLIQUE", "69002", "LYON"),
         "matching_etablissements": [
             etab("22222222200031", "45", "AV", "JEAN JAURES", "69007", "LYON", siege=False)]},
    ],
    "Boulangerie Martin": [
        {"siren": "333333333", "nom_complet": "BOULANGERIE DUPONT", "etat_administratif": "A",
         "siege": etab("33333333300010", "1", "PL", "DE LA MAIRIE", "44000", "NANTES")},
    ],
    "Ferme Sans Adresse": [
        {"siren": "444444444", "nom_complet": "FERME SANS ADRESSE SARL",
         "etat_administratif": "A",
         "siege": etab("44444444400012", "2", "CHE", "DES VIGNES", "33000", "BORDEAUX")},
    ],
    "555555555": [
        {"siren": "555555555", "nom_complet": "DEJA SIREN", "etat_administratif": "A",
         "siege": etab("55555555500019", "10", "BD", "HAUSSMANN", "75009", "PARIS")},
    ],
}


class FauxClient:
    def __init__(self):
        self.requetes = []

    def rechercher(self, texte, par_page=5, page=1):
        self.requetes.append(texte)
        # La vraie recherche est tolérante (accents, forme juridique) : on l'imite.
        index = {enr.normaliser_nom(k): v for k, v in RESULTATS.items()}
        return index.get(enr.normaliser_nom(texte), [])


class TestEnrichissement(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.entree = os.path.join(self.dossier, "entreprises.csv")
        with open(self.entree, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Record ID", "Nom de l'entreprise", "Secteur d'activité",
                        "Adresse postale", "Ville", "SIREN", "SIRET"])
            w.writerow(["1", "Soleil Énergie SAS", "Énergie", "45 avenue Jean-Jaurès",
                        "Lyon", "", ""])
            w.writerow(["2", "Boulangerie Martin", "Alimentaire", "1 place de la Mairie",
                        "Nantes", "", ""])
            w.writerow(["3", "Complet", "BTP", "1 rue X", "Paris", "999999999",
                        "99999999900011"])
            w.writerow(["4", "Ferme Sans Adresse", "Agriculture", "", "Bordeaux", "", ""])
            w.writerow(["5", "Déjà SIREN", "Services", "10 boulevard Haussmann", "Paris 9e",
                        "555 555 555", ""])
        self.sortie = os.path.join(self.dossier, "sortie.csv")
        self.rapport = os.path.join(self.dossier, "rapport.csv")
        self.client = FauxClient()

    def lancer(self, remplir_a_verifier=False):
        compteurs = enr.traiter(self.entree, self.sortie, self.rapport, {}, 5,
                                remplir_a_verifier, client=self.client)
        with open(self.sortie, encoding="utf-8-sig") as f:
            lignes = list(csv.reader(f, delimiter=";"))
        return compteurs, lignes

    def test_enrichissement(self):
        compteurs, lignes = self.lancer()
        # 2e résultat retenu, SIRET de l'établissement à l'adresse HubSpot (pas le siège).
        self.assertEqual(lignes[1][5:], ["222222222", "22222222200031"])
        # Nom différent : rien n'est écrit.
        self.assertEqual(lignes[2][5:], ["", ""])
        # Ligne complète : ignorée, sans appel à l'API.
        self.assertEqual(lignes[3][5:], ["999999999", "99999999900011"])
        self.assertNotIn("Complet", self.client.requetes)
        # Pas d'adresse : à vérifier, non écrit par défaut.
        self.assertEqual(lignes[4][5:], ["", ""])
        # SIREN déjà présent : recherche par SIREN, SIRET complété, SIREN conservé.
        self.assertEqual(lignes[5][5:], ["555 555 555", "55555555500019"])
        self.assertEqual(compteurs, {"TROUVÉ": 2, "À VÉRIFIER": 1, "NON TROUVÉ": 1,
                                     "DÉJÀ RENSEIGNÉ": 1})

    def test_remplir_a_verifier(self):
        _, lignes = self.lancer(remplir_a_verifier=True)
        self.assertEqual(lignes[4][5:], ["444444444", "44444444400012"])

    def test_normalisation(self):
        self.assertEqual(enr.normaliser_nom("Soleil Énergie SAS"), "soleil energie")
        self.assertEqual(enr.normaliser_ville("Paris 9e"), "paris")
        self.assertEqual(enr.normaliser_ville("St-Étienne Cedex 2"), "saint etienne")
        self.assertEqual(enr.decomposer_adresse("45 av. Jean-Jaurès 69007 Lyon"),
                         ("45", ["avenue", "jean", "jaures"], "69007"))


if __name__ == "__main__":
    unittest.main()
