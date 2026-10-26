#!/usr/bin/env python3
"""
Outils de la routine hebdomadaire de dédoublonnage HubSpot (voir DEDOUBLONNAGE_RECURRENT.md).

Les connecteurs (HubSpot, Google Drive, Google Sheets) répondent en JSON ; quand la réponse est
longue, Claude Code l'enregistre dans un fichier. Ces commandes préparent les requêtes et
transforment ces réponses en fichiers utilisables par les scripts.

  python outils_routine.py acces                              # FUSION=oui/non : jeton et API

Lecture de toute la base HubSpot par le connecteur (query_crm_data : 500 fiches au plus par
requête, fenêtre de 10 000 résultats) : par tours de 20 pages lancées en parallèle.

  python outils_routine.py requetes entreprises [--borne ID]  # 20 requêtes SQL du tour
  python outils_routine.py borne entreprises DOSSIER --depuis ID  # plus grand ID lu, tour complet ?
  python outils_routine.py fin entreprises                    # requête des 500 derniers ID
  python outils_routine.py collecter entreprises base_entreprises.jsonl DOSSIER
  python outils_routine.py somme entreprises                  # requête de contrôle (somme des ID)
  python outils_routine.py controle entreprises base_entreprises.jsonl SOMME

  python outils_routine.py fichier REPONSE.json SORTIE        # Drive (download_file_content) :
                                                              # contenu base64 -> fichier
  python outils_routine.py valeurs REPONSE.json SORTIE.csv    # Sheets (get_values) : valeurs ->
                                                              # CSV « ; » (mémoire, GT 3.0)
  python outils_routine.py lignes DECISIONS.csv               # CSV écrit par --memoriser ->
                                                              # lignes JSON à ajouter à la feuille
  python outils_routine.py bilan CLASSEUR.xlsx [--rapport FUSION.csv]  # compte rendu (email)
  python outils_routine.py journal FUSION.csv --classeur CLASSEUR.xlsx --origine TEXTE
                                                              # fusions faites -> lignes JSON du
                                                              # journal (sheets_append_values)

Aucune dépendance externe : uniquement la bibliothèque standard Python (3.8+).
"""

import argparse
import base64
import csv
import json
import math
import os
import sys
import zipfile

# Propriétés lues par le connecteur HubSpot (hs_additional_emails est masquée en SQL).
OBJETS = {
    "entreprises": ("COMPANY", "0-2", [
        "hs_object_id", "name", "domain", "website", "phone", "city", "zip", "address", "siren",
        "siret", "type_de_decideur", "hubspot_owner_id", "num_associated_contacts",
        "num_associated_deals", "industry", "createdate"]),
    "contacts": ("CONTACT", "0-1", [
        "hs_object_id", "firstname", "lastname", "email", "phone", "mobilephone", "jobtitle",
        "company", "associatedcompanyid", "hubspot_owner_id", "createdate",
        "hs_email_hard_bounce_reason_enum", "notes_last_updated"]),
}
TAILLE_PAGE = 500          # maximum du connecteur
PAGES_PAR_TOUR = 20        # 20 x 500 = fenêtre de 10 000 résultats de la recherche HubSpot


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


def requetes(objet, borne=0):
    """Requêtes SQL d'un tour : 20 pages de 500 fiches d'ID supérieur à borne."""
    table, _, proprietes = OBJETS[objet]
    sql = "SELECT {} FROM {}".format(", ".join(proprietes), table)
    if borne:
        sql += " WHERE hs_object_id > {}".format(borne)
    sql += " ORDER BY hs_object_id ASC LIMIT {}".format(TAILLE_PAGE)
    return [sql + (" OFFSET {}".format(k * TAILLE_PAGE) if k else "")
            for k in range(PAGES_PAR_TOUR)]


def requete_fin(objet):
    """Les 500 fiches d'ID le plus élevé : couvre la dernière page, trop courte pour être
    enregistrée dans un fichier."""
    table, _, proprietes = OBJETS[objet]
    return "SELECT {} FROM {} ORDER BY hs_object_id DESC LIMIT {}".format(
        ", ".join(proprietes), table, TAILLE_PAGE)


