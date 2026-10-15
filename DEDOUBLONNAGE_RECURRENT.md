# Dédoublonnage HubSpot hebdomadaire

Chaque **lundi à 7 h 47** (heure de Paris), une routine Claude :

1. lit toute la base HubSpot (entreprises, puis contacts) avec le **connecteur HubSpot** ;
2. repère les fiches **créées depuis 7 jours** (depuis minuit, il y a 7 jours) et les compare à toute la base ;
3. **fusionne les doublons « Certain »** : chaque groupe est relu dans HubSpot et recontrôlé fiche par fiche
   juste avant la fusion (la fiche gardée est la racine suggérée) ;
4. envoie le compte rendu (email et app Claude) : groupes fusionnés, doublons « Probable » à vérifier à la
   main avec les liens HubSpot, alertes. Les classeurs de la semaine sont joints dans l'app Claude.

Les doublons « Probable » ne sont **jamais** fusionnés automatiquement. Les entreprises passent avant les
contacts : les contacts sont lus après la fusion des entreprises, avec leurs nouvelles associations.

## Configuration requise (une fois)

Les connecteurs HubSpot et Alter Watt MCP lisent les données mais ne savent pas fusionner : la fusion passe
par l'API HubSpot, avec le jeton de l'application privée.

Dans les réglages de l'environnement cloud (menu de l'environnement dans la barre de titre d'une session,
puis **Edit**) :

- **Accès réseau** : ajouter `api.hubapi.com` aux domaines autorisés (laisser cochée l'autorisation des
  gestionnaires de paquets) ;
- **Variable d'environnement** `HUBSPOT_TOKEN` : jeton de l'application privée HubSpot, avec les droits
  `crm.objects.companies.read`, `crm.objects.companies.write`, `crm.objects.contacts.read`,
  `crm.objects.contacts.write`, `crm.objects.owners.read` et `sales-email-read`.

Ne jamais écrire le jeton dans le dépôt (il est public), dans un fichier ou dans un message.

Dans la routine (claude.ai/code › Routines) :

- **Connecteurs** : **HubSpot** (lecture), **Alter Watt MCP** (GT 3.0), **Gmail** (compte rendu) ;
- **Dépôt** : `gcotte-ops/Main`, seul dépôt de la routine : la session démarre dans ce dépôt et
  ses scripts sont son propre code. Un dépôt simplement cloné en cours de session est traité comme
  du code externe par le mode automatique, qui refuse d'en lancer les scripts. Si des commandes
  restent bloquées, ajouter dans le dépôt un `.claude/settings.json` avec des règles
  `permissions.allow` du type `Bash(python outils_routine.py:*)` (une par script).

Sans jeton ou sans accès réseau, la routine détecte quand même mais ne fusionne rien : le compte rendu
liste les doublons Certain à fusionner à la main et rappelle la configuration à faire.

## Fusionner à la main

Dans HubSpot, ouvrir la fiche marquée « garder », **Actions › Fusionner**, choisir la fiche « doublon » et
garder la fiche « garder » comme fiche principale.

## Rattraper une semaine manquée, mettre en pause

- Semaine manquée : claude.ai/code › Routines › la routine › exécuter maintenant, avec le message
  « période : 14 jours ».
- Pause : claude.ai/code › Routines › désactiver la routine.

## Références

| Élément | Valeur |
|---|---|
| Portail HubSpot | `20368543` (EU) |
| GT 3.0 : « 0 - SUIVI PROJETS », onglet `GT3`, colonnes `Lien_hubspot` (FF) et `Id_hubspot` (FG) : **ID d'entreprise** | `1K2kXDwHK_k4H-PEp-X-2J3F2h-iXqYbK1bzsjbkt6P0` |
| Destinataire du compte rendu | gcotte@alter-watt.com |

---

## Procédure de la routine (instructions pour Claude)

Règles de conduite :
- ne fusionner que les groupes **Certain** du classeur produit par la détection de ce passage ; jamais les
  Probable ;
- plus de **20 groupes Certain** pour un objet : ne rien fusionner pour cet objet (import en masse
  probable) et le signaler en tête du compte rendu ;
- jeton absent ou refusé, HubSpot injoignable : ne rien fusionner (simulation hors ligne) ; le compte rendu
  le dit et liste les Certain à fusionner à la main ;
- ne jamais afficher, écrire ni transmettre la valeur de `HUBSPOT_TOKEN` ;
- compte rendu court, en français : chiffres, groupes, liens, alertes.

### 1. Préparation

1. Le dépôt `gcotte-ops/Main` est extrait dans le dossier de travail de la session (dépôt de la
   routine) : se placer dans ce dossier (`cd` seul, dans une commande à part), puis
   `mkdir -p travail`. Lancer ensuite chaque script seul, depuis ce dossier
   (`python outils_routine.py …`, sans `cd … &&` devant ni `|` derrière). openpyxl manquant :
   `pip install -q openpyxl`.
   Si le dépôt n'est pas extrait (routine sans dépôt), le dire dans le compte rendu et s'arrêter :
   les scripts d'un dépôt cloné en cours de session sont refusés.
2. **Période** : 7 jours, sauf si le message de lancement en donne une autre (« période : 14 jours »).
3. **Accès à l'API** (pour fusionner) : `python outils_routine.py acces` affiche `FUSION=oui` ou
   `FUSION=non : <raison>` (variable `HUBSPOT_TOKEN` absente, `api.hubapi.com` non autorisé, jeton
   refusé, droit manquant). La raison va dans le compte rendu.
