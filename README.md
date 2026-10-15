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

# Dédoublonnage HubSpot : détection puis fusion

Quatre scripts, à lancer **dans cet ordre** (portail Alter Watt `20368543`) :

| Étape | Script | Produit / effet |
|---|---|---|
| 1. Détection des entreprises, puis **relecture** | `detection_entreprises_hubspot.py` | `doublons_entreprises.xlsx` (lecture seule) |
| 2. Fusion des entreprises | `fusion_entreprises_hubspot.py doublons_entreprises.xlsx` | fusionne les groupes « Certain » |
| 3. **Nouvelle extraction** des contacts, puis détection | `detection_contacts_hubspot.py` | `doublons_contacts.xlsx` (lecture seule) |
| 4. Fusion des contacts | `fusion_doublons_hubspot.py doublons_contacts.xlsx` | fusionne les groupes « Certain » |

La détection des contacts se lance **après** la fusion des entreprises : une fois les ID d'entreprise stabilisés,
« même entreprise associée » devient un lien fiable. Seuls les groupes de niveau **« Certain »** sont fusionnés ; les
niveaux « Probable » et les onglets de relecture servent à la vérification humaine.

Fichiers à garder dans le même dossier : les quatre scripts, `normalisation.py` (normalisation commune), `familles.py`
et `lexique_familles.csv` (règle des familles). Les scripts de fusion n'ont besoin d'aucune dépendance ; les scripts
de détection utilisent `openpyxl` pour écrire le classeur (`pip install openpyxl`).

Accès : variable d'environnement `HUBSPOT_TOKEN`. La détection ne demande que la lecture
(`crm.objects.companies.read`, `crm.objects.contacts.read`, `crm.objects.owners.read`) et n'écrit jamais dans HubSpot.

Tests hors ligne : `python -m unittest test_detection_doublons test_fusion_entreprises_hubspot test_fusion_doublons_hubspot`

## Détection des entreprises

```bash
python detection_entreprises_hubspot.py                                   # lecture de toutes les entreprises par l'API
python detection_entreprises_hubspot.py --depuis-export entreprises.csv   # sur un export HubSpot, sans l'API
python detection_entreprises_hubspot.py --ancien doublons_potentiels_entreprises_hubspot.xlsx   # + onglet « Comparaison »
```

Toutes les comparaisons se font sur des valeurs normalisées (`normalisation.py`) : noms sans accents ni ponctuation,
« St » → « Saint », nom équivalent sans forme juridique (SARL, EURL, association, fondation…), sans type
d'établissement (OGEC, école, lycée, EHPAD…) ni mots vides ; villes sans « cedex » ni arrondissement ; téléphones
à 10 chiffres ; domaine principal (deux derniers labels, trois pour `gouv.fr`, `asso.fr`, `ac-*.fr`…). Domaines
factices (`4313.co`), punycode, plateformes (wixsite, e-lyco…), téléphones `00 00 00 00 00`, « Ne sait pas encore »,
« NC »… sont traités comme vides.

