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
  0. SIRET déjà renseigné → recherche **par SIRET** (jamais par le nom) : adresse identique → **TROUVÉ** (SIREN écrit) ;
     adresse différente → **ADRESSE À VÉRIFIER** (SIREN écrit, adresse laissée telle quelle).
  1. Recherche du nom (ou du SIREN s'il est connu) : nom + adresse identiques → **TROUVÉ**, SIREN + SIRET écrits.
  2. Sinon, recherche « nom + ville du CSV » : nom + adresse identiques → **TROUVÉ** ;
     1er résultat = même entreprise, en activité, à une autre adresse → **ADRESSE CORRIGÉE** : SIREN + SIRET écrits,
     adresse et ville HubSpot remplacées (`--sans-correction-adresse` pour ne pas y toucher).
     Fiche **sans adresse** : une seule entreprise de ce nom avec un établissement actif dans la ville → **TROUVÉ (VILLE)**
     (adresse vide remplie si l'entreprise sort en 1er résultat) ; plusieurs homonymes dans la ville → rien n'est écrit.
  3. Sinon → **RECHERCHE INTERNET** (rien n'est écrit, adresse non modifiée).
- Établissements scolaires (catégorie « Enseignement… » ou nom d'école) : noms nettoyés (« DAH - », « (fermé) », suffixe
  « - Ville »), chaque partie du nom essayée, comparaison sur les mots distinctifs (« OGEC École Sainte-Anne » =
  « Organisme de gestion… Sainte Anne »), et seules les associations / entités d'enseignement (NAF 85) sont retenues.
- Adresses génériques (même adresse sur au moins 3 fiches de villes différentes) : ignorées.
  - Entreprise cessée → **FERMÉE** : fiche à supprimer ou entreprise radiée (INPI).
  - SIRET qui ne commence pas par le SIREN → **INCOHÉRENT** (signalé, non modifié).
- L'adresse n'est modifiée que dans le cas **ADRESSE CORRIGÉE**.
- Le CSV complété contient une colonne **« Statut enrichissement »** juste à droite de « SIRET » : `Trouvé`,
  `À vérifier` (SIREN/SIRET écrits mais à contrôler) ou `Fermée`, vide quand rien n'a été écrit. Elle est réutilisée
  (pas dupliquée) si on relance le script sur un CSV déjà complété.
- Le rapport indique pour chaque ligne le statut, l'action à mener, la recherche effectuée, l'ancienne et la
  nouvelle adresse, et le lien vers la fiche de l'Annuaire.
- Colonnes détectées automatiquement (`Record ID`, `Nom de l'entreprise`, `Adresse`, `Ville`, `SIREN`, `SIRET`...) ;
  sinon `--col-nom "..."`, `--col-adresse "..."`, etc.
- Séparateur (`,` ou `;`) et encodage (UTF-8 / Windows) conservés : le CSV complété peut être réimporté dans HubSpot.

Envoi d'email : définir `SMTP_HOST`, `SMTP_PORT` (587 par défaut), `SMTP_USER`, `SMTP_PASSWORD`
(pour Google Workspace : `smtp.gmail.com` et un mot de passe d'application).

Tests hors ligne : `python -m unittest test_enrichissement_siren_siret`

# Fusion des contacts HubSpot en doublon certain

`fusion_doublons_hubspot.py` fusionne les contacts listés dans l'onglet « Doublons certains »
(`doublons_potentiels_hubspot.xlsx` exporté en CSV) : les fiches d'un même groupe (G-001, G-002…)
sont fusionnées en une seule, puis la fiche obtenue est corrigée.

```bash
python fusion_doublons_hubspot.py doublons.csv --hors-ligne            # aperçu à partir du seul CSV
python fusion_doublons_hubspot.py doublons.csv                         # simulation, fiches lues dans HubSpot
python fusion_doublons_hubspot.py doublons.csv --groupes G-001,G-002 --executer   # test sur 2 groupes
python fusion_doublons_hubspot.py doublons.csv --executer              # tous les groupes
```

Règles appliquées à chaque groupe :

| Champ | Valeur conservée |
|---|---|
| Email | Une seule adresse en email principal (HubSpot garde l'autre en email secondaire). Écartées : adresses en échec (hard bounce), punycode `xn--`, domaine invalide. Groupe « a changé d'entreprise ou de domaine » → adresse de la fiche la plus récente ; sinon → adresse de la « Racine suggérée ». La fiche qui porte l'adresse retenue est la fiche principale de la fusion. |
| Prénom / Nom | La fiche la mieux renseignée : prénom **et** nom, prénom complet plutôt qu'initiale, forme la plus complète (« Nevers-Brunel » plutôt que « Nevers »), répartition majoritaire si prénom et nom sont inversés. Civilités retirées (« M. », « Madame »), accents gardés, jamais de tout-majuscules (« DUCHENE » → « Duchene »). |
| Téléphone / Mobile | Repris dès qu'une fiche en a un (le plus récent s'il y en a plusieurs). Un second mobile va dans le champ mobile s'il est vide ; les autres numéros sont listés dans le rapport. |
| Intitulé du poste | Celui de la fiche la plus récente (date de création) qui en a un. |
| Entreprise | Celle de la fiche la plus récente qui en a une : nom de l'entreprise et entreprise associée principale. Une valeur copiée d'un domaine email (« 54.fr ») est ignorée. |
| Propriétaire | Celui de la fiche principale s'il est actif, sinon le plus récent actif. |

Sécurités :
- **par défaut, rien n'est modifié** : le rapport `<csv>_fusion_rapport.csv` montre ce qui serait fait ;
- `--executer` fusionne réellement (irréversible), après avoir tapé `FUSIONNER` (`--oui` pour s'en passer) ;
- les groupes dont les prénoms se contredisent ne sont pas fusionnés (statut **À VÉRIFIER**) ;
- le script peut être relancé : les groupes déjà fusionnés sont détectés (**DÉJÀ FUSIONNÉ**).

Le rapport (CSV `;`, lisible dans Excel) donne pour chaque groupe : statut, ID de la fiche finale et lien,
valeurs retenues, numéros non repris et remarques à vérifier (prénoms divergents, email et entreprise
issus de fiches différentes, propriétaire désactivé conservé…).

Accès HubSpot : variable d'environnement `HUBSPOT_TOKEN` = jeton d'une application privée avec les droits
`crm.objects.contacts.read`, `crm.objects.contacts.write`, `crm.objects.companies.read` et `crm.objects.owners.read`.

Tests hors ligne : `python -m unittest test_fusion_doublons_hubspot`
