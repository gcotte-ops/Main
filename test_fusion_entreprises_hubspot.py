"""Tests hors ligne de la fusion des entreprises : HubSpot est simulé."""

import csv
import os
import tempfile
import unittest
import zipfile

import fusion_doublons_hubspot as fc
import fusion_entreprises_hubspot as fe

ENTETES = ["Groupe", "Niveau", "Raison du rapprochement", "Racine suggérée", "ID HubSpot",
           "Lien HubSpot", "Nom de l’entreprise", "Ville", "SIREN", "SIRET", "Téléphone",
           "Nom de domaine", "Type de décideur", "Propriétaire", "Contacts associés",
           "Date de création"]


def entreprise(id, creation, contacts=0, racine=False, actif=None, dates=None, transactions=0,
               **valeurs):
    return fe.Entreprise(id, valeurs, dates=dates, nb_contacts=contacts, creation=creation,
                         racine=racine, proprietaire_actif=actif, nb_transactions=transactions)


def ecrire_xlsx(chemin, lignes, feuille="Doublons"):
    """Classeur minimal : une feuille, textes en ligne, nombres en valeur."""
    def cellule(ref, v):
        if isinstance(v, (int, float)):
            return '<c r="{}"><v>{}</v></c>'.format(ref, v)
        texte = str(v).replace("&", "&amp;").replace("<", "&lt;")
        return '<c r="{}" t="inlineStr"><is><t>{}</t></is></c>'.format(ref, texte)
    rows = []
    for i, ligne in enumerate(lignes, 1):
        cells = "".join(cellule("{}{}".format(chr(65 + j), i), v)
                        for j, v in enumerate(ligne) if v not in (None, ""))
        rows.append('<row r="{}">{}</row>'.format(i, cells))
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    with zipfile.ZipFile(chemin, "w") as z:
        z.writestr("xl/workbook.xml", (
            '<workbook {} xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/'
            'relationships"><sheets><sheet name="Synthèse" sheetId="1" r:id="rId1"/>'
            '<sheet name="{}" sheetId="2" r:id="rId2"/></sheets></workbook>').format(ns, feuille))
        z.writestr("xl/_rels/workbook.xml.rels", (
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="x"/>'
            '<Relationship Id="rId2" Target="/xl/worksheets/sheet2.xml" Type="x"/>'
            '</Relationships>'))
        z.writestr("xl/worksheets/sheet1.xml", '<worksheet {}><sheetData/></worksheet>'.format(ns))
        z.writestr("xl/worksheets/sheet2.xml", '<worksheet {}><sheetData>{}</sheetData>'
                   '</worksheet>'.format(ns, "".join(rows)))


class Lecture(unittest.TestCase):

    def test_xlsx(self):
        dossier = tempfile.mkdtemp()
        chemin = os.path.join(dossier, "doublons.xlsx")
        ecrire_xlsx(chemin, [
            ENTETES,
            ["G-001", "Certain", "Même nom + même ville", "Oui", 14939896642, "Ouvrir",
             "ABBAYE DE LA COUDRE", "Laval", "352761043", "", "", "abbaye-coudre.fr", "",
             "", 2, "2021-07-09 14:48"],
            ["G-001", "Certain", "Même nom + même ville", "", 6543335692.0, "Ouvrir",
             "EURL ABBAYE & CIE", "LAVAL", "", "", "", "", "", "", 0, "2021-07-09 14:48"],
            ["G-500", "Probable", "Nom à une faute près", "", 1, "Ouvrir", "X", "", "", "",
             "", "", "", "", 0, ""],
        ])
        lignes = fe.lire_liste(chemin)
        self.assertEqual([l["ID HubSpot"] for l in lignes], ["14939896642", "6543335692"])
        self.assertEqual(lignes[1]["Nom de l’entreprise"], "EURL ABBAYE & CIE")
        self.assertEqual(lignes[0]["Contacts associés"], "2")


