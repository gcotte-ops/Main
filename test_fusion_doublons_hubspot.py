"""Tests hors ligne : HubSpot est remplacé par un faux client en mémoire."""

import csv
import os
import tempfile
import unittest

import fusion_doublons_hubspot as fus

ENTETES = ["Groupe", "Niveau", "Raison du rapprochement", "Racine suggérée", "ID HubSpot",
           "Lien HubSpot", "Prénom", "Nom", "E-mail", "Téléphone", "Entreprise",
           "Intitulé du poste", "Propriétaire du contact", "Date de création",
           "Dernière activité", "LinkedIn"]

CHANGEMENT = "Même prénom et nom + même identifiant email, a changé d’entreprise ou de domaine"
DOMAINE = "Même boîte mail sur deux domaines de la même structure"


def fiche(id, creation, **kw):
    return fus.Fiche(id=id, creation=creation, **kw)


class Regles(unittest.TestCase):

    def test_casse(self):
        self.assertEqual(fus.casse_nom("JEAN-PIERRE"), "Jean-Pierre")
        self.assertEqual(fus.casse_nom("DE VILLIERS"), "de Villiers")
        self.assertEqual(fus.casse_nom("D'HALLUIN"), "d'Halluin")
        self.assertEqual(fus.casse_nom("O'BRIEN"), "O'Brien")
        self.assertEqual(fus.graphie(["DUCHENE", "Duchene"]), "Duchene")
        self.assertEqual(fus.graphie(["Francois", "François"]), "François")
        self.assertEqual(fus.graphie(["ALLARD d'ARGOEUVES"]), "Allard d'Argoeuves")
        self.assertEqual(fus.graphie(["R&D"]), "R&D")

    def test_telephones(self):
        self.assertEqual(fus.chiffres("+33 (0)6 73 80 44 68"), "0673804468")
        self.assertEqual(fus.chiffres("336 33 00 34 80"), "0633003480")
        self.assertEqual(fus.chiffres("33 6 33 00 34 80"), "0633003480")
        self.assertTrue(fus.est_mobile("+33626533987"))
        self.assertFalse(fus.est_mobile("01 43 45 69 13"))

    def test_email_valide(self):
        self.assertTrue(fus.email_valide("marie.dupeyroux@corum-am.com"))
        self.assertFalse(fus.email_valide("marie.dupeyroux@xn--corumam-906c.com"))
        self.assertFalse(fus.email_valide("helene.auffret@griffaton_et_montreuil.fr"))

    def test_civilites(self):
        self.assertEqual(fus.nettoyer_nom("M. Frederic BEAU", ""), ("", "Frederic BEAU"))
        self.assertEqual(fus.nettoyer_nom("Madame", "Mouton"), ("", "Mouton"))
        self.assertEqual(fus.nettoyer_nom("Stéphane", "M. Rault"), ("Stéphane", "Rault"))
        self.assertEqual(fus.nettoyer_nom("Abbé Louis-Joseph", "Vaillant"),
                         ("Louis-Joseph", "Vaillant"))

    def test_prenoms(self):
        a = fiche(1, "2023", prenom="S", nom="Duchene")
        b = fiche(2, "2023", prenom="Sophie", nom="DUCHENE")
        c = fiche(3, "2023", prenom="Nadia", nom="Gowsy")
        d = fiche(4, "2023", prenom="Thibault", nom="François")
        e = fiche(5, "2023", prenom="François", nom="Thibault")
        self.assertTrue(fus.prenoms_compatibles(a, b))
        self.assertFalse(fus.prenoms_compatibles(b, c))
        self.assertTrue(fus.prenoms_compatibles(d, e))

    def test_nom_le_mieux_renseigne(self):
        # Initiale + nom complet sur une autre fiche.
        fiches = [fiche(1, "2023-07", prenom="S", nom="Duchene", racine=True),
                  fiche(2, "2023-11", prenom="Sophie", nom="DUCHENE"),
                  fiche(3, "2023-12")]
        self.assertEqual(fus.choisir_nom(fiches, fiches[0])[:2], ("Sophie", "Duchene"))
        # Nom complet dans le champ nom, prénom vide : la forme la plus complète l'emporte.
        fiches = [fiche(1, "2025", prenom="Sabine", nom="Nevers", racine=True),
                  fiche(2, "2024", nom="Sabine Nevers-Brunel")]
        self.assertEqual(fus.choisir_nom(fiches, fiches[0])[:2], ("Sabine", "Nevers-Brunel"))
        # Prénom/nom inversés : la répartition majoritaire gagne.
        fiches = [fiche(1, "2026", prenom="François", nom="Thibault", racine=True),
                  fiche(2, "2024", prenom="Thibault", nom="François"),
                  fiche(3, "2023", prenom="Thibault", nom="Francois")]
        self.assertEqual(fus.choisir_nom(fiches, fiches[0])[:2], ("Thibault", "François"))
        # Aucun prénom : redécoupage confirmé par l'email.
        fiches = [fiche(1, "2024", nom="Léa Sournac", email="l.sournac@6si.fr")]
        self.assertEqual(fus.choisir_nom(fiches, fiches[0])[:2], ("Léa", "Sournac"))

    def test_email(self):
        racine = fiche(1, "2025-01", email="marie.dupeyroux@corum-am.com", racine=True)
        recente = fiche(2, "2026-09", email="marie.dupeyroux@xn--corumam-906c.com")
        self.assertIs(fus.choisir_email([racine, recente], CHANGEMENT), racine)
        racine = fiche(1, "2025-11", email="s.fesq@5-cinq.com", racine=True)
        recente = fiche(2, "2026-09", email="s.fesq@avramova.org")
        self.assertIs(fus.choisir_email([racine, recente], CHANGEMENT), recente)
        racine = fiche(1, "2023", email="monprojetrenov@nantesmetropole.fr", racine=True)
        recente = fiche(2, "2025", email="monprojetrenov@nantesmetrople.fr")
        self.assertIs(fus.choisir_email([racine, recente], DOMAINE), racine)
        racine = fiche(1, "2023", email="sduchene@archimeet.fr", racine=True, en_echec=True)
        autre = fiche(2, "2022", email="s.duchene@archimeet.fr")
        self.assertIs(fus.choisir_email([racine, autre], DOMAINE), autre)

    def test_plan(self):
        racine = fiche(1, "2025-11-18", prenom="Sébastien", nom="Fesq", email="s.fesq@5-cinq.com",
                       telephone="01 43 45 69 13", entreprise="5-CINQ",
                       poste="Chargé de projet économie", proprietaire="11",
                       proprietaire_actif=False, racine=True)
        recente = fiche(2, "2026-09-22", prenom="Sébastien", nom="Fesq",
                        email="s.fesq@avramova.org", telephone="+33 (0)6 73 80 44 68",
                        entreprise="Avramova & Associes Architecte", id_entreprise="77",
                        poste="Chargé de projet", proprietaire="22", proprietaire_actif=True)
        plan = fus.planifier("G-008", [racine, recente], CHANGEMENT)
        self.assertEqual(plan["statut"], "À FUSIONNER")
        self.assertIs(plan["principale"], recente)
        self.assertEqual(plan["poste"], "Chargé de projet")
        self.assertEqual(plan["entreprise"], "Avramova & Associes Architecte")
        self.assertEqual(plan["id_entreprise"], "77")
        self.assertEqual(plan["telephone"], "+33 (0)6 73 80 44 68")
        self.assertEqual(plan["non_repris"], ["01 43 45 69 13"])
        self.assertEqual(plan["proprietaire"], "22")

    def test_poste_et_entreprise_de_la_fiche_la_plus_recente_qui_en_a(self):
        racine = fiche(1, "2024", prenom="Jessica", nom="Sinibaldi", entreprise="Objectif 54",
                       poste="Directrice", racine=True, email="jessica.s@objectif54.fr")
        recente = fiche(2, "2025", entreprise="54.fr", email="jessica.s@objectif.54.fr")
        plan = fus.planifier("G-009", [racine, recente], DOMAINE)
        self.assertEqual(plan["entreprise"], "Objectif 54")   # « 54.fr » vient du domaine
        self.assertEqual(plan["poste"], "Directrice")

    def test_prenoms_differents_non_fusionnes(self):
        a = fiche(1, "2023", prenom="Mélissa", nom="Belkadi", racine=True)
        b = fiche(2, "2023", prenom="Nadia", nom="Gowsy")
        self.assertEqual(fus.planifier("G-068", [a, b], DOMAINE)["statut"], "À VÉRIFIER")


