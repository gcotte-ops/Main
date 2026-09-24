# Enrichissement SIREN / SIRET des entreprises HubSpot

`enrichissement_siren_siret.py` complète les colonnes SIREN et SIRET d'un export CSV
d'entreprises HubSpot à partir de l'[Annuaire des Entreprises](https://annuaire-entreprises.data.gouv.fr/).

Python 3.8+ suffit, sans aucune dépendance à installer.

```bash
python enrichissement_siren_siret.py entreprises.csv            # -> entreprises_complete.csv + entreprises_rapport.csv
python enrichissement_siren_siret.py entreprises.csv --envoyer  # + envoi par email à gcotte@alter-watt.fr
```

- Les lignes où le SIREN **et** le SIRET sont déjà remplis sont ignorées, ainsi que les entreprises hors France.
- Arbre de décision appliqué à chaque autre ligne :
  1. Recherche du nom : nom + adresse identiques → **TROUVÉ**, SIREN + SIRET écrits.
  2. Sinon, recherche reformulée « nom + adresse postale + ville » → **TROUVÉ** si nom + adresse concordent.
  3. Sinon, si le nom a été trouvé mais à une autre adresse → **ADRESSE CORRIGÉE** : SIREN + SIRET du siège écrits,
     adresse et ville HubSpot remplacées par celles de l'Annuaire (`--sans-correction-adresse` pour ne pas y toucher).
  4. Sinon → **RECHERCHE INTERNET** (rien n'est écrit).
  - Entreprise cessée → **FERMÉE** : fiche à supprimer ou entreprise radiée (INPI).
- Le rapport indique pour chaque ligne le statut, l'action à mener, la recherche effectuée, l'ancienne et la
  nouvelle adresse, et le lien vers la fiche de l'Annuaire.
- Colonnes détectées automatiquement (`Record ID`, `Nom de l'entreprise`, `Adresse`, `Ville`, `SIREN`, `SIRET`...) ;
  sinon `--col-nom "..."`, `--col-adresse "..."`, etc.
- Séparateur (`,` ou `;`) et encodage (UTF-8 / Windows) conservés : le CSV complété peut être réimporté dans HubSpot.

Envoi d'email : définir `SMTP_HOST`, `SMTP_PORT` (587 par défaut), `SMTP_USER`, `SMTP_PASSWORD`
(pour Google Workspace : `smtp.gmail.com` et un mot de passe d'application).

Tests hors ligne : `python -m unittest test_enrichissement_siren_siret`