def requete_somme(objet):
    """Somme des ID de la base : contrôle que la lecture n'a perdu aucune fiche."""
    return "SELECT SUM(hs_object_id) FROM {}".format(OBJETS[objet][0])


def fichiers(chemins):
    resultat = []
    for chemin in chemins:
        if os.path.isdir(chemin):
            resultat += sorted(os.path.join(chemin, f) for f in os.listdir(chemin)
                               if os.path.isfile(os.path.join(chemin, f)))
        elif os.path.isfile(chemin):
            resultat.append(chemin)
    return resultat


def lecture(chemin, objet):
    """Propriétés des fiches de l'objet dans un fichier (réponse enregistrée du connecteur ou
    .jsonl écrit par « collecter »), dans l'ordre du fichier ; [] si le fichier n'en contient
    pas."""
    try:
        if chemin.endswith(".jsonl"):
            with open(chemin, encoding="utf-8") as f:
                lus = [json.loads(l) for l in f if l.strip()]
            if lus and lus[0].get("_objet") != objet:
                return []
            lus = [{k: v for k, v in p.items() if k != "_objet"} for p in lus]
        else:
            donnees = charger(chemin)
            if not isinstance(donnees, dict) or "results" not in donnees:
                return []
            lus = []
            for r in donnees["results"]:
                contenu = r.get("content") if isinstance(r, dict) else None
                enregistrement = json.loads(contenu) if isinstance(contenu, str) else r
                if enregistrement.get("objectTypeId") == OBJETS[objet][1]:
                    lus.append(enregistrement.get("properties", {}))
    except (ValueError, OSError, AttributeError):
        return []
    return [p for p in lus if str(p.get("hs_object_id") or "").isdigit()]


def enregistrements(chemins, objet):
    """Propriétés des fiches de l'objet dans les réponses du connecteur HubSpot enregistrées
    (fichiers ou dossiers), ou dans un fichier .jsonl écrit par « collecter ». Une fiche lue
    plusieurs fois n'est gardée qu'une fois."""
    fiches = {}
    for chemin in fichiers(chemins):
        for p in lecture(chemin, objet):
            fiches[str(p["hs_object_id"])] = p
    return [fiches[i] for i in sorted(fiches, key=int)]


def decroissant(ids):
    """Réponse de la requête « fin » (ID décroissants) : elle ne compte pas dans la borne."""
    return len(ids) > 1 and all(a > b for a, b in zip(ids, ids[1:]))


def borne(chemins, objet, depuis=0):
    """(plus grand ID lu, nombre de fiches lues, nombre de fiches d'ID > depuis). La borne et le
    nombre de fiches du tour ignorent la requête « fin » : lancée avec un tour, elle ferait
    sauter la borne au-delà des fiches que ce tour n'a pas encore lues."""
    tous, montants = set(), set()
    for chemin in fichiers(chemins):
        ids = [int(p["hs_object_id"]) for p in lecture(chemin, objet)]
        tous.update(ids)
        if not decroissant(ids):
            montants.update(ids)
    return max(montants, default=0), len(tous), sum(1 for i in montants if i > depuis)


def tour_complet(lues_ce_tour):
    """Faut-il un tour de plus ? Oui dès que toutes les pages lues sont pleines (multiple de
    500), quel que soit le nombre de pages lancées : seule une page incomplète, ou un tour vide,
    marque la fin de la base. Au pire, un tour de plus ne renvoie rien."""
    return lues_ce_tour > 0 and lues_ce_tour % TAILLE_PAGE == 0


def ecart_admis(somme):
    """HubSpot calcule la somme en virgule flottante : au-delà de 2^53 (environ 9 × 10^15), elle
    est arrondie à quelques unités près. Écart toléré : 4 fois le pas des nombres à virgule
    flottante à cette hauteur (0 en dessous de 2^53, où le calcul est exact)."""
    somme = abs(int(somme))
    return 0 if somme < 2 ** 53 else 4 * 2 ** (math.frexp(somme)[1] - 53)