class FauxHubSpot:
    """Contacts en mémoire ; une fusion crée un nouvel ID, comme HubSpot."""

    def __init__(self, contacts):
        self.contacts = contacts          # id -> Fiche
        self.redirections = {}
        self.appels = []
        self.prochain = 9000

    def fiche(self, id_contact, racine=False):
        id_contact = self.redirections.get(str(id_contact), str(id_contact))
        f = self.contacts.get(id_contact)
        if f is None:
            return None
        copie = fus.Fiche(**{k: getattr(f, k) for k in (
            "id", "prenom", "nom", "email", "telephone", "mobile", "poste", "entreprise",
            "id_entreprise", "proprietaire", "proprietaire_actif", "creation", "en_echec")})
        copie.racine = racine
        return copie

    def fusionner(self, principal, autre):
        self.appels.append(("merge", principal, autre))
        p, a = self.contacts.pop(principal), self.contacts.pop(autre)
        nouveau = str(self.prochain)
        self.prochain += 1
        p.id = nouveau
        for champ in ("telephone",):
            if not getattr(p, champ):
                setattr(p, champ, getattr(a, champ))
        self.contacts[nouveau] = p
        for ancien in (principal, autre):
            self.redirections[ancien] = nouveau
        for k, v in list(self.redirections.items()):
            if v in (principal, autre):
                self.redirections[k] = nouveau
        return nouveau

    def modifier(self, id_contact, proprietes):
        self.appels.append(("patch", id_contact, proprietes))

    def entreprise_principale(self, id_contact, id_entreprise):
        self.appels.append(("assoc", id_contact, id_entreprise))