4. **Réponses des connecteurs** : quand Claude Code enregistre une réponse longue dans un fichier, il indique
   son chemin ; ces fichiers sont dans le dossier `tool-results` de la session (noté DOSSIER ci-dessous).
   Une réponse courte : l'écrire telle quelle dans un fichier `.json` de `travail/`.
5. **GT 3.0** : `sheets_get_values` (Alter Watt MCP) sur `1K2kXDwHK_k4H-PEp-X-2J3F2h-iXqYbK1bzsjbkt6P0`, plage
   `GT3!FF1:FG`, puis `python outils_routine.py valeurs REPONSE travail/gt3.csv`. La 1re ligne doit contenir
   `Lien_hubspot` et `Id_hubspot` ; sinon lire `GT3!1:1`, retrouver ces deux colonnes et relire la bonne
   plage. En cas d'échec : continuer sans `--gt3` et le signaler.
6. **Lien de la session** (compte rendu) : `get_session` sans argument donne l'ID ; le lien est
   `https://claude.ai/code/<ID>`.

### 2. Lecture de la base (OBJET = `entreprises`, puis `contacts`)

Le connecteur HubSpot (`query_crm_data`) renvoie au plus 500 fiches par requête et 10 000 par recherche :
la base se lit par tours de 20 requêtes, chaque tour reprenant après le plus grand ID lu.

1. `python outils_routine.py requetes OBJET` : 20 requêtes SQL. Les lancer **toutes dans un même message**
   (`query_crm_data`, `verbosityLevel` = `LOW`), sans recopier les résultats.
2. `python outils_routine.py borne OBJET DOSSIER --depuis 0`. Tant que la réponse dit `tour_complet=oui` :
   `python outils_routine.py requetes OBJET --borne <borne>`, lancer ces 20 requêtes, puis
   `python outils_routine.py borne OBJET DOSSIER --depuis <borne de ce tour>`.
3. `python outils_routine.py fin OBJET` : lancer cette requête (les 500 derniers ID, dont la dernière page,
   trop courte pour être enregistrée).
4. `python outils_routine.py collecter OBJET travail/base_OBJET.jsonl DOSSIER`
5. Contrôle : `python outils_routine.py somme OBJET`, lancer la requête (elle renvoie la somme des ID), puis
   `python outils_routine.py controle OBJET travail/base_OBJET.jsonl <somme>`. « Lecture INCOMPLÈTE » :
   relancer la requête « fin » et la requête « somme », recollecter et recontrôler une fois ; si l'écart
   demeure, continuer mais le signaler (des doublons peuvent manquer ; les fusions restent contrôlées).

### 3. Entreprises

1. Lecture (section 2) avec OBJET = `entreprises`.
2. `python detection_entreprises_hubspot.py --depuis-mcp travail/base_entreprises.jsonl --nouvelles-depuis 7 --gt3 travail/gt3.csv -o travail/doublons_entreprises_AAAA-MM-JJ.xlsx`
   (7 : la période ; sans `--gt3` si la GT 3.0 n'a pas pu être lue). Noter les chiffres affichés.
3. Fusion des groupes Certain (s'il y en a, et au plus 20) :
   - FUSION = oui : `python fusion_entreprises_hubspot.py travail/doublons_entreprises_AAAA-MM-JJ.xlsx --gt3 travail/gt3.csv --executer --oui --limite 20 --rapport travail/fusion_entreprises.csv`
   - FUSION = non : la même commande avec `--hors-ligne` au lieu de `--executer --oui` (rien n'est modifié).
4. `python outils_routine.py bilan travail/doublons_entreprises_AAAA-MM-JJ.xlsx --rapport travail/fusion_entreprises.csv`

### 4. Contacts (après la fusion des entreprises)

1. Lecture (section 2) avec OBJET = `contacts`.
2. `python detection_contacts_hubspot.py --depuis-mcp travail/base_contacts.jsonl --nouvelles-depuis 7 -o travail/doublons_contacts_AAAA-MM-JJ.xlsx`
3. Fusion des groupes Certain, comme pour les entreprises, avec
   `python fusion_doublons_hubspot.py travail/doublons_contacts_AAAA-MM-JJ.xlsx --executer --oui --limite 20 --rapport travail/fusion_contacts.csv`
   (ou `--hors-ligne`).
4. `python outils_routine.py bilan travail/doublons_contacts_AAAA-MM-JJ.xlsx --rapport travail/fusion_contacts.csv`

### 5. Compte rendu

1. `SendUserFile` (status `proactive`, display `attach`) : les deux classeurs et les rapports de fusion.
2. Email (Gmail, `send_message`) à gcotte@alter-watt.com, objet
   « Dédoublonnage HubSpot – semaine du JJ/MM/AAAA », texte brut :
   - alertes d'abord (fusion impossible et pourquoi, plus de 20 Certain, lecture incomplète, GT 3.0 non lue) ;
   - entreprises puis contacts : fiches lues, fiches créées sur la période, puis le texte de `bilan`.
     Statuts : `FUSIONNÉ` (fait) ; `FUSIONNÉ - CORRECTIONS À FAIRE` (fusionné, champs à reprendre à la
     main) ; `À VÉRIFIER` (le contrôle avant fusion a refusé : ne pas fusionner sans regarder) ; `ERREUR` ;
     `SIMULATION` (pas fusionné : à faire à la main) ;
   - lien vers la session.
   Si aucun doublon n'a été trouvé, l'email le dit en deux lignes.