def controle(chemins, objet, somme):
    """(lecture complète ?, fiches lues, somme de leurs ID) ; somme : réponse de requete_somme.
    Une page de 500 fiches perdue fait un écart bien plus grand que l'arrondi toléré."""
    ids = [int(p["hs_object_id"]) for p in enregistrements(chemins, objet)]
    return abs(sum(ids) - int(somme)) <= ecart_admis(somme), len(ids), sum(ids)


def collecter(chemins, objet, sortie):
    """Fiches lues, une par ligne (JSON), pour --depuis-mcp des scripts de détection."""
    lus = enregistrements(chemins, objet)
    with open(sortie, "w", encoding="utf-8") as f:
        for p in lus:
            f.write(json.dumps(dict(p, _objet=objet), ensure_ascii=False) + "\n")
    return len(lus)


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


def acces():
    """(fusion possible ?, message) : jeton HUBSPOT_TOKEN présent, API joignable, droits de
    lecture des contacts, des entreprises et des propriétaires. La valeur du jeton n'est jamais
    affichée. Les droits d'écriture ne se vérifient qu'à la fusion."""
    jeton = os.environ.get("HUBSPOT_TOKEN", "").strip()
    if not jeton:
        return False, ("variable HUBSPOT_TOKEN absente : l'ajouter aux variables d'environnement "
                       "de l'environnement cloud (nouvelle session nécessaire)")
    import fusion_doublons_hubspot as fc
    client = fc.ClientHubSpot(jeton)
    probleme = fc.verifier_jeton(client, jeton)
    if probleme:
        if "injoignable" in probleme:
            probleme += " ; vérifier que api.hubapi.com est dans les domaines autorisés"
        return False, probleme
    try:
        client.requete("GET", "/crm/v3/objects/companies?limit=1")
    except fc.ErreurHubSpot as e:
        return False, "lecture des entreprises refusée ({}) : droit crm.objects.companies.read".format(e)
    try:
        client.proprietaires_actifs(strict=True)
    except fc.ErreurHubSpot as e:
        return False, "lecture des propriétaires refusée ({}) : droit crm.objects.owners.read".format(e)
    return True, "API HubSpot joignable, jeton accepté (contacts, entreprises, propriétaires)"


PORTAIL = "20368543"
LIEN = "https://app-eu1.hubspot.com/contacts/{portail}/record/{type}/{id}"


def lire_rapport(chemin):
    """{groupe: (statut, remarques, ID final)} d'un rapport de fusion (CSV « ; »)."""
    if not chemin or not os.path.isfile(chemin):
        return {}
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        return {l.get("Groupe", ""): (l.get("Statut", ""), l.get("Remarques", ""),
                                      l.get("ID final", ""))
                for l in csv.DictReader(f, delimiter=";")}


def bilan(classeur, rapport=None, portail=PORTAIL):
    """Texte du compte rendu : groupes Certain (avec le statut de la fusion si un rapport est
    donné) et groupes Probable, fiche à garder en premier, avec les liens HubSpot."""
    import fusion_entreprises_hubspot as fe
    rangs = fe.lire_xlsx(classeur)
    contacts = bool(rangs) and "Prénom" in rangs[0]
    type_objet = "0-1" if contacts else "0-2"
    statuts = lire_rapport(rapport)
    groupes = {}
    for l in rangs:
        g = str(l.get("Groupe") or "").strip()
        if g and str(l.get("ID HubSpot") or "").strip():
            groupes.setdefault(g, []).append(l)

    def nom(l):
        if contacts:
            texte = " ".join(str(l.get(c) or "").strip() for c in ("Prénom", "Nom")).strip()
            return texte or str(l.get("E-mail") or "").strip()
        return (str(l.get("Nom de l’entreprise") or "").strip()
                or str(l.get("Nom de domaine") or "").strip() or "(sans nom)")

    sortie = []
    for niveau, titre in (("Certain", "Doublons certains (fusion automatique)"),
                          ("Probable", "Doublons probables (à vérifier, fusion à la main)")):
        choisis = [(g, ls) for g, ls in groupes.items()
                   if str(ls[0].get("Niveau") or "").strip() == niveau]
        sortie.append("{} : {}".format(titre, len(choisis)))
        for g, ls in choisis:
            ls = sorted(ls, key=lambda l: str(l.get("Racine suggérée") or "").lower() != "oui")
            entete = "- {} {}".format(g, nom(ls[0]))
            final = ""
            if g in statuts:
                statut, remarques, final = statuts[g]
                entete += " : {}".format(statut) + (" ({})".format(remarques) if remarques else "")
            sortie.append(entete)
            motif = str(ls[0].get("Raison du rapprochement") or "").strip()
            if motif:
                sortie.append("    motif : " + motif)
            for k, l in enumerate(ls):
                i = str(l.get("ID HubSpot")).strip()
                sortie.append("    {} {} {} {}".format(
                    "garder" if k == 0 else "doublon", i, nom(l),
                    LIEN.format(portail=portail, type=type_objet, id=i)))
            if final and statuts[g][0].startswith("FUSIONN"):
                sortie.append("    fiche fusionnée {} {}".format(
                    final, LIEN.format(portail=portail, type=type_objet, id=final)))
    return "\n".join(sortie)