| Niveau | Règle |
|---|---|
| **Bloquée** | SIREN différents (B1), ou **familles incompatibles** (B2). La paire n'est dans aucun groupe : onglet « Entités distinctes ». |
| **Certain** | Même nom / nom équivalent + au moins un lien fort (même domaine, même téléphone, même ville), sans contradiction ; nom générique (nom distinctif de 6 caractères ou moins, ou porté dans 3 villes) : deux liens forts ; domaines différents tolérés avec deux liens forts. Fiche sans nom ou nommée par son domaine + même site + même téléphone ou même ville. Même SIREN + « Centralisé » sur les deux fiches. Nom à une faute près + même SIREN. |
| Jamais Certain | Nom à une faute près sans SIREN identique, nom seulement inclus, domaine seulement proche (y compris deux sous-domaines d'un même domaine), villes différentes, ville absente sans autre lien fort, domaines différents avec un seul lien fort. |
| **Probable** | Nom identique, équivalent, à une faute près ou inclus + un lien fort ou une ville absente ; fiche sans nom ou nommée par son domaine + domaine identique ou proche, ou même téléphone ; noms différents + même domaine + même téléphone. |

**Règle des familles** (`familles.py`) : deux noms qui portent chacun un qualificatif de champs différents ne sont
jamais fusionnés, en activité (enseignement, collectivité, État, médico-social, religieux, immobilier…) ou en nature
juridique (association/fondation, société, public). « OGEC Marmoutier » / « Mairie - Marmoutier » : incompatibles ;
« Fondation Alix Le Clerc » / « Association Alix Le Clerc » : compatibles. Les marqueurs sont dans
`lexique_familles.csv` (séparateur `;`), à enrichir sans toucher au code ; les mots ambigus (institut, résidence,
maison, groupe, centre, communauté, MAS) ne sont jamais marqueurs seuls.

**Groupes, règle stricte** : une fusion est irréversible, aucun chaînage n'est accepté. Dans un groupe « Certain »,
toutes les paires de fiches sont « Certain ». Une fiche liée à une partie seulement du groupe va dans un groupe
« Probable » « lien indirect (chaînage) », avec la racine du groupe Certain. Numérotation `G-001`… triée par nom de la
racine, identique d'une exécution à l'autre.

**Racine suggérée** : même ordre que la fusion (fiche avec transactions, celle de la GT 3.0 si plusieurs, le plus de
contacts associés, un vrai nom, la plus complète, un propriétaire actif, la plus ancienne).

Le classeur contient :
- **Synthèse** : date et source, nombres de fiches et de groupes par niveau et par onglet, avertissements, « Comment
  lire les niveaux » ;
- **Doublons** : niveaux Certain et Probable, colonnes lues par la fusion (sans renommage) + « Transactions
  associées », « Dans la GT 3.0 » et « Liens avec la racine » (liens et contradictions de chaque fiche avec la racine) ;
- **Filiales et établissements** (`F-`), **Homonymes à vérifier** (`H-`), **SIREN commun** (`S-`), **Entités
  distinctes** (`E-`, paires bloquées avec leur motif) : relecture seulement, jamais fusionnés ;
- **Comparaison** (avec `--ancien`) : ancien et nouveau niveau de chaque groupe de l'ancien classeur.

Avec `--depuis-export`, les colonnes absentes de l'export sont signalées et les règles qui en dépendent désactivées.
L'ancien classeur de doublons peut servir d'export (`--depuis-export ancien.xlsx`) pour un test de non-régression.

## Détection des contacts

```bash
python detection_contacts_hubspot.py                                 # nouvelle extraction par l'API
python detection_contacts_hubspot.py --depuis-export contacts.csv
```

| Niveau | Règle |
|---|---|
| **Bloquée** | Prénoms incompatibles (deux prénoms complets différents, initiales qui ne correspondent pas) : onglet « Personnes distinctes ». |
| **Certain** | Même email (principal identique, ou principal de l'un parmi les emails secondaires de l'autre), sauf adresse générique ; même boîte sur un domaine mal orthographié + même nom de famille ; même prénom et même nom + un lien fort : même entreprise associée, même domaine email professionnel, même mobile, même téléphone fixe. |
| Jamais Certain | Webmails seuls, entreprises différentes sans autre lien, prénom réduit à une initiale (sauf même email), adresse générique partagée (contact@, accueil@…). |
| **Probable** | Les cas ci-dessus ; nom à une faute près, incomplet ou composé + un lien fort ; fiche sans nom dont l'email reprend le prénom et le nom de l'autre. Un prénom + nom porté par plus de 3 fiches sans autre lien n'est pas proposé (homonymes). |

Onglets : **Doublons** (colonnes lues par la fusion + « Autres emails », « Mobile », « ID entreprise associée »,
« Liens avec la racine »), **Personnes distinctes** (`P-`), **Adresses génériques partagées** (`A-`).

# Fusion des contacts HubSpot en doublon certain

`fusion_doublons_hubspot.py` fusionne les contacts de niveau « Certain » de l'onglet « Doublons » du classeur
`doublons_contacts.xlsx` (lu directement ; un CSV avec les mêmes colonnes, comme l'ancienne liste « Doublons
certains », convient aussi) : les fiches d'un même groupe (G-001, G-002…) sont fusionnées en une seule, puis la
fiche obtenue est corrigée.

```bash
python fusion_doublons_hubspot.py doublons_contacts.xlsx --hors-ligne        # aperçu à partir du seul classeur
python fusion_doublons_hubspot.py doublons_contacts.xlsx                     # simulation, fiches lues dans HubSpot
python fusion_doublons_hubspot.py doublons_contacts.xlsx --groupes G-001,G-002 --executer   # test sur 2 groupes
python fusion_doublons_hubspot.py doublons_contacts.xlsx --executer          # tous les groupes « Certain »
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
- les groupes dont les prénoms se contredisent ne sont pas fusionnés (statut **À VÉRIFIER**), ni ceux dont une
  paire n'est pas un doublon certain d'après les fiches lues (même email, même boîte + même nom, ou même prénom et
  nom + un lien fort : voir « Détection des contacts ») ;
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
classeur `doublons_entreprises.xlsx` (lu directement, sans rien installer ; un CSV exporté avec les mêmes colonnes
convient aussi). Il utilise `fusion_doublons_hubspot.py`, `normalisation.py`, `familles.py` et
`detection_entreprises_hubspot.py`, à garder dans le même dossier.

```bash
python fusion_entreprises_hubspot.py doublons.xlsx --hors-ligne                          # aperçu à partir du seul classeur
python fusion_entreprises_hubspot.py doublons.xlsx                                       # simulation, fiches lues dans HubSpot
python fusion_entreprises_hubspot.py doublons.xlsx --groupes G-001,G-002 --executer      # essai sur 2 groupes
python fusion_entreprises_hubspot.py doublons.xlsx --executer                            # tous les groupes « Certain »
```

| Champ | Valeur conservée |
|---|---|
| Fiche racine | Celle qui a **une ou plusieurs transactions associées**. Si plusieurs en ont : celle dont la transaction figure dans la **GT 3.0** (onglet GT3 du classeur « 0 - SUIVI PROJETS », colonne `Id_hubspot`) ; si plusieurs y figurent ou aucune, et pour les groupes sans transaction : celle qui a **le plus de contacts associés**. À égalité : la « Racine suggérée » du classeur, puis la plus complète, puis la plus ancienne. Les autres fiches y sont fusionnées. |
| Nom | Celui de la racine ; si la racine n'a pas de vrai nom (vide ou nom de domaine), celui de la racine suggérée, sinon le vrai nom le plus récent. |
| Domaine, site web | Ceux de la fiche qui donne le nom (ils servent à rattacher les contacts), remplacés seulement s'ils sont vides, factices (`4313.co`), en punycode (`xn--`) ou sur une plateforme (e-lyco, wixsite…), ou par le domaine principal du même site (`intranet.apei.fr` → `apei.fr`). |
| Propriétaire | Toujours un utilisateur actif si une des fiches en a un (celui de la racine d'abord) ; un propriétaire désactivé n'est jamais ajouté. |
| Tous les autres champs | Adresse, ville, téléphone, SIREN, SIRET, Type de décideur, secteur, catégorie d'actifs, champs OPERAT… : **la valeur saisie le plus récemment** dans HubSpot (historique de chaque propriété) ; une fiche vide est complétée par les autres. Téléphones `00 00 00 00 00` ignorés, « Ne sait pas encore » utilisé seulement faute de mieux, une valeur identique à la casse ou à la mise en forme près n'est pas réécrite. |

Ne sont pas fusionnés (statut **À VÉRIFIER**) les groupes dont les fiches portent des **SIREN différents** (souvent
deux entités juridiques distinctes, OGEC et association par exemple), dont deux noms sont de **familles
incompatibles** (« familles incompatibles : A / B »), ou dont une paire n'est pas un doublon certain d'après les fiches
lues dans HubSpot (« lien indirect » : règles de la détection recalculées). Un nom retenu qui commence par une forme
juridique (« EURL ABBAYE DE LA COUDRE ») est remplacé par celui d'une autre fiche du groupe qui n'en a pas ; un « Type
de décideur » ou une catégorie d'actifs contradictoires entre fiches sont signalés dans les remarques (la valeur la
plus récente est gardée). Mêmes sécurités que pour les contacts :
simulation par défaut, confirmation `FUSIONNER`, relance sans risque. Le rapport donne, pour chaque groupe, le nombre de
contacts de chaque fiche, la racine retenue, le lien vers la fiche et la liste des champs complétés ou mis à jour.

La GT 3.0 est lue dans `gt3_ids.txt` (IDs HubSpot des entreprises de l'onglet GT3, un par ligne) s'il est dans le
dossier, ou dans le fichier donné par `--gt3` : cette liste ou un export CSV de l'onglet GT3. Sans elle, le script le
signale et départage les fiches à transactions par le nombre de contacts. Les lignes non numériques sont ignorées et
les ID de moins de 8 chiffres signalés. Si l'onglet GT3 contient finalement des ID de transaction, passer
`GT3_CONTIENT = "transactions"` en tête de `fusion_entreprises_hubspot.py` (utilisé aussi par la détection).

Droits du jeton : `crm.objects.companies.read`, **`crm.objects.companies.write`** et `crm.objects.owners.read`.

Tests hors ligne : `python -m unittest test_fusion_entreprises_hubspot`
