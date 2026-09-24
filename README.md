# Enrichissement SIREN / SIRET des entreprises HubSpot

`enrichissement_siren_siret.py` complète les colonnes SIREN et SIRET d'un export CSV
d'entreprises HubSpot à partir de l'[Annuaire des Entreprises](https://annuaire-entreprises.data.gouv.fr/).

Python 3.8+ suffit, sans aucune dépendance à installer.

```bash
python enrichissement_siren_siret.py entreprises.csv            # -> entreprises_complete.csv + entreprises_rapport.csv
python enrichissement_siren_siret.py entreprises.csv --envoyer  # + envoi par email à gcotte@alter-watt.fr
```

- Les lignes où le SIREN **et** le SIRET sont déjà remplis sont ignorées.
- Pour chaque autre ligne : recherche du nom, puis examen des résultats dans l'ordre
  (1er, 2e, ...) jusqu'à en trouver un dont le **nom** et l'**adresse** correspondent.
  Le SIRET retenu est celui de l'établissement situé à l'adresse HubSpot (siège ou établissement secondaire).
- Si le SIREN est déjà connu, la recherche se fait par SIREN et seul le SIRET est complété.
- Seules les correspondances sûres sont écrites. Le rapport indique pour chaque ligne :
  `TROUVÉ`, `À VÉRIFIER` (pas de rue dans HubSpot, établissement fermé...) ou `NON TROUVÉ`, avec le motif et le lien vers la fiche de l'Annuaire.
  `--remplir-a-verifier` écrit aussi les cas `À VÉRIFIER`.
- Colonnes détectées automatiquement (`Record ID`, `Nom de l'entreprise`, `Adresse`, `Ville`, `SIREN`, `SIRET`...) ;
  sinon `--col-nom "..."`, `--col-adresse "..."`, etc.
- Séparateur (`,` ou `;`) et encodage (UTF-8 / Windows) conservés : le CSV complété peut être réimporté dans HubSpot.

Envoi d'email : définir `SMTP_HOST`, `SMTP_PORT` (587 par défaut), `SMTP_USER`, `SMTP_PASSWORD`
(pour Google Workspace : `smtp.gmail.com` et un mot de passe d'application).

Tests hors ligne : `python -m unittest test_enrichissement_siren_siret`
