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
| Fiche la plus à jour | On regarde d'abord les **emails reçus du contact** : le dernier email qu'il a envoyé désigne la fiche (et l'adresse) avec laquelle il a travaillé en dernier. À défaut d'échange, c'est la date de création qui compte. Chaque fiche est datée par le plus récent des deux. |
| Entreprise | Celle de la fiche la plus à jour qui en a une : nom de l'entreprise et entreprise associée principale. Une valeur copiée d'un domaine email (« 54.fr ») est ignorée. |
| Email | Une seule adresse en email principal (HubSpot garde l'autre en email secondaire) : **celle de l'entreprise retenue si elle existe** (même entreprise, ou même boîte sur un domaine mal orthographié), en préférant l'adresse du dernier échange, puis la « Racine suggérée ». Écartées : adresses en échec (hard bounce), punycode `xn--`, domaine invalide. S'il n'y a aucune adresse pour l'entreprise retenue, l'autre est gardée et signalée dans le rapport. La fiche qui porte l'adresse retenue est la fiche principale de la fusion. |
| Prénom / Nom | La fiche la mieux renseignée : prénom **et** nom, prénom complet plutôt qu'initiale, forme la plus complète (« Nevers-Brunel » plutôt que « Nevers »), répartition majoritaire si prénom et nom sont inversés. Civilités retirées (« M. », « Madame »). Prénom avec accents (« Sophie-Anne »), **NOM en majuscules** (« DUCHENE »). |
| Téléphone / Mobile | Repris dès qu'une fiche en a un (celui de la fiche la plus à jour s'il y en a plusieurs). Un second mobile va dans le champ mobile s'il est vide ; les autres numéros sont listés dans le rapport. |
| Intitulé du poste | Celui de la fiche la plus à jour qui en a un. |
| Propriétaire | **Toujours un utilisateur actif** quand une des fiches en a un (celui de la fiche principale en priorité). Un propriétaire désactivé n'est gardé que si aucun n'est actif. Sans le droit de lire les propriétaires, `--executer` refuse de démarrer. |

Sécurités :
- **par défaut, rien n'est modifié** : le rapport `<csv>_fusion_rapport.csv` montre ce qui serait fait ;
- `--executer` fusionne réellement (irréversible), après avoir tapé `FUSIONNER` (`--oui` pour s'en passer) ;
- les groupes dont les prénoms se contredisent ne sont pas fusionnés (statut **À VÉRIFIER**) ;
- le script peut être relancé : les groupes déjà fusionnés sont détectés (**DÉJÀ FUSIONNÉ**).

Le rapport (CSV `;`, lisible dans Excel) donne pour chaque groupe : statut, ID de la fiche finale et lien,
valeurs retenues, numéros non repris et remarques à vérifier (prénoms divergents, email et entreprise
sans adresse pour l'entreprise retenue, propriétaire désactivé faute d'actif…), ainsi que la fiche la
plus à jour et la date du dernier email reçu.

Accès HubSpot : variable d'environnement `HUBSPOT_TOKEN` = jeton d'une application privée avec les droits
`crm.objects.contacts.read`, `crm.objects.contacts.write`, `crm.objects.companies.read`, `crm.objects.owners.read`
et `sales-email-read` (lecture des emails échangés ; sans lui, l'entreprise est choisie sur la date de création).

En mode `--hors-ligne`, les échanges d'emails et les propriétaires ne sont pas lus : l'aperçu s'appuie sur la
date de création et sur la mention « (Deactivated User) » du CSV.

Tests hors ligne : `python -m unittest test_fusion_doublons_hubspot`

# Fusion des entreprises HubSpot en doublon certain

`fusion_entreprises_hubspot.py` fusionne les entreprises de niveau « Certain » de l'onglet « Doublons » du
classeur `doublons_potentiels_entreprises_hubspot.xlsx` (lu directement, sans rien installer ; un CSV exporté
avec les mêmes colonnes convient aussi). Il utilise `fusion_doublons_hubspot.py`, à garder dans le même dossier.

```bash
python fusion_entreprises_hubspot.py doublons.xlsx --hors-ligne                          # aperçu à partir du seul classeur
python fusion_entreprises_hubspot.py doublons.xlsx                                       # simulation, fiches lues dans HubSpot
python fusion_entreprises_hubspot.py doublons.xlsx --groupes G-001,G-002 --executer      # essai sur 2 groupes
python fusion_entreprises_hubspot.py doublons.xlsx --executer                            # tous les groupes « Certain »
```

| Champ | Valeur conservée |
|---|---|
| Fiche racine | Celle qui a **le plus de contacts associés** ; à égalité, la « Racine suggérée » du classeur, puis la plus complète, puis la plus ancienne. Les autres fiches y sont fusionnées. |
| Nom | Celui de la racine ; si la racine n'a pas de vrai nom (vide ou nom de domaine), celui de la racine suggérée, sinon le vrai nom le plus récent. |
| Domaine, site web | Ceux de la fiche qui donne le nom (ils servent à rattacher les contacts), remplacés seulement s'ils sont vides, factices (`4313.co`), en punycode (`xn--`) ou sur une plateforme (e-lyco, wixsite…), ou par le domaine principal du même site (`intranet.apei.fr` → `apei.fr`). |
| Propriétaire | Toujours un utilisateur actif si une des fiches en a un (celui de la racine d'abord) ; un propriétaire désactivé n'est jamais ajouté. |
| Tous les autres champs | Adresse, ville, téléphone, SIREN, SIRET, Type de décideur, secteur, catégorie d'actifs, champs OPERAT… : **la valeur saisie le plus récemment** dans HubSpot (historique de chaque propriété) ; une fiche vide est complétée par les autres. Téléphones `00 00 00 00 00` ignorés, « Ne sait pas encore » utilisé seulement faute de mieux, une valeur identique à la casse ou à la mise en forme près n'est pas réécrite. |

Les groupes dont les fiches portent des **SIREN différents** ne sont pas fusionnés (statut **À VÉRIFIER**) : ce sont
souvent deux entités juridiques distinctes (OGEC et association, par exemple). Mêmes sécurités que pour les contacts :
simulation par défaut, confirmation `FUSIONNER`, relance sans risque. Le rapport donne, pour chaque groupe, le nombre de
contacts de chaque fiche, la racine retenue, le lien vers la fiche et la liste des champs complétés ou mis à jour.

Droits du jeton : `crm.objects.companies.read`, **`crm.objects.companies.write`** et `crm.objects.owners.read`.

Tests hors ligne : `python -m unittest test_fusion_entreprises_hubspot`
