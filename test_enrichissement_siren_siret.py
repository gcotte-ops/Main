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


def entreprise(siren, nom, siege, etat="A", matching=None):
    return {"siren": siren, "nom_complet": nom, "etat_administratif": etat, "siege": siege,
            "matching_etablissements": matching or []}


AUTRE = entreprise("999000000", "AUTRE SOCIETE",
                   etab("99900000000010", "1", "RUE", "NATIONALE", "59000", "LILLE"))

RESULTATS = {
    # 1er résultat : bon nom, mauvaise adresse -> il faut prendre le 2e, et le SIRET de
    # l'établissement secondaire situé à l'adresse HubSpot (pas celui du siège).
    "Soleil Energie": [
        entreprise("111111111", "SOLEIL ENERGIE",
                   etab("11111111100011", "3", "RUE", "DU PORT", "13002", "MARSEILLE")),
        entreprise("222222222", "SOLEIL ENERGIE (SE)",
                   etab("22222222200015", "8", "RUE", "DE LA REPUBLIQUE", "69002", "LYON"),
                   matching=[etab("22222222200031", "45", "AV", "JEAN JAURES", "69007",
                                  "LYON", siege=False)]),
    ],
    # La ville est répétée dans l'adresse HubSpot.
    "Communauté de communes - Pays de la Serre": [
        entreprise("200043602", "COMMUNAUTE DE COMMUNES DU PAYS DE LA SERRE",
                   etab("20004360200017", "1", "RUE", "DES TELLIERS", "02270",
                        "CRECY-SUR-SERRE")),
    ],
    # Nom seul : mauvaise adresse. « Nom + ville » : 1er résultat, active -> adresse corrigée
    # avec l'établissement situé dans la ville du CSV.
    "Demenageurs Bretons": [
        entreprise("333333333", "DEMENAGEURS BRETONS",
                   etab("33333333300010", "12", "AV", "DES CHAMPS ELYSEES", "75008", "PARIS")),
    ],
    "Demenageurs Bretons Rennes": [
        entreprise("333333333", "DEMENAGEURS BRETONS",
                   etab("33333333300010", "12", "AV", "DES CHAMPS ELYSEES", "75008", "PARIS"),
                   matching=[etab("33333333300028", "8", "BD", "DE LA LIBERTE", "35000",
                                  "RENNES", siege=False)]),
    ],
    # Nom seul : rien. « Nom + ville » : trouvée à la bonne adresse.
    "Atelier Bois Nantes": [
        entreprise("777777777", "ATELIER BOIS",
                   etab("77777777700015", "3", "QUA", "DE LA FOSSE", "44000", "NANTES")),
    ],
    # Nom trouvé mais à une autre adresse, et pas en 1er résultat avec « nom + ville » :
    # l'adresse ne doit PAS être modifiée.
    "Garage Dupuis": [
        entreprise("888888888", "GARAGE DUPUIS",
                   etab("88888888800011", "40", "RUE", "SOLFERINO", "59000", "LILLE")),
    ],
    "Garage Dupuis Lille": [
        AUTRE,
        entreprise("888888888", "GARAGE DUPUIS",
                   etab("88888888800011", "40", "RUE", "SOLFERINO", "59000", "LILLE")),
    ],
    # Entreprise cessée.
    "Vieille Usine": [
        entreprise("444444444", "VIEILLE USINE",
                   etab("44444444400012", "2", "CHE", "DES VIGNES", "33000", "BORDEAUX",
                        etat="F"), etat="C"),
    ],
    # Nom différent -> rien de fiable.
    "Boulangerie Martin": [
        entreprise("555555555", "BOULANGERIE DUPONT",
                   etab("55555555500010", "1", "PL", "DE LA MAIRIE", "44000", "NANTES")),
    ],
    # SIREN déjà connu : recherche par SIREN.
    "666666666": [
        entreprise("666666666", "DEJA SIREN",
                   etab("66666666600019", "10", "BD", "HAUSSMANN", "75009", "PARIS")),
    ],
    # SIRET déjà connu : recherche par SIRET.
    "12312312300016": [
        entreprise("123123123", "SIRET BONNE ADRESSE",
                   etab("12312312300016", "7", "RUE", "DE LA GARE", "38000", "GRENOBLE")),
    ],
    "32132132100014": [
        entreprise("321321321", "SIRET AUTRE ADRESSE",
                   etab("32132132100014", "9", "AV", "FOCH", "67000", "STRASBOURG")),
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


ENTETES = ["ID de fiche d'informations", "Nom de l'entreprise", "Secteur d'activité",
           "Pays/Région", "Ville", "Adresse postale", "SIREN", "SIRET"]
LIGNES = [
    ["1", "Soleil Énergie SAS", "Énergie", "France", "Lyon", "45 avenue Jean-Jaurès", "", ""],
    ["2", "Communauté de communes - Pays de la Serre", "Public", "France", "Crecy Sur Serre",
     "1 rue des Telliers  Crécy-sur-Serre", "", ""],
    ["3", "Déménageurs Bretons", "Transport", "France", "Rennes", "4 rue de Brest", "", ""],
    ["4", "Atelier Bois", "Artisanat", "", "Nantes", "3 quai de la Fosse", "", ""],
    ["5", "Vieille Usine", "Industrie", "France", "Bordeaux", "2 chemin des Vignes", "", ""],
    ["6", "Boulangerie Martin", "Alimentaire", "France", "Nantes", "1 place de la Mairie",
     "", ""],
    ["7", "Complet", "BTP", "France", "Paris", "1 rue X", "999999999", "99999999900011"],
    ["8", "Déjà SIREN", "Services", "FRANCE", "Paris 9e", "10 boulevard Haussmann",
     "666 666 666", ""],
    ["9", "Acme Inc", "Tech", "United States", "Boston", "1 Main Street", "", ""],
    ["10", "Garage Dupuis", "Auto", "France", "Lille", "2 rue Faidherbe", "", ""],
    ["11", "Nom sans importance", "BTP", "France", "Grenoble", "7 rue de la Gare", "",
     "12312312300016"],
    ["12", "Nom sans importance", "BTP", "France", "Metz", "1 place d'Armes", "",
     "32132132100014"],
    ["13", "Incohérente", "BTP", "France", "Paris", "1 rue Y", "111222333", "44455566600017"],
]


class TestEnrichissement(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.entree = os.path.join(self.dossier, "entreprises.csv")
        with open(self.entree, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(ENTETES)
            w.writerows(LIGNES)
        self.sortie = os.path.join(self.dossier, "sortie.csv")
        self.rapport = os.path.join(self.dossier, "rapport.csv")
        self.client = FauxClient()

    def lancer(self, **options):
        compteurs = enr.traiter(self.entree, self.sortie, self.rapport, {}, 5, False,
                                client=self.client, **options)
        with open(self.sortie, encoding="utf-8-sig") as f:
            lignes = list(csv.reader(f))
        with open(self.rapport, encoding="utf-8-sig") as f:
            rapport = {r[0]: r for r in list(csv.reader(f))[1:]}
        return compteurs, lignes, rapport

    def test_arbre_de_decision(self):
        compteurs, lignes, rapport = self.lancer()
        par_id = {l[0]: l for l in lignes[1:]}
        adresse = lambda i: par_id[i][4:6]
        # Bonne adresse (2e résultat, établissement secondaire).
        self.assertEqual(par_id["1"][6:], ["222222222", "22222222200031"])
        # Ville répétée dans l'adresse HubSpot.
        self.assertEqual(par_id["2"][6:], ["200043602", "20004360200017"])
        self.assertEqual(adresse("2"), ["Crecy Sur Serre", "1 rue des Telliers  Crécy-sur-Serre"])
        # Trouvée du 1er coup avec « nom + ville », autre adresse -> adresse corrigée.
        self.assertEqual(par_id["3"][4:], ["Rennes", "8 Boulevard de la Liberte",
                                           "333333333", "33333333300028"])
        self.assertEqual(rapport["3"][4], "ADRESSE CORRIGÉE")
        # Trouvée avec « nom + ville » à la bonne adresse.
        self.assertEqual(par_id["4"][6:], ["777777777", "77777777700015"])
        self.assertIn("Atelier Bois Nantes", self.client.requetes)
        # Entreprise cessée -> fiche à supprimer.
        self.assertEqual(rapport["5"][4], "FERMÉE")
        # Rien de fiable -> recherche Internet, rien d'écrit.
        self.assertEqual(par_id["6"][6:], ["", ""])
        self.assertEqual(rapport["6"][4], "RECHERCHE INTERNET")
        # Ligne complète : ignorée, sans appel à l'API.
        self.assertEqual(par_id["7"][6:], ["999999999", "99999999900011"])
        self.assertNotIn("Complet", self.client.requetes)
        # SIREN déjà présent : conservé tel quel, SIRET complété.
        self.assertEqual(par_id["8"][6:], ["666 666 666", "66666666600019"])
        # Hors France : non recherchée.
        self.assertEqual(par_id["9"][6:], ["", ""])
        # Pas trouvée du 1er coup avec « nom + ville » : adresse NON modifiée, rien d'écrit.
        self.assertEqual(par_id["10"][4:], ["Lille", "2 rue Faidherbe", "", ""])
        self.assertEqual(rapport["10"][4], "RECHERCHE INTERNET")
        # SIRET connu : recherche par SIRET (jamais par le nom), SIREN écrit.
        self.assertEqual(par_id["11"][6:], ["123123123", "12312312300016"])
        self.assertEqual(rapport["11"][4], "TROUVÉ")
        self.assertNotIn("Nom sans importance", self.client.requetes)
        # SIRET connu, adresse différente : SIREN écrit, adresse laissée telle quelle.
        self.assertEqual(par_id["12"][4:], ["Metz", "1 place d'Armes", "321321321",
                                            "32132132100014"])
        self.assertEqual(rapport["12"][4], "ADRESSE À VÉRIFIER")
        # SIREN et SIRET incohérents : signalés, non modifiés.
        self.assertEqual(par_id["13"][6:], ["111222333", "44455566600017"])
        self.assertEqual(rapport["13"][4], "INCOHÉRENT")
        self.assertEqual(compteurs, {"TROUVÉ": 5, "ADRESSE CORRIGÉE": 1,
                                     "ADRESSE À VÉRIFIER": 1, "FERMÉE": 1, "À VÉRIFIER": 0,
                                     "RECHERCHE INTERNET": 2, "HORS FRANCE": 1,
                                     "DÉJÀ RENSEIGNÉ": 1, "INCOHÉRENT": 1})

    def test_ids_et_autres_colonnes_inchanges(self):
        _, lignes, _ = self.lancer(corriger_adresse=False)
        self.assertEqual([l[:6] for l in lignes[1:]], [l[:6] for l in LIGNES])

    def test_normalisation(self):
        self.assertEqual(enr.normaliser_nom("Soleil Énergie SAS"), "soleil energie")
        self.assertEqual(enr.normaliser_ville("Paris 9e"), "paris")
        self.assertEqual(enr.normaliser_ville("St-Étienne Cedex 2"), "saint etienne")
        self.assertEqual(enr.decomposer_adresse("45 av. Jean-Jaurès 69007 Lyon"),
                         ("45", ["avenue", "jean", "jaures"], "69007"))
        self.assertEqual(enr.retirer_ville("1 rue des Telliers  Crécy-sur-Serre",
                                           "Crecy Sur Serre"), "1 rue des Telliers")
        self.assertEqual(enr.mettre_en_forme("12 AVENUE DES CHAMPS-ELYSEES"),
                         "12 Avenue des Champs-Elysees")


if __name__ == "__main__":
    unittest.main()
