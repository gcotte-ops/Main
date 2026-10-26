"""Tests hors ligne : l'API de l'Annuaire est remplacée par des réponses simulées."""

import csv
import json
import os
import tempfile
import unittest
from unittest import mock

import enrichissement_siren_siret as enr


def cle(debut):
    """Complète `debut` (8 ou 13 chiffres) avec sa clé de contrôle : numéros de test valides."""
    return next(debut + d for d in "0123456789" if enr.cle_valide(debut + d))


def mauvaise_cle(numero):
    return numero[:-1] + str((int(numero[-1]) + 1) % 10)


# SIREN / SIRET de test, tous à clé valide.
N = {}
for nom, debut in [("soleil_1", "11111111"), ("soleil_2", "22222222"), ("cc", "20004360"),
                   ("demenageurs", "33333333"), ("atelier", "77777777"), ("garage", "88888888"),
                   ("usine", "44444444"), ("dupont", "55555555"), ("deja", "66666666"),
                   ("siret_ok", "12312312"), ("siret_autre", "32132132"), ("complet", "98765432"),
                   ("incoherent", "11122233"), ("autre_siret", "44455566"), ("alpha", "51515151"),
                   ("alpha_holding", "52525252"), ("zephyr", "53535353"), ("double_1", "54545454"),
                   ("double_2", "56565656"), ("commune", "21690000"), ("autre", "99900000"),
                   ("marguerite", "78111111"), ("joseph_1", "78222222"), ("joseph_2", "78333333"),
                   ("notre_dame", "78444444"), ("anne", "78555555"), ("louis", "78666666"),
                   ("inconnue", "99988877")]:
    N[nom] = cle(debut)


def siret(nom, numero="0001"):
    return cle(N[nom] + numero)


def etab(siret_etab, numero, type_voie, voie, cp, commune, siege=True, etat="A"):
    return {"siret": siret_etab, "numero_voie": numero, "type_voie": type_voie,
            "libelle_voie": voie, "code_postal": cp, "libelle_commune": commune,
            "est_siege": siege, "etat_administratif": etat,
            "adresse": "{} {} {} {} {}".format(numero, type_voie, voie, cp, commune)}


def entreprise(nom_cle, nom, siege, etat="A", matching=None, **autres):
    e = {"siren": N[nom_cle], "nom_complet": nom, "etat_administratif": etat, "siege": siege,
         "matching_etablissements": matching or []}
    e.update(autres)
    return e


AUTRE = entreprise("autre", "AUTRE SOCIETE",
                   etab(siret("autre"), "1", "RUE", "NATIONALE", "59000", "LILLE"))