class Execution(unittest.TestCase):

    def ecrire_csv(self, lignes):
        dossier = tempfile.mkdtemp()
        chemin = os.path.join(dossier, "doublons.csv")
        with open(chemin, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(ENTETES)
            for l in lignes:
                w.writerow(l)
        return chemin, os.path.join(dossier, "rapport.csv")

    def lire_rapport(self, chemin):
        with open(chemin, encoding="utf-8-sig") as f:
            return list(csv.DictReader(f, delimiter=";"))

    def setUp(self):
        self.csv, self.rapport = self.ecrire_csv([
            ["G-001", "Certain", DOMAINE, "Oui", "1", "", "Sophie", "", "s.duchene@archimeet.fr",
             "", "", "", "", "2023-07-18 08:22", "", ""],
            ["G-001", "Certain", DOMAINE, "", "2", "", "", "", "", "", "", "", "",
             "2023-11-13 11:03", "", ""],
            ["G-001", "Certain", DOMAINE, "", "3", "", "", "", "", "", "", "", "",
             "2023-12-15 10:35", "", ""],
        ])
        self.client = FauxHubSpot({
            "1": fiche("1", "2023-07-18", prenom="S", nom="Duchene",
                       email="s.duchene@archimeet.fr", telephone="06 33 56 45 94",
                       entreprise="Archimeet"),
            "2": fiche("2", "2023-11-13", prenom="Sophie", nom="DUCHENE",
                       telephone="+33633564594", entreprise="Archimeet", poste="Architecte",
                       id_entreprise="55"),
            "3": fiche("3", "2023-12-15", email="sduchene@archimeet.fr", en_echec=True,
                       entreprise="Archimeet"),
        })

    def test_simulation_ne_modifie_rien(self):
        compteur = fus.traiter(self.csv, self.rapport, client=self.client, journal=lambda *a: 0)
        self.assertEqual(compteur, {"SIMULATION": 1})
        self.assertEqual(self.client.appels, [])
        ligne = self.lire_rapport(self.rapport)[0]
        self.assertEqual((ligne["Prénom"], ligne["Nom"]), ("Sophie", "Duchene"))
        self.assertEqual(ligne["Email principal"], "s.duchene@archimeet.fr")
        self.assertEqual(ligne["Intitulé du poste"], "Architecte")

    def test_fusion_puis_corrections(self):
        compteur = fus.traiter(self.csv, self.rapport, client=self.client, reel=True,
                               journal=lambda *a: 0)
        self.assertEqual(compteur, {"FUSIONNÉ": 1})
        merges = [a for a in self.client.appels if a[0] == "merge"]
        self.assertEqual(merges, [("merge", "1", "2"), ("merge", "9000", "3")])
        patch = next(a for a in self.client.appels if a[0] == "patch")
        self.assertEqual(patch[1], "9001")
        self.assertEqual(patch[2]["firstname"], "Sophie")
        self.assertEqual(patch[2]["jobtitle"], "Architecte")
        self.assertNotIn("lastname", patch[2])
        self.assertIn(("assoc", "9001", "55"), self.client.appels)
        self.assertEqual(self.lire_rapport(self.rapport)[0]["ID final"], "9001")

        # Relance : le groupe est reconnu comme déjà fusionné, rien n'est refait.
        self.client.appels.clear()
        compteur = fus.traiter(self.csv, self.rapport, client=self.client, reel=True,
                               journal=lambda *a: 0)
        self.assertEqual(compteur, {"DÉJÀ FUSIONNÉ": 1})
        self.assertEqual(self.client.appels, [])

    def test_filtre_groupes(self):
        compteur = fus.traiter(self.csv, self.rapport, client=self.client, filtre={"G-999"},
                               journal=lambda *a: 0)
        self.assertEqual(compteur, {})


if __name__ == "__main__":
    unittest.main()