class Regles(unittest.TestCase):

    def test_valeurs_factices(self):
        self.assertEqual(fe.nettoyer("domain", "4313.co"), "")
        self.assertEqual(fe.nettoyer("phone", "00 00 00 00 00"), "")
        self.assertEqual(fe.nettoyer("siren", '="012345678"'), "012345678")
        self.assertEqual(fe.nettoyer("domain", "abbaye-coudre.fr"), "abbaye-coudre.fr")

    def test_racine_le_plus_de_contacts(self):
        a = entreprise(1, "2021", contacts=1, racine=True, name="ABBAYE")
        b = entreprise(2, "2023", contacts=4, name="abbaye.fr")
        self.assertIs(fe.choisir_racine([a, b])[0], b)
        b.nb_contacts = 1                    # égalité : la racine suggérée
        self.assertIs(fe.choisir_racine([a, b])[0], a)

    def test_racine_avec_transactions(self):
        a = entreprise(1, "2021", contacts=1, transactions=2, name="ABBAYE")
        b = entreprise(2, "2023", contacts=9, racine=True, name="ABBAYE")
        self.assertIs(fe.choisir_racine([a, b])[0], a)

    def test_transactions_des_deux_cotes_gt3(self):
        a = entreprise(1, "2021", contacts=1, transactions=2, name="ABBAYE")
        b = entreprise(2, "2023", contacts=9, transactions=1, name="ABBAYE")
        # Une seule des deux dans la GT 3.0 : c'est elle, même avec moins de contacts.
        racine, remarque = fe.choisir_racine([a, b], gt3={"1", "77"})
        self.assertIs(racine, a)
        self.assertIn("GT 3.0", remarque)
        # Les deux dans la GT 3.0, aucune, ou GT 3.0 non fournie : le plus de contacts.
        for gt3 in ({"1", "2"}, set(), None):
            self.assertIs(fe.choisir_racine([a, b], gt3=gt3)[0], b)
        plan = fe.planifier("G-001", [a, b], fe.PROPRIETES_DEFAUT, gt3={"1", "2"})
        self.assertIs(plan["racine"], b)
        self.assertTrue(any("toutes dans la GT 3.0" in r for r in plan["remarques"]))

    def test_lecture_gt3(self):
        dossier = tempfile.mkdtemp()
        liste = os.path.join(dossier, "gt3_ids.txt")
        with open(liste, "w") as f:
            f.write("# GT 3.0 (onglet GT3, colonne Id_hubspot) - extraction\n"
                    "8881957130\n16091473180\n\n")
        self.assertEqual(fe.lire_gt3(liste), {"8881957130", "16091473180"})
        export = os.path.join(dossier, "GT3.csv")
        with open(export, "w", encoding="utf-8") as f:
            f.write("Numero_projet,Nom_projet,Lien_hubspot,Id_hubspot\n"
                    "2022255,AFS,https://app.hubspot.com/contacts/1/record/0-2/8881957130,"
                    "8881957130\n"
                    "2022430,Ch,https://app.hubspot.com/contacts/1/record/0-2/16091473180,\n"
                    "2022431,X,,\n")
        self.assertEqual(fe.lire_gt3(export), {"8881957130", "16091473180"})

    def test_siren_differents(self):
        a = entreprise(1, "2021", name="Sainte Marie Antony", siren="301546503")
        b = entreprise(2, "2022", name="Association Sainte-Marie", siret="52957270300013")
        plan = fe.planifier("G-037", [a, b], fe.PROPRIETES_DEFAUT)
        self.assertEqual(plan["statut"], "À VÉRIFIER")

    def test_valeur_la_plus_recente(self):
        a = entreprise(1, "2021-01-01", contacts=3, phone="+33 3 28 36 56 56", city="LILLE",
                       dates={"phone": "2021-01-01", "city": "2021-01-01"})
        b = entreprise(2, "2023-01-01", phone="+33 3 28 36 56 66", city="Lille", siren="123456789")
        self.assertEqual(fe.choisir_valeur("phone", [a, b], a), "+33 3 28 36 56 66")
        self.assertEqual(fe.choisir_valeur("city", [a, b], a), "LILLE")    # équivalente
        self.assertEqual(fe.choisir_valeur("siren", [a, b], a), "123456789")  # complétée
        b.valeurs["phone"] = "03 28 36 56 56"                               # même numéro
        self.assertEqual(fe.choisir_valeur("phone", [a, b], a), "+33 3 28 36 56 56")

    def test_type_de_decideur_inconnu(self):
        a = entreprise(1, "2023", contacts=6, type_de_decideur="Décentralisé")
        b = entreprise(2, "2025", type_de_decideur="Ne sais pas encore")
        self.assertEqual(fe.choisir_valeur("type_de_decideur", [a, b], a), "Décentralisé")

    def test_domaines(self):
        racine = entreprise(1, "2022", contacts=4, name="Aix-Marseille Université",
                            domain="univ-amu.fr")
        autre = entreprise(2, "2024", domain="etu.univ-amu.fr")
        self.assertEqual(fe.choisir_valeur("domain", [racine, autre], racine), "univ-amu.fr")
        racine.valeurs["domain"] = "intranet.apei.fr"
        autre.valeurs["domain"] = "apei.fr"
        self.assertEqual(fe.choisir_valeur("domain", [racine, autre], racine), "apei.fr")
        # Domaine de la racine conservé face à un autre vrai domaine plus récent.
        racine.valeurs["domain"] = "loire-atlantique.fr"
        autre.valeurs["domain"] = "loire-atlantique.gouv.fr"
        self.assertEqual(fe.choisir_valeur("domain", [racine, autre], racine),
                         "loire-atlantique.fr")
        # Punycode, plateforme ou factice : remplacés.
        racine.valeurs["domain"] = "xn--manrse-6ua.com"
        autre.valeurs["domain"] = "manrese.com"
        self.assertEqual(fe.choisir_valeur("domain", [racine, autre], racine), "manrese.com")
        racine.valeurs["domain"] = "sacrecoeur.paysdelaloire.e-lyco.fr"
        autre.valeurs["domain"] = "sacrecoeurlemans.fr"
        self.assertEqual(fe.choisir_valeur("domain", [racine, autre], racine),
                         "sacrecoeurlemans.fr")

    def test_racine_sans_nom(self):
        # G-226 : la fiche créée depuis un domaine a plus de contacts et reste la racine,
        # mais le nom et le domaine viennent de la vraie fiche.
        vraie = entreprise(1, "2023-02-15", contacts=0, racine=True, name="Ville de Nevers",
                           domain="nevers.fr", siren="831869367")
        auto = entreprise(2, "2025-11-20", contacts=1, domain="ville-nevers.fr")
        plan = fe.planifier("G-226", [vraie, auto], fe.PROPRIETES_DEFAUT)
        self.assertIs(plan["racine"], auto)
        self.assertEqual(plan["cibles"]["name"], "Ville de Nevers")
        self.assertEqual(plan["cibles"]["domain"], "nevers.fr")
        self.assertEqual(plan["cibles"]["siren"], "831869367")

    def test_proprietaire(self):
        racine = entreprise(1, "2021", contacts=2, hubspot_owner_id="11", actif=False)
        autre = entreprise(2, "2023", hubspot_owner_id="22", actif=True)
        self.assertEqual(fe.choisir_proprietaire([racine, autre], racine)[0], "22")
        # Aucun actif : rien n'est ajouté sur une racine sans propriétaire.
        racine.valeurs.pop("hubspot_owner_id")
        autre.proprietaire_actif = False
        self.assertEqual(fe.choisir_proprietaire([racine, autre], racine), ("", ""))