# Clé = texte recherché (comparé sans accents ni forme juridique) ; « @dép » = recherche filtrée
# sur ce département.
RESULTATS = {
    # 1er résultat : bon nom, mauvaise adresse -> il faut prendre le 2e, et le SIRET de
    # l'établissement secondaire situé à l'adresse HubSpot (pas celui du siège).
    "Soleil Energie": [
        entreprise("soleil_1", "SOLEIL ENERGIE",
                   etab(siret("soleil_1"), "3", "RUE", "DU PORT", "13002", "MARSEILLE")),
        entreprise("soleil_2", "SOLEIL ENERGIE (SE)",
                   etab(siret("soleil_2"), "8", "RUE", "DE LA REPUBLIQUE", "69002", "LYON"),
                   matching=[etab(siret("soleil_2", "0003"), "45", "AV", "JEAN JAURES", "69007",
                                  "LYON", siege=False)]),
    ],
    # La ville est répétée dans l'adresse HubSpot.
    "Communauté de communes - Pays de la Serre": [
        entreprise("cc", "COMMUNAUTE DE COMMUNES DU PAYS DE LA SERRE",
                   etab(siret("cc"), "1", "RUE", "DES TELLIERS", "02270", "CRECY-SUR-SERRE")),
    ],
    # Nom seul : siège à Paris, rien à Rennes -> 2e recherche filtrée sur le département de
    # Rennes : établissement à Rennes, autre adresse -> adresse corrigée.
    "Demenageurs Bretons": [
        entreprise("demenageurs", "DEMENAGEURS BRETONS",
                   etab(siret("demenageurs"), "12", "AV", "DES CHAMPS ELYSEES", "75008", "PARIS")),
    ],
    "Demenageurs Bretons @35": [
        entreprise("demenageurs", "DEMENAGEURS BRETONS",
                   etab(siret("demenageurs"), "12", "AV", "DES CHAMPS ELYSEES", "75008", "PARIS"),
                   matching=[etab(siret("demenageurs", "0002"), "8", "BD", "DE LA LIBERTE",
                                  "35000", "RENNES", siege=False)]),
    ],
    # Nom seul : trouvée à la bonne adresse (la ville n'est jamais ajoutée à la requête).
    "Atelier Bois": [
        entreprise("atelier", "ATELIER BOIS",
                   etab(siret("atelier"), "3", "QUA", "DE LA FOSSE", "44000", "NANTES")),
    ],
    # Seule entreprise de ce nom dans la ville, à une autre adresse -> adresse corrigée.
    "Garage Dupuis": [
        AUTRE,
        entreprise("garage", "GARAGE DUPUIS",
                   etab(siret("garage"), "40", "RUE", "SOLFERINO", "59000", "LILLE")),
    ],
    # Société cessée trouvée par le nom : à arbitrer, rien d'écrit.
    "Vieille Usine": [
        entreprise("usine", "VIEILLE USINE",
                   etab(siret("usine"), "2", "CHE", "DES VIGNES", "33000", "BORDEAUX", etat="F"),
                   etat="C"),
    ],
    # Nom différent -> rien de fiable.
    "Boulangerie Martin": [
        entreprise("dupont", "BOULANGERIE DUPONT",
                   etab(siret("dupont"), "1", "PL", "DE LA MAIRIE", "44000", "NANTES")),
    ],
    # SIREN déjà connu : recherche par SIREN.
    N["deja"]: [
        entreprise("deja", "DEJA SIREN",
                   etab(siret("deja"), "10", "BD", "HAUSSMANN", "75009", "PARIS")),
    ],
    # SIRET déjà connu : recherche par SIRET.
    siret("siret_ok"): [
        entreprise("siret_ok", "SIRET BONNE ADRESSE",
                   etab(siret("siret_ok"), "7", "RUE", "DE LA GARE", "38000", "GRENOBLE")),
    ],
    siret("siret_autre"): [
        entreprise("siret_autre", "SIRET AUTRE ADRESSE",
                   etab(siret("siret_autre"), "9", "AV", "FOCH", "67000", "STRASBOURG")),
    ],
    # Holding et filiale du même nom à la même adresse : départage selon le type de décideur.
    "Groupe Alpha": [
        entreprise("alpha", "ALPHA", etab(siret("alpha"), "5", "RUE", "DE LA PAIX", "75002",
                                           "PARIS"), activite_principale="70.22Z",
                   categorie_entreprise="PME"),
        entreprise("alpha_holding", "ALPHA HOLDING",
                   etab(siret("alpha_holding"), "5", "RUE", "DE LA PAIX", "75002", "PARIS"),
                   activite_principale="64.20Z", categorie_entreprise="PME"),
    ],
    # Ni adresse ni ville : une seule structure de ce nom / deux structures.
    "Zephyr Conseil": [
        entreprise("zephyr", "ZEPHYR CONSEIL",
                   etab(siret("zephyr"), "2", "RUE", "DES LILAS", "31000", "TOULOUSE")),
    ],
    "Double Nom": [
        entreprise("double_1", "DOUBLE NOM", etab(siret("double_1"), "1", "RUE", "A", "13001",
                                                  "MARSEILLE")),
        entreprise("double_2", "DOUBLE NOM", etab(siret("double_2"), "1", "RUE", "B", "06000",
                                                  "NICE")),
    ],
    # « Mairie de X » = « Commune de X » pour l'INSEE.
    "Mairie de Trifouilly": [
        entreprise("commune", "COMMUNE DE TRIFOUILLY",
                   etab(siret("commune"), "1", "PL", "DE LA MAIRIE", "69999", "TRIFOUILLY"),
                   nature_juridique="7210"),
    ],
}
DEPARTEMENTS = {"rennes": ["35"]}


