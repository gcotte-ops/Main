#!/usr/bin/env python3
"""
Contexte des échanges : départager les doublons de contacts « Probable » par leurs emails HubSpot.

Deux fiches au même prénom et au même nom (doublon Probable : entreprises différentes, aucun
autre lien fort) désignent la même personne quand leurs échanges se recoupent :
  - toutes deux ont échangé avec la même personne d'Alter Watt (adresse d'un domaine interne) ;
  - et l'organisation de l'email de l'une apparaît dans les échanges de l'autre : une adresse de
    son domaine (ou d'un domaine de la même organisation), ou un correspondant dont l'adresse
    porte le nom de cette organisation (« n.brisak@… » pour une fiche en « @brisak.org »).

  python contexte_contacts.py doublons_contacts.xlsx            # passe en Certain ce qui l'est
  python contexte_contacts.py doublons_contacts.xlsx --apercu   # n'écrit rien

Le classeur est modifié sur place (Niveau « Certain », raison complétée). Les mêmes règles sont
appliquées par fusion_doublons_hubspot.py dans son contrôle avant fusion. Affiche ensuite les
doublons Probable restants dont les fiches ont des entreprises différentes : à vérifier sur les
expériences LinkedIn (Sales Navigator, en session).

Jeton : variable d'environnement HUBSPOT_TOKEN (droit sales-email-read pour lire les emails).
"""

import argparse
import os
import re
import sys

import detection_contacts_hubspot as dc
import fusion_doublons_hubspot as fc
import normalisation as nz

DOMAINES_INTERNES = {"alter-watt.com"}
EMAILS_LUS = 200                    # par fiche, les plus récents
PROPRIETES_EMAIL = ["hs_email_from_email", "hs_email_to_email", "hs_email_cc_email",
                    "hs_email_bcc_email"]


def adresses(texte):
    return {a.lower() for a in re.findall(r"[\w.+'-]+@[\w-]+(?:\.[\w-]+)+", texte or "")}


def correspondants(client, id_contact, limite=EMAILS_LUS):
    """Adresses (expéditeur, destinataires, copies) des emails HubSpot associés au contact."""
    vues, apres = set(), None
    while True:
        corps = {"filterGroups": [{"filters": [{"propertyName": "associations.contact",
                                                "operator": "EQ", "value": str(id_contact)}]}],
                 "sorts": [{"propertyName": "hs_timestamp", "direction": "DESCENDING"}],
                 "properties": PROPRIETES_EMAIL, "limit": 100}
        if apres:
            corps["after"] = apres
        rep = client.requete("POST", "/crm/v3/objects/emails/search", corps)
        for email in rep.get("results", []):
            for prop in PROPRIETES_EMAIL:
                vues |= adresses(email.get("properties", {}).get(prop))
        limite -= len(rep.get("results", []))
        apres = rep.get("paging", {}).get("next", {}).get("after")
        if not apres or limite <= 0:
            break
    return vues


def internes(adresses_):
    return {a for a in adresses_ if nz.domaine_email(a) in DOMAINES_INTERNES}


def organisation_citee(fiche, adresses_autre):
    """Adresse des échanges de l'autre fiche qui désigne l'organisation de cette fiche."""
    propres = set(dc.normes(fiche).emails)
    domaines = dc.normes(fiche).domaines_pro - DOMAINES_INTERNES
    mots = {m for d in domaines for m in nz.mots_domaine(d)}
    for adresse in sorted(adresses_autre - propres):
        domaine = nz.domaine_email(adresse)
        if domaine in DOMAINES_INTERNES:
            continue
        if domaine in domaines or any(nz.domaines_apparentes(domaine, d) for d in domaines):
            return adresse
        if set(re.split(r"[._+'-]+", nz.local_email(adresse))) & mots:
            return adresse
    return ""


def lien_par_echanges(a, b, adresses_a, adresses_b):
    """Raison (texte) si les échanges des deux fiches désignent la même personne, sinon ""."""
    communs = internes(adresses_a) & internes(adresses_b)
    if not communs:
        return ""
    for fiche, autres in ((b, adresses_a), (a, adresses_b)):
        cite = organisation_citee(fiche, autres)
        if cite:
            return ("contexte des échanges : même interlocuteur Alter Watt ({}) ; l'organisation "
                    "de {} apparaît dans les échanges de l'autre fiche ({})".format(
                        ", ".join(sorted(communs)), dc.normes(fiche).email or fiche.id, cite))
    return ""