class FauxHubSpot:
    """Entreprises en mémoire ; une fusion garde la racine et crée un nouvel ID."""

    def __init__(self, entreprises):
        self.entreprises = entreprises
        self.redirections = {}
        self.appels = []
        self.prochain = 9000

    def proprietes_modifiables(self):
        return list(fe.PROPRIETES_DEFAUT)

    def entreprise(self, id_entreprise, proprietes, racine=False):
        id_entreprise = self.redirections.get(str(id_entreprise), str(id_entreprise))
        f = self.entreprises.get(id_entreprise)
        if f is None:
            return None
        return fe.Entreprise(f.id, dict(f.valeurs), dates=dict(f.dates),
                             nb_contacts=f.nb_contacts, creation=f.creation, racine=racine,
                             proprietaire_actif=f.proprietaire_actif,
                             nb_transactions=f.nb_transactions)

    def fusionner_entreprises(self, principal, autre):
        self.appels.append(("merge", principal, autre))
        p, a = self.entreprises.pop(principal), self.entreprises.pop(autre)
        nouveau = str(self.prochain)
        self.prochain += 1
        p.id = nouveau
        p.nb_contacts += a.nb_contacts
        p.nb_transactions += a.nb_transactions
        self.entreprises[nouveau] = p
        for k in [principal, autre] + [k for k, v in self.redirections.items()
                                       if v in (principal, autre)]:
            self.redirections[k] = nouveau
        return nouveau

    def modifier_entreprise(self, id_entreprise, proprietes):
        self.appels.append(("patch", id_entreprise, proprietes))
        return []