ENTETES_JOURNAL = ["Horodatage", "Objet", "Origine", "Groupe", "Nom", "Fiches fusionnées",
                   "ID fiche finale", "Lien fiche finale", "Statut", "Motif", "Remarques"]


def journal(rapport, classeur=None, origine="", heure=""):
    """Lignes du journal des fusions (une par groupe fusionné), pour sheets_append_values.
    Rapport sans colonne « Horodatage » (rapports anciens) : heure donnée, sinon date du
    fichier."""
    with open(rapport, encoding="utf-8-sig", newline="") as f:
        rangs = list(csv.DictReader(f, delimiter=";"))
    if not heure:
        import fusion_doublons_hubspot as fc
        heure = fc.horodatage(os.path.getmtime(rapport))
    motifs = {}
    if classeur:
        import fusion_entreprises_hubspot as fe
        for l in fe.lire_xlsx(classeur):
            g = str(l.get("Groupe") or "").strip()
            motifs.setdefault(g, str(l.get("Raison du rapprochement") or "").strip())
    sortie = []
    for l in rangs:
        if not l.get("Statut", "").startswith("FUSIONN"):          # fusions faites seulement
            continue
        contacts = "Prénom" in l
        nom = (" ".join(x for x in (l.get("Prénom", "").strip(), l.get("Nom", "").strip()) if x)
               if contacts else l.get("Nom", "").strip())
        sortie.append([
            l.get("Horodatage") or heure, "Contact" if contacts else "Entreprise", origine,
            l.get("Groupe", ""), nom, l.get("Fiches du groupe", ""), l.get("ID final", ""),
            l.get("Lien HubSpot", ""), l.get("Statut", ""), motifs.get(l.get("Groupe", ""), ""),
            l.get("Remarques", "")])
    return sortie


