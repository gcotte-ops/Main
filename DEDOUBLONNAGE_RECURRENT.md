# Dédoublonnage HubSpot récurrent

Chaque semaine, trois routines Claude enchaînent la chaîne de dédoublonnage. La relecture humaine
reste obligatoire : **une fusion ne part que si le classeur relu a été déposé dans Drive**.

## Calendrier (heure de Paris)

| Jour | Routine | Ce qu'elle fait | Ce que fait l'équipe |
|---|---|---|---|
| Lundi 7 h 47 | Détection des entreprises | Lit HubSpot, produit `doublons_entreprises_AAAA-MM-JJ.xlsx`, l'envoie (notification Claude + email récapitulatif). | Relit le classeur et le dépose dans « 1 - Relus à fusionner » **avant mercredi 7 h**. |
| Mercredi 7 h 47 | Fusion des entreprises, puis détection des contacts | Fusionne les groupes validés du classeur déposé, mémorise les décisions, range le classeur dans « 2 - Traités ». Puis nouvelle extraction des contacts et envoi de `doublons_contacts_AAAA-MM-JJ.xlsx`. | Relit le classeur des contacts et le dépose **avant vendredi 7 h**. |
| Vendredi 7 h 47 | Fusion des contacts | Fusionne les groupes validés du classeur des contacts déposé. | — |

Sans dépôt, rien n'est fusionné : la détection suivante reproposera les mêmes groupes.

## Relecture (équipe)

1. Ouvrir le classeur reçu, onglet **Doublons**. La colonne **Nouveau** signale les groupes absents de
   la relecture précédente : ce sont eux à regarder en priorité.
2. Colonne **Décision** (liste déroulante) :
   - « Fusionner » est pré-rempli sur les groupes **Certain** : rien à faire s'ils sont bons ;
   - « Ne pas fusionner » sur la ligne d'une fiche la **retire du groupe** ; sur toutes les lignes, le
     groupe entier est écarté ;
   - sur un groupe **Probable**, « Ne pas fusionner » enregistre que ce ne sont pas des doublons : ils
     ne seront plus proposés. Les vrais doublons Probable se fusionnent à la main dans HubSpot.
3. Enregistrer en .xlsx **sans changer le nom du fichier** et le déposer dans Drive :
   « Dédoublonnage HubSpot / 1 - Relus à fusionner ».

Les décisions « Ne pas fusionner » sont mémorisées dans la feuille « Mémoire des décisions » : une fiche
écartée n'est plus jamais reproposée avec les autres fiches de son groupe. Pour revenir sur une
décision, supprimer la ligne correspondante de la feuille.

## Dossiers et fichiers Drive

| Élément | ID |
|---|---|
| Dossier « Dédoublonnage HubSpot » | `1E8Gpt6V3TJliz1pXU_FyAp5aNpjd_uGE` |
| « 1 - Relus à fusionner » (dépôt de l'équipe) | `1asQliFbRrWgJ5rZ3O0XLO7-aFN7cvyxz` |
| « 2 - Traités » (classeurs fusionnés, servent de classeur précédent) | `14KQ3kMG1RTaeM8TNXUpKoxy_X1HexUes` |
| « 3 - Mémoire des décisions » | `1Fe7f8msvtFTZwvkY41iXBD-qCWwSdQEZ` |
| Google Sheet « Mémoire des décisions », onglet `Décisions` (ID A, ID B, Objet, Classeur, Date) | `1SKAtfPIckho7E_-4P_2c0MLyd-cz-V53YrWg8vIEtlE` |
| GT 3.0 : « 0 - SUIVI PROJETS », onglet `GT3`, colonnes `Lien_hubspot` (FF) et `Id_hubspot` (FG) : **ID d'entreprise** | `1K2kXDwHK_k4H-PEp-X-2J3F2h-iXqYbK1bzsjbkt6P0` |

Emails envoyés à : gcotte@alter-watt.com.

## Configuration requise (une fois)

- **Réseau** de l'environnement cloud : autoriser `api.hubapi.com`.
- **Variable d'environnement** `HUBSPOT_TOKEN` : jeton de l'application privée HubSpot, avec les droits
  `crm.objects.companies.read`, `crm.objects.companies.write`, `crm.objects.contacts.read`,
  `crm.objects.contacts.write`, `crm.objects.owners.read` et `sales-email-read`.
- **Connecteurs** des routines : Gmail, Google Drive et Alter Watt MCP (Google Sheets).

Mettre une routine en pause : claude.ai/code, Routines, désactiver la routine.

---

## Procédure des routines (instructions pour Claude)

Règles de conduite :
- ne jamais lancer `--executer` sur un classeur qui n'a pas été pris dans « 1 - Relus à fusionner » ;
  ne jamais modifier un classeur relu ;
- au plus 200 groupes fusionnés par passage (`--limite 200`) : le reste est redétecté la semaine suivante ;
- jeton refusé (401/403), HubSpot injoignable ou classeur abîmé : ne rien fusionner, envoyer l'email
  d'alerte et s'arrêter ;
- emails courts, en français : chiffres, groupes à vérifier, prochaine échéance. Pas d'autres données
  personnelles que les noms de groupes nécessaires.

### Préparation commune

1. `git clone --depth 1 https://github.com/gcotte-ops/main dedoublonnage && cd dedoublonnage && pip install -q openpyxl`
2. Contrôle : `test -n "$HUBSPOT_TOKEN"` puis
   `curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $HUBSPOT_TOKEN" "https://api.hubapi.com/crm/v3/objects/companies?limit=1"`
   doit renvoyer 200. Sinon, envoyer l'email « Dédoublonnage HubSpot : configuration à faire » (ce qui
   manque : variable, accès réseau ou droits du jeton ; voir « Configuration requise ») et s'arrêter.