def lire_sortie(chemin):
    """Lit le CSV complété ; renvoie (lignes sans la colonne de statut, {id: statut})."""
    with open(chemin, encoding="utf-8-sig") as f:
        lignes = list(csv.reader(f))
    i = lignes[0].index(enr.COLONNE_STATUT)
    assert lignes[0][i - 1] == "SIRET", "la colonne de statut doit suivre « SIRET »"
    rendus = {l[0]: l[i] for l in lignes[1:]}
    return [l[:i] + l[i + 1:] for l in lignes], rendus


class FauxClient:
    def __init__(self, resultats=RESULTATS, departements=DEPARTEMENTS):
        # La vraie recherche est tolérante (accents, forme juridique) : on l'imite.
        self.index = {}
        for cle_texte, valeur in resultats.items():
            texte, _, dep = cle_texte.partition(" @")
            self.index[(enr.normaliser_nom(texte), dep)] = valeur
        self.deps = departements
        self.requetes = []
        self.dernier_total = 0

    def rechercher(self, texte, par_page=5, page=1, **filtres):
        self.requetes.append((texte, filtres))
        resultats = self.index.get((enr.normaliser_nom(texte), filtres.get("departement", "")), [])
        self.dernier_total = len(resultats)
        return resultats

    def departements(self, ville):
        return self.deps.get(enr.normaliser_ville(ville), [])


ENTETES = ["ID de fiche d'informations", "Nom de l'entreprise", "Secteur d'activité",
           "Pays/Région", "Ville", "Adresse postale", "SIREN", "SIRET", "Type de décideur"]