def organisation(fiche):
    """Entreprise de la fiche, à défaut le domaine professionnel de son email."""
    n = dc.normes(fiche)
    return fc.normaliser(fiche.entreprise) or next(iter(sorted(n.domaines_pro)), "")


def organisations_differentes(a, b):
    """Même personne possible (prénom et nom compatibles, aucune adresse générique), deux
    organisations différentes : à vérifier sur les expériences LinkedIn."""
    p = dc.evaluer(a, b)
    if p.bloquee or p.niveau != dc.PROBABLE or not p.liens & {"meme_personne", "prenom_compatible"}:
        return False
    if any(f.email and nz.est_generique(f.email) for f in (a, b)):
        return False
    if p.liens & {"meme_entreprise", "meme_domaine_pro", "domaine_apparente", "poste_designe"}:
        return False
    oa, ob = organisation(a), organisation(b)
    if "entreprises_differentes" in p.liens:
        return True
    da, db = dc.normes(a).domaines_pro, dc.normes(b).domaines_pro
    return bool(oa and ob and oa != ob and da and db and not da & db)


def eligible(p):
    """Paire Probable au même prénom et nom, sans blocage : le contexte peut la départager."""
    return p.niveau == dc.PROBABLE and "meme_personne" in p.liens and not p.bloquee


def confirmer(client, a, b, cache=None):
    """Raison si la paire Probable (a, b) est confirmée par le contexte des échanges."""
    p = dc.evaluer(a, b)
    if not eligible(p):
        return ""
    cache = {} if cache is None else cache
    for f in (a, b):
        if f.id not in cache:
            cache[f.id] = correspondants(client, f.id)
    return lien_par_echanges(a, b, cache[a.id], cache[b.id])


# --------------------------------------------------------------------------- #
# Classeur de détection
# --------------------------------------------------------------------------- #

def traiter_classeur(chemin, client, ecrire=True, journal=print):
    import openpyxl
    wb = openpyxl.load_workbook(chemin)
    ws = wb["Doublons"]
    entetes = [c.value for c in ws[1]]
    col = {nom: i for i, nom in enumerate(entetes)}
    groupes = {}
    for ligne in ws.iter_rows(min_row=2):
        g = ligne[col["Groupe"]].value
        if g and ligne[col["Niveau"]].value == "Probable":
            groupes.setdefault(g, []).append(ligne)
    promus, a_verifier, cache = [], [], {}
    for g, lignes in groupes.items():
        if len(lignes) != 2:
            continue
        fiches = [client.fiche(str(l[col["ID HubSpot"]].value).strip()) for l in lignes]
        if None in fiches or fiches[0].id == fiches[1].id:
            continue
        raison = confirmer(client, fiches[0], fiches[1], cache)
        if raison:
            promus.append((g, raison))
            for l in lignes:
                l[col["Niveau"]].value = dc.CERTAIN
                l[col["Raison du rapprochement"]].value = "{} + {}".format(
                    l[col["Raison du rapprochement"]].value, raison)
            journal("{} Certain : {}".format(g, raison))
        elif organisations_differentes(*fiches):
            a_verifier.append((g, fiches))
    if ecrire and promus:
        wb.save(chemin)
    return promus, a_verifier


def main(argv=None):
    parser = argparse.ArgumentParser(description="Contexte des échanges des doublons Probable.")
    parser.add_argument("classeur", help="doublons_contacts.xlsx de detection_contacts_hubspot.py")
    parser.add_argument("--apercu", action="store_true", help="n'écrit rien dans le classeur")
    args = parser.parse_args(argv)
    jeton = os.environ.get("HUBSPOT_TOKEN")
    if not jeton:
        parser.error("définir HUBSPOT_TOKEN")
    client = fc.ClientHubSpot(jeton.strip())
    promus, a_verifier = traiter_classeur(args.classeur, client, ecrire=not args.apercu)
    print("Passés en Certain par le contexte des échanges : {}".format(len(promus)))
    print("Probable, entreprises différentes, à vérifier sur LinkedIn (en session) : {}".format(
        len(a_verifier)))
    for g, fiches in a_verifier:
        print("  {} {} : {}".format(g, fiches[0].prenom + " " + fiches[0].nom, " / ".join(
            "{} ({})".format(f.entreprise or organisation(f) or "?", f.id) for f in fiches)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