class Execution(unittest.TestCase):

    def setUp(self):
        dossier = tempfile.mkdtemp()
        self.liste = os.path.join(dossier, "doublons.csv")
        self.rapport = os.path.join(dossier, "rapport.csv")
        with open(self.liste, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(ENTETES)
            w.writerow(["G-002", "Certain", "x", "Oui", "10", "", "ABBAYE DU RIVET", "", "", "",
                        "", "", "", "", "1", "2021-07-09 14:48"])
            w.writerow(["G-002", "Certain", "x", "", "20", "", "abbaye.com", "", "", "", "", "",
                        "", "", "0", "2023-03-16 14:39"])
        self.client = FauxHubSpot({
            "10": entreprise("10", "2021-07-09", contacts=1, name="ABBAYE DU RIVET",
                             phone="+33556650530", city="AUROS", hubspot_owner_id="11",
                             actif=False),
            "20": entreprise("20", "2023-03-16", contacts=3, name="abbaye.com",
                             domain="abbayesaintemariedurivet.com", phone="335 56 65 05 30",
                             city="Auros", hubspot_owner_id="22", actif=True),
        })

    def test_simulation(self):
        compteur = fe.traiter(self.liste, self.rapport, client=self.client, journal=lambda *a: 0)
        self.assertEqual(compteur, {"SIMULATION": 1})
        self.assertEqual(self.client.appels, [])

    def test_fiche_avec_transaction_gardee_en_racine(self):
        self.client.entreprises["10"].nb_transactions = 1
        fe.traiter(self.liste, self.rapport, client=self.client, reel=True, journal=lambda *a: 0)
        self.assertEqual(self.client.appels[0], ("merge", "10", "20"))
        with open(self.rapport, encoding="utf-8-sig") as f:
            ligne = next(csv.DictReader(f, delimiter=";"))
        self.assertEqual(ligne["Transactions par fiche"], "1 ; 0")
        self.assertEqual(ligne["Fiche racine"], "10")

    def test_fusion_dans_la_fiche_qui_a_le_plus_de_contacts(self):
        compteur = fe.traiter(self.liste, self.rapport, client=self.client, reel=True,
                              journal=lambda *a: 0)
        self.assertEqual(compteur, {"FUSIONNÉ": 1})
        self.assertEqual(self.client.appels[0], ("merge", "20", "10"))
        patch = self.client.appels[1]
        self.assertEqual(patch[1], "9000")
        self.assertEqual(patch[2], {"name": "ABBAYE DU RIVET"})   # le reste est déjà bon
        # Relance : rien n'est refait.
        self.client.appels.clear()
        compteur = fe.traiter(self.liste, self.rapport, client=self.client, reel=True,
                              journal=lambda *a: 0)
        self.assertEqual(compteur, {"DÉJÀ FUSIONNÉ": 1})
        self.assertEqual(self.client.appels, [])


class ClientHubSpot(unittest.TestCase):

    def client(self, reponses):
        client = fe.ClientEntreprises("x")
        appels = []

        def requete(methode, chemin, corps=None):
            appels.append((methode, chemin, corps))
            for (m, debut), rep in reponses.items():
                if m == methode and chemin.startswith(debut):
                    if isinstance(rep, Exception):
                        raise rep
                    return rep
            raise AssertionError(chemin)
        client.requete = requete
        return client, appels

    def test_lecture_avec_historique(self):
        client, _ = self.client({
            ("GET", "/crm/v3/owners"): {"results": [{"id": "22"}]},
            ("GET", "/crm/v3/objects/companies/10?"): {"id": "10", "properties": {
                "name": "ABBAYE", "phone": "00 00 00 00 00", "city": "Auros",
                "hubspot_owner_id": "22", "num_associated_contacts": "3",
                "num_associated_deals": "2",
                "createdate": "2021-07-09T12:48:00Z"},
                "propertiesWithHistory": {"city": [
                    {"value": "Auros", "timestamp": "2024-05-02T10:00:00.000Z"},
                    {"value": "AUROS", "timestamp": "2021-07-09T12:48:00.000Z"}]}},
        })
        f = client.entreprise("10", ["name", "phone", "city", "hubspot_owner_id"])
        self.assertEqual((f.nb_contacts, f.nb_transactions), (3, 2))
        self.assertNotIn("phone", f.valeurs)                      # numéro factice
        self.assertEqual(f.dates["city"], "2024-05-02 10:00:00")
        self.assertEqual(f.dates["name"], "2021-07-09 12:48:00")   # sans historique
        self.assertIs(f.proprietaire_actif, True)

    def test_proprietes_modifiables(self):
        client, _ = self.client({("GET", "/crm/v3/properties/companies"): {"results": [
            {"name": "name", "hubspotDefined": True},
            {"name": "siren", "hubspotDefined": False},
            {"name": "montant", "hubspotDefined": False, "calculated": True},
            {"name": "notes_last_updated", "hubspotDefined": True,
             "modificationMetadata": {"readOnlyValue": True}},
            {"name": "hs_analytics_source", "hubspotDefined": True},
            {"name": "lifecyclestage", "hubspotDefined": True},
        ]}})
        self.assertEqual(client.proprietes_modifiables(), ["name", "siren"])

    def test_valeur_refusee(self):
        client, appels = self.client({})

        def requete(methode, chemin, corps=None):
            appels.append(corps)
            if "montant" in corps["properties"]:
                raise fc.ErreurHubSpot(400, "calculated property")
            return {}
        client.requete = requete
        refusees = client.modifier_entreprise("1", {"name": "A", "montant": "3"})
        self.assertEqual(refusees, ["montant"])
        self.assertIn({"properties": {"name": "A"}}, appels)


if __name__ == "__main__":
    unittest.main()