3. **Lire une réponse de connecteur** : quand Claude Code enregistre une réponse longue dans un fichier,
   utiliser ce fichier. Une réponse courte : l'écrire telle quelle dans `reponse.json`. Puis :
   - fichier Drive (`download_file_content`) : `python outils_routine.py fichier REPONSE sortie.xlsx`
     (pour une Google Sheet, demander `exportMimeType` =
     `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`). « classeur abîmé » : ne pas
     l'utiliser ;
   - plage Sheets (`sheets_get_values`) : `python outils_routine.py valeurs REPONSE sortie.csv`.
4. **Mémoire** : `sheets_get_values` sur la feuille mémoire, plage `Décisions!A:E`, vers `memoire.csv`.
5. **GT 3.0** (entreprises) : `sheets_get_values` sur « 0 - SUIVI PROJETS », plage `GT3!FF1:FG`, vers
   `gt3.csv`. Vérifier que la 1re ligne contient `Lien_hubspot` et `Id_hubspot` ; sinon lire `GT3!1:1`,
   retrouver ces deux colonnes et relire la bonne plage. En cas d'échec : continuer sans `--gt3`.
6. **Lien vers la session** (pour les emails) : `get_session` sans argument donne l'ID de la session ;
   le lien est `https://claude.ai/code/<ID>`.
7. **Classeur précédent** : dans « 2 - Traités » (`search_files` avec `parentId`), le fichier le plus
   récent dont le nom contient `entreprises` (ou `contacts`), téléchargé vers `precedent.xlsx`. S'il
   n'y en a pas, lancer la détection sans `--ancien`.

### Lundi : détection des entreprises

1. Préparation 1 à 7.
2. `python detection_entreprises_hubspot.py -o doublons_entreprises_AAAA-MM-JJ.xlsx --decisions memoire.csv --gt3 gt3.csv --ancien precedent.xlsx`
   (sans les options dont le fichier manque).
3. Envoyer le classeur avec `SendUserFile` (status `proactive`, display `attach`).
4. Email « Dédoublonnage HubSpot – entreprises à relire » : groupes et fiches Certain et Probable, groupes
   nouveaux, paires écartées à une relecture précédente, onglets de relecture (chiffres affichés par le
   script), lien vers cette session, consignes de relecture (section « Relecture » ci-dessus), échéance :
   dépôt dans « 1 - Relus à fusionner » avant mercredi 7 h.

### Mercredi : fusion des entreprises, puis détection des contacts

A. Fusion des entreprises
1. Préparation 1 à 6.
2. Lister « 1 - Relus à fusionner ». Garder les classeurs dont le nom contient `entreprises`. S'il n'y en
   a pas : pas de fusion, le dire dans l'email, passer à B.
3. Pour chaque classeur, du plus ancien au plus récent : le télécharger vers `relu.xlsx`, puis
   - simulation : `python fusion_entreprises_hubspot.py relu.xlsx --gt3 gt3.csv --memoriser decisions_nouvelles.csv --rapport simulation.csv`
   - fusion : `python fusion_entreprises_hubspot.py relu.xlsx --gt3 gt3.csv --executer --oui --limite 200 --rapport fusion.csv`
     (sans `--gt3` si `gt3.csv` n'a pas pu être lu) ;
   - décisions : `python outils_routine.py lignes decisions_nouvelles.csv` ; si la liste n'est pas vide,
     l'ajouter avec `sheets_append_values` (plage `Décisions!A1`, `valueInputOption` = `RAW`) ;
   - ranger le classeur : `update_file` avec `parentId` = « 2 - Traités » et le titre
     « <nom sans .xlsx> – fusionné AAAA-MM-JJ.xlsx ».
4. Résumé du rapport `fusion.csv` (séparateur `;`) : nombre de groupes par statut ; pour les statuts
   « À VÉRIFIER », « ERREUR » et « FUSIONNÉ - CORRECTIONS À FAIRE », le groupe, le nom et la remarque.

B. Détection des contacts (même s'il n'y a pas eu de fusion)
1. Lien vers la session et classeur précédent des contacts (préparation 6 et 7, nom contenant `contacts`).
2. `python detection_contacts_hubspot.py -o doublons_contacts_AAAA-MM-JJ.xlsx --decisions memoire.csv --ancien precedent_contacts.xlsx`
3. `SendUserFile` comme le lundi.
4. Un seul email « Dédoublonnage HubSpot – fusion des entreprises et contacts à relire » : résumé de A,
   chiffres de B, lien vers cette session, échéance : dépôt avant vendredi 7 h.

### Vendredi : fusion des contacts

1. Préparation 1 à 4 et 6.
2. Comme le mercredi (A), avec les classeurs dont le nom contient `contacts` et
   `python fusion_doublons_hubspot.py relu.xlsx …` (mêmes options, sans `--gt3`).
3. Email « Dédoublonnage HubSpot – fusion des contacts » : résumé du rapport. S'il n'y avait aucun
   classeur déposé, l'email le dit simplement.