LIGNES = [
    ["1", "Soleil Énergie SAS", "Énergie", "France", "Lyon", "45 avenue Jean-Jaurès", "", "", ""],
    ["2", "Communauté de communes - Pays de la Serre", "Public", "France", "Crecy Sur Serre",
     "1 rue des Telliers  Crécy-sur-Serre", "", "", ""],
    ["3", "Déménageurs Bretons", "Transport", "France", "Rennes", "4 rue de Brest", "", "", ""],
    ["4", "Atelier Bois", "Artisanat", "", "Nantes", "3 quai de la Fosse", "", "", ""],
    ["5", "Vieille Usine", "Industrie", "France", "Bordeaux", "2 chemin des Vignes", "", "", ""],
    ["6", "Boulangerie Martin", "Alimentaire", "France", "Nantes", "1 place de la Mairie",
     "", "", ""],
    ["7", "Complet", "BTP", "France", "Paris", "1 rue X", N["complet"], siret("complet"), ""],
    ["8", "Déjà SIREN", "Services", "FRANCE", "Paris 9e", "10 boulevard Haussmann",
     " ".join([N["deja"][:3], N["deja"][3:6], N["deja"][6:]]), "", ""],
    ["9", "Acme Inc", "Tech", "United States", "Boston", "1 Main Street", "", "", ""],
    ["10", "Garage Dupuis", "Auto", "France", "Lille", "2 rue Faidherbe", "", "", ""],
    ["11", "Nom sans importance", "BTP", "France", "Grenoble", "7 rue de la Gare", "",
     siret("siret_ok"), ""],
    ["12", "Nom sans importance", "BTP", "France", "Metz", "1 place d'Armes", "",
     siret("siret_autre"), ""],
    ["13", "Incohérente", "BTP", "France", "Paris", "1 rue Y", N["incoherent"],
     siret("autre_siret"), ""],
    ["14", "Soleil Énergie SAS", "Énergie", "France", "Lyon", "45 avenue Jean-Jaurès",
     mauvaise_cle(N["soleil_2"]), "", ""],
    ["15", "Groupe Alpha", "Services", "France", "Paris", "5 rue de la Paix", "", "", "Centralisé"],
    ["16", "Groupe Alpha", "Services", "France", "Paris", "5 rue de la Paix", "", "",
     "Décentralisé"],
    ["17", "Zéphyr Conseil", "Conseil", "", "", "", "", "", ""],
    ["18", "Double Nom", "Conseil", "", "", "", "", "", ""],
    ["19", "Mairie de Trifouilly", "Public", "France", "Trifouilly", "", "", "", ""],
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
        compteurs = enr.traiter(self.entree, self.sortie, self.rapport, {}, 5,
                                client=self.client, **options)
        lignes, self.rendus = lire_sortie(self.sortie)
        with open(self.rapport, encoding="utf-8-sig") as f:
            rapport = {r[0]: r for r in list(csv.reader(f))[1:]}
        return compteurs, {l[0]: l for l in lignes[1:]}, lignes, rapport

    def test_arbre_de_decision(self):
        compteurs, par_id, _, rapport = self.lancer()
        statut = lambda i: rapport[i][4]
        numeros = lambda i: par_id[i][6:8]
        # Bonne adresse (2e résultat, établissement secondaire) : sûr.
        self.assertEqual(numeros("1"), [N["soleil_2"], siret("soleil_2", "0003")])
        self.assertEqual(self.rendus["1"], "Trouvé")
        # Ville répétée dans l'adresse HubSpot.
        self.assertEqual(numeros("2"), [N["cc"], siret("cc")])
        self.assertEqual(par_id["2"][4:6], ["Crecy Sur Serre", "1 rue des Telliers  Crécy-sur-Serre"])
        # Rien dans la ville avec le nom seul -> recherche filtrée sur le département ; autre
        # adresse dans la ville -> adresse corrigée, à vérifier.
        self.assertIn(("Déménageurs Bretons", {"limite_matching_etablissements": 100,
                                               "departement": "35"}), self.client.requetes)
        self.assertEqual(par_id["3"][4:8], ["Rennes", "8 Boulevard de la Liberte",
                                            N["demenageurs"], siret("demenageurs", "0002")])
        self.assertEqual(statut("3"), "ADRESSE CORRIGÉE")
        self.assertEqual(self.rendus["3"], "À vérifier")
        # La ville n'est jamais ajoutée au nom dans la requête.
        self.assertEqual(numeros("4"), [N["atelier"], siret("atelier")])
        self.assertTrue(all("Nantes" not in texte for texte, _ in self.client.requetes))
        # Société cessée trouvée par le nom : SIREN proposé dans le rapport, rien d'écrit.
        self.assertEqual(statut("5"), "À ARBITRER")
        self.assertEqual(rapport["5"][6], N["usine"])
        self.assertEqual(numeros("5"), ["", ""])
        self.assertEqual(self.rendus["5"], "")
        # Rien de fiable -> recherche Internet, rien d'écrit.
        self.assertEqual(numeros("6"), ["", ""])
        self.assertEqual(statut("6"), "RECHERCHE INTERNET")
        # Ligne complète : ignorée, sans appel à l'API.
        self.assertEqual(numeros("7"), [N["complet"], siret("complet")])
        self.assertNotIn("Complet", [t for t, _ in self.client.requetes])
        # SIREN déjà présent : conservé tel quel (espaces compris), SIRET complété.
        self.assertEqual(par_id["8"][6], LIGNES[7][6])
        self.assertEqual(par_id["8"][7], siret("deja"))
        # Hors France : non recherchée.
        self.assertEqual(numeros("9"), ["", ""])
        # Seule entreprise du nom dans la ville, autre adresse : adresse corrigée, à vérifier.
        self.assertEqual(par_id["10"][4:8], ["Lille", "40 Rue Solferino", N["garage"], siret("garage")])
        self.assertEqual(self.rendus["10"], "À vérifier")
        # SIRET connu : recherche par SIRET (jamais par le nom), SIREN écrit.
        self.assertEqual(numeros("11"), [N["siret_ok"], siret("siret_ok")])
        self.assertEqual(statut("11"), "TROUVÉ")
        self.assertNotIn("Nom sans importance", [t for t, _ in self.client.requetes])
        # SIRET connu, adresse différente : SIREN écrit, adresse laissée telle quelle.
        self.assertEqual(par_id["12"][4:8], ["Metz", "1 place d'Armes", N["siret_autre"],
                                             siret("siret_autre")])
        self.assertEqual(statut("12"), "ADRESSE À VÉRIFIER")
        self.assertEqual(self.rendus["12"], "À vérifier")
        # SIREN et SIRET incohérents : signalés, non modifiés.
        self.assertEqual(numeros("13"), [N["incoherent"], siret("autre_siret")])
        self.assertEqual(statut("13"), "INCOHÉRENT")
        # SIREN à clé fausse : signalé avec le SIREN trouvé, rien n'est modifié.
        self.assertEqual(statut("14"), "CLÉ INVALIDE")
        self.assertIn("SIREN proposé : " + N["soleil_2"], rapport["14"][13])
        self.assertEqual(numeros("14"), [mauvaise_cle(N["soleil_2"]), ""])
        # Holding et filiale à la même adresse : Centralisé -> holding, Décentralisé ->
        # entité locale ; proposés, non écrits.
        self.assertEqual((statut("15"), rapport["15"][6]), ("À ARBITRER", N["alpha_holding"]))
        self.assertEqual((statut("16"), rapport["16"][6]), ("À ARBITRER", N["alpha"]))
        self.assertEqual(numeros("15") + numeros("16"), ["", "", "", ""])
        # Ni adresse ni ville : une seule structure de ce nom -> à vérifier ; deux -> rien.
        self.assertEqual(numeros("17"), [N["zephyr"], siret("zephyr")])
        self.assertEqual((statut("17"), self.rendus["17"]), ("TROUVÉ (NOM UNIQUE)", "À vérifier"))
        self.assertEqual((statut("18"), numeros("18")), ("RECHERCHE INTERNET", ["", ""]))
        # « Mairie de X » trouvée comme « Commune de X ».
        self.assertEqual((statut("19"), numeros("19")), ("TROUVÉ (VILLE)", [N["commune"],
                                                                             siret("commune")]))
        self.assertEqual(self.rendus["7"], "")               # déjà renseignée
        attendus = dict.fromkeys(enr.ORDRE_STATUTS, 0)
        attendus.update({"TROUVÉ": 5, "TROUVÉ (VILLE)": 1, "TROUVÉ (NOM UNIQUE)": 1,
                         "ADRESSE CORRIGÉE": 2, "ADRESSE À VÉRIFIER": 1, "À ARBITRER": 3,
                         "CLÉ INVALIDE": 1, "INCOHÉRENT": 1, "RECHERCHE INTERNET": 2,
                         "HORS FRANCE": 1, "DÉJÀ RENSEIGNÉ": 1})
        self.assertEqual(compteurs, attendus)

    def test_options(self):
        _, par_id, _, _ = self.lancer(nom_unique_trouve=True, ecrire_incertains=True)
        self.assertEqual(self.rendus["17"], "Trouvé")
        # Cas à arbitrer écrits en « À vérifier » (adresse jamais modifiée pour eux).
        self.assertEqual(par_id["15"][6], N["alpha_holding"])
        self.assertEqual(par_id["16"][6], N["alpha"])
        self.assertEqual(self.rendus["15"], "À vérifier")
        self.assertEqual(par_id["5"][4:7], ["Bordeaux", "2 chemin des Vignes", N["usine"]])
        # Règle par défaut « groupe » pour un type de décideur vide.
        _, _, _, rapport = self.lancer(defaut_decideur="groupe")
        self.assertEqual(rapport["15"][6], N["alpha_holding"])

    def test_ids_et_autres_colonnes_inchanges(self):
        _, _, lignes, _ = self.lancer(corriger_adresse=False)
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
        self.assertEqual(enr.nom_officiel("Mairie de Trifouilly"), "Commune de Trifouilly")
        self.assertEqual(enr.nom_officiel("Mairie - Trifouilly"), "Commune de Trifouilly")
        self.assertEqual(enr.nom_officiel("Ville de Trifouilly"), "Commune de Trifouilly")
        self.assertEqual(enr.nom_officiel("Villeneuve Énergie"), "Villeneuve Énergie")
        self.assertEqual(enr.nom_court("ACME S.E."), "acme")
        self.assertEqual(enr.nom_court("ACME HOLDING 4 (AH4)"), "acme holding 4")

    def test_score_des_noms(self):
        # L'un contient l'autre mot pour mot...
        self.assertGreaterEqual(enr.score_texte("alter watt", "alter watt energies"), 0.9)
        # ... mais un seul mot du nom HubSpot ne suffit pas.
        self.assertLess(enr.score_texte("generale eaux nord", "generale"), enr.SEUIL_NOM)
        self.assertGreaterEqual(enr.score_texte("credit agricole aquitaine", "credit agricole"), 0.9)

    def test_cle_de_controle(self):
        self.assertTrue(enr.cle_valide(N["soleil_2"]))
        self.assertTrue(enr.cle_valide(siret("soleil_2")))
        self.assertFalse(enr.cle_valide(mauvaise_cle(N["soleil_2"])))
        self.assertFalse(enr.cle_valide("12345"))
        self.assertTrue(enr.cle_valide("35600000000001"))     # SIRET de La Poste : somme / 5

    def test_departements(self):
        reponse = {"features": [
            {"properties": {"citycode": "97411", "score": 0.96}},
            {"properties": {"citycode": "93066", "score": 0.96}},
            {"properties": {"citycode": "11339", "score": 0.93}},
            {"properties": {"citycode": "2A004", "score": 0.40}}]}
        self.assertEqual(enr.departements_geocodage(reponse), ["974", "93", "11"])
        self.assertEqual(enr.departements_geocodage({"features": [
            {"properties": {"citycode": "51457", "score": 0.35}}]}), [])


class FausseConnexion:
    """Coupe la première requête, puis répond."""

    def __init__(self, reponses):
        self.reponses = list(reponses)
        self.appels = 0

    def get(self, chemin):
        self.appels += 1
        reponse = self.reponses.pop(0)
        if isinstance(reponse, Exception):
            raise reponse
        return reponse


class TestClient(unittest.TestCase):
    @mock.patch.object(enr.time, "sleep")
    def test_reprise_et_cache(self, _):
        cache = tempfile.mkdtemp()
        client = enr.ClientAnnuaire(delai=0, cache=cache)
        corps = json.dumps({"results": [{"siren": N["zephyr"]}], "total_results": 1}).encode()
        connexion = FausseConnexion([ConnectionResetError(), (429, b""), (200, corps)])
        client.connexions[enr.API_HOTE] = connexion
        self.assertEqual(client.rechercher("Zephyr Conseil", par_page=25), [{"siren": N["zephyr"]}])
        self.assertEqual((client.dernier_total, connexion.appels), (1, 3))
        # 2e appel identique : lu dans le cache, sans requête.
        self.assertEqual(client.rechercher("Zephyr Conseil", par_page=25), [{"siren": N["zephyr"]}])
        self.assertEqual(connexion.appels, 3)
        self.assertEqual(len(os.listdir(cache)), 1)

    @mock.patch.object(enr.time, "sleep")
    def test_requete_refusee(self, _):
        client = enr.ClientAnnuaire(delai=0)
        client.connexions[enr.API_HOTE] = FausseConnexion([(400, b"{}")])
        self.assertEqual(client.rechercher("AB"), [])


def ecole(nom_cle, nom, siege, matching=None, nature="9220", activite="85.20Z", etat="A"):
    return entreprise(nom_cle, nom, siege, etat=etat, matching=matching, nature_juridique=nature,
                      activite_principale=activite)


RESULTATS_ECOLES = {
    # Nom pollué (« DAH - », ville en suffixe) et entité juridique au nom d'OGEC.
    "ECOLE SAINTE MARGUERITE": [
        ecole("marguerite", "OGEC STE MARGUERITE",
              etab(siret("marguerite"), "2", "RUE", "DE L EGLISE", "69610", "HAUTE-RIVOIRE")),
    ],
    # Deux OGEC « Saint Joseph » différents dans la même ville : à arbitrer.
    "Ecole Saint Joseph": [
        ecole("joseph_1", "OGEC SAINT JOSEPH",
              etab(siret("joseph_1"), "5", "RUE", "SALA", "69002", "LYON")),
        ecole("joseph_2", "ASSOCIATION SAINT JOSEPH",
              etab(siret("joseph_2"), "9", "RUE", "MARIETTON", "69009", "LYON")),
    ],
    # Une SARL homonyme n'est pas une école.
    "College Notre Dame": [
        ecole("notre_dame", "NOTRE DAME", etab(siret("notre_dame"), "1", "RUE", "NATIONALE",
                                               "59000", "LILLE"),
              nature="5499", activite="47.11B"),
    ],
    # Adresse HubSpot générique : ignorée, l'école est trouvée sur le nom et la ville.
    "Lycee Sainte Anne": [
        ecole("anne", "ORGANISME DE GESTION DE L ENSEIGNEMENT CATHOLIQUE SAINTE ANNE",
              etab(siret("anne"), "20", "RUE", "LAMARTINE", "29200", "BREST")),
    ],
    # SIREN connu, ni adresse ni ville : une seule structure -> SIRET du siège.
    N["louis"]: [
        ecole("louis", "OGEC SAINT LOUIS",
              etab(siret("louis"), "4", "PL", "DU MARCHE", "44000", "NANTES")),
    ],
}


class TestEcoles(unittest.TestCase):
    ENTETES = ["ID de fiche d'informations", "Nom de l'entreprise", "Ville",
               "Sous-catégorie d'actifs majoritaires", "Pays/Région", "Adresse postale",
               "SIREN", "SIRET"]
    CAT = "Enseignement Privé - Ecoles, collège, Lycée"

    def test_ecoles(self):
        lignes = [
            ["1", "DAH - ECOLE SAINTE MARGUERITE - Haute Rivoire", "Haute-Rivoire", self.CAT,
             "", "", "", ""],
            ["2", "Ecole Saint Joseph", "Lyon", self.CAT, "", "", "", ""],
            ["3", "Collège Notre Dame", "Lille", self.CAT, "", "", "", ""],
            # Trois fiches de villes différentes avec la même adresse : adresse générique.
            ["4", "Lycée Sainte Anne", "Brest", self.CAT, "", "277 rue Saint-Jacques", "", ""],
            ["5", "Autre école", "Rennes", self.CAT, "", "277 rue Saint-Jacques", "", ""],
            ["6", "Encore une école", "Nice", self.CAT, "", "277 rue Saint-Jacques", "", ""],
            ["7", "OGEC Saint Louis", "", self.CAT, "", "", N["louis"], ""],
            ["8", "Ecole Saint Pierre", "", self.CAT, "", "", "", ""],
            ["9", "École inconnue", "Paris", self.CAT, "", "", "", siret("inconnue")],
        ]
        dossier = tempfile.mkdtemp()
        entree, sortie, rapport = (os.path.join(dossier, n) for n in ("e.csv", "s.csv", "r.csv"))
        with open(entree, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(self.ENTETES)
            w.writerows(lignes)
        client = FauxClient(RESULTATS_ECOLES)
        enr.traiter(entree, sortie, rapport, {}, 5, client=client)
        lignes_sortie, rendus = lire_sortie(sortie)
        par_id = {l[0]: l for l in lignes_sortie[1:]}
        with open(rapport, encoding="utf-8-sig") as f:
            statut = {l[0]: l[4] for l in list(csv.reader(f))[1:]}

        # Nom nettoyé, OGEC reconnu dans la ville ; l'adresse vide n'est pas remplie.
        self.assertEqual(statut["1"], "TROUVÉ (VILLE)")
        self.assertEqual(par_id["1"][5:], ["", N["marguerite"], siret("marguerite")])
        self.assertEqual(rendus["1"], "À vérifier")
        # Deux écoles du même nom dans la ville : à arbitrer, rien d'écrit.
        self.assertEqual(statut["2"], "À ARBITRER")
        self.assertEqual(par_id["2"][6:], ["", ""])
        # Entreprise commerciale homonyme : rejetée.
        self.assertEqual(statut["3"], "RECHERCHE INTERNET")
        # Adresse générique ignorée : trouvée sur le nom et la ville, adresse inchangée.
        self.assertEqual(statut["4"], "TROUVÉ (VILLE)")
        self.assertEqual(par_id["4"][5:], ["277 rue Saint-Jacques", N["anne"], siret("anne")])
        # SIREN connu, ni adresse ni ville : SIRET du siège.
        self.assertEqual(par_id["7"][6:], [N["louis"], siret("louis")])
        # Ni adresse ni ville, aucun résultat.
        self.assertEqual(statut["8"], "RECHERCHE INTERNET")
        # SIRET introuvable : SIREN déduit du SIRET, écrit comme « À vérifier ».
        self.assertEqual(statut["9"], "À VÉRIFIER")
        self.assertEqual(par_id["9"][6:], [N["inconnue"], siret("inconnue")])
        self.assertEqual(rendus["9"], "À vérifier")

        # Relancer sur le CSV complété ne duplique pas la colonne et garde les statuts.
        sortie_2 = os.path.join(dossier, "s2.csv")
        enr.traiter(sortie, sortie_2, os.path.join(dossier, "r2.csv"), {}, 5, client=client)
        with open(sortie_2, encoding="utf-8-sig") as f:
            entetes_2 = next(csv.reader(f))
        self.assertEqual(entetes_2.count(enr.COLONNE_STATUT), 1)
        self.assertEqual(lire_sortie(sortie_2)[1]["1"], "À vérifier")

    def test_noms(self):
        self.assertEqual(enr.parties_nom("DAH - OGEC Saint Martin - Collège Immaculée "
                                         "Conception (fermé)", "Biarritz"),
                         ["OGEC Saint Martin - Collège Immaculée Conception",
                          "Collège Immaculée Conception", "OGEC Saint Martin"])
        self.assertEqual(enr.parties_nom("ECOLE SAINT JOSEPH - MARCOUSSIS", "MARCOUSSIS"),
                         ["ECOLE SAINT JOSEPH - MARCOUSSIS", "ECOLE SAINT JOSEPH"])
        oge = {"nom_complet": "ORGANISME DE GESTION DE L ENSEIGNEMENT CATHOLIQUE SAINTE ANNE"}
        self.assertEqual(enr.score_nom("École Sainte-Anne", oge, ecole=True), 1.0)
        self.assertLess(enr.score_nom("Ecole Saint Joseph", {"nom_complet": "OGEC SAINT JEAN"},
                                      ecole=True), enr.SEUIL_NOM)
        # « Saint » seul ne suffit jamais.
        self.assertLess(enr.score_nom("Ecole Saint", {"nom_complet": "OGEC SAINT PAUL"},
                                      ecole=True), enr.SEUIL_NOM)


if __name__ == "__main__":
    unittest.main()