def lignes(decisions):
    """Lignes d'un CSV écrit par --memoriser (sans l'en-tête), en JSON, pour
    sheets_append_values."""
    with open(decisions, encoding="utf-8-sig", newline="") as f:
        rangs = list(csv.reader(f, delimiter=";"))
    return rangs[1:]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Outils de la routine de dédoublonnage.")
    sous = parser.add_subparsers(dest="commande", required=True)
    sous.add_parser("acces", help="la fusion par l'API est-elle possible ? (FUSION=oui/non)")
    p = sous.add_parser("requetes", help="requêtes SQL d'un tour de lecture")
    p.add_argument("objet", choices=sorted(OBJETS))
    p.add_argument("--borne", type=int, default=0, help="plus grand ID déjà lu")
    p = sous.add_parser("fin", help="requête des 500 derniers ID")
    p.add_argument("objet", choices=sorted(OBJETS))
    p = sous.add_parser("somme", help="requête de la somme des ID (contrôle)")
    p.add_argument("objet", choices=sorted(OBJETS))
    p = sous.add_parser("controle", help="la base collectée est-elle complète ?")
    p.add_argument("objet", choices=sorted(OBJETS))
    p.add_argument("base", help="fichier .jsonl écrit par « collecter »")
    p.add_argument("somme", help="somme des ID renvoyée par la requête « somme »")
    p = sous.add_parser("borne", help="plus grand ID lu dans les réponses enregistrées")
    p.add_argument("objet", choices=sorted(OBJETS))
    p.add_argument("chemins", nargs="+")
    p.add_argument("--depuis", type=int, default=0, help="borne du tour qui vient d'être lu")
    p = sous.add_parser("collecter", help="réponses enregistrées -> fichier .jsonl")
    p.add_argument("objet", choices=sorted(OBJETS))
    p.add_argument("sortie")
    p.add_argument("chemins", nargs="+")
    p = sous.add_parser("fichier", help="réponse Drive -> fichier")
    p.add_argument("reponse")
    p.add_argument("sortie")
    p = sous.add_parser("valeurs", help="réponse Sheets -> CSV")
    p.add_argument("reponse")
    p.add_argument("sortie")
    p = sous.add_parser("lignes", help="CSV de décisions -> lignes JSON")
    p.add_argument("decisions")
    p = sous.add_parser("journal", help="rapport de fusion -> lignes JSON du journal")
    p.add_argument("rapport")
    p.add_argument("--classeur", help="classeur de détection (motif du rapprochement)")
    p.add_argument("--origine", default="", help="« Routine hebdomadaire », « Passage manuel »…")
    p.add_argument("--heure", default="", help="horodatage des rapports anciens, sans colonne")
    p = sous.add_parser("bilan", help="compte rendu d'un classeur de détection (et du rapport "
                                      "de fusion)")
    p.add_argument("classeur")
    p.add_argument("--rapport", help="rapport de fusion (.csv)")
    p.add_argument("--portail", default=PORTAIL)
    args = parser.parse_args(argv)
    if args.commande == "acces":
        possible, message = acces()
        print("FUSION={} : {}".format("oui" if possible else "non", message))
        return 0 if possible else 1
    if args.commande == "requetes":
        print("\n".join(requetes(args.objet, args.borne)))
    elif args.commande == "fin":
        print(requete_fin(args.objet))
    elif args.commande == "somme":
        print(requete_somme(args.objet))
    elif args.commande == "controle":
        complet, total, somme = controle([args.base], args.objet, args.somme)
        if complet:
            ecart = abs(somme - int(args.somme))
            print("lecture complète : {} fiches".format(total) + (
                " (écart de {} sur la somme : arrondi du calcul de HubSpot)".format(ecart)
                if ecart else ""))
        else:
            print("lecture INCOMPLÈTE : {} fiches lues, somme des ID {} au lieu de {}".format(
                total, somme, args.somme))
            return 1
    elif args.commande == "borne":
        plus_grand, total, tour = borne(args.chemins, args.objet, args.depuis)
        complet = tour_complet(tour)
        print("borne={} fiches_lues={} lues_ce_tour={} tour_complet={}".format(
            plus_grand, total, tour, "oui" if complet else "non"))
        print("suite : " + ("nouveau tour avec --borne {}".format(plus_grand) if complet else
                            "lancer la requête « fin », puis collecter"))
    elif args.commande == "collecter":
        print("{} : {} fiches".format(args.sortie, collecter(args.chemins, args.objet,
                                                              args.sortie)))
    elif args.commande == "fichier":
        print("{} écrit ({})".format(args.sortie, fichier(args.reponse, args.sortie)))
    elif args.commande == "valeurs":
        print("{} écrit : {} lignes".format(args.sortie, valeurs(args.reponse, args.sortie)))
    elif args.commande == "bilan":
        print(bilan(args.classeur, args.rapport, args.portail))
    elif args.commande == "journal":
        print(json.dumps(journal(args.rapport, args.classeur, args.origine, args.heure),
                         ensure_ascii=False))
    else:
        print(json.dumps(lignes(args.decisions), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
