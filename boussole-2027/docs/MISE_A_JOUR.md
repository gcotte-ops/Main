# Procédure de mise à jour des données candidat·es

Les positions des candidat·es proviennent **exclusivement** de `docs/01_programmes_presidentielle_2027.md` (fichier 01). On ne modifie jamais `src/data/candidates.json` ni `src/data/measures.json` à la main : on met à jour le fichier 01, puis on régénère.

## Procédure générale

1. **Mettre à jour le fichier 01** :
   - modifier la date « État des connaissances au … » ;
   - pour chaque fiche concernée, les mesures (une puce ou un paragraphe « **Thème** : … ; … »), la ligne `*Sources : … *`, le tableau de codage `| ECO | IDE | … |` avec la confiance entre parenthèses, et la ligne « > Confiance globale » si besoin ;
   - la ligne du panorama (§2) : statut commençant par « Déclaré », « Primaire » ou « Pressenti ». Tout autre libellé, ou la présence de « ⚠️ », donne « Incertain ».
2. **Régénérer et contrôler** (depuis `boussole-2027/`) :
   ```bash
   npm run extract:candidates      # candidates.json + measures.json + scripts/reports/extract-candidates.md
   npm run lint:questions          # les sourceMeasure des questions doivent toujours exister
   npm test                        # schémas, références croisées, neutralité, personas
   npm run simulate:personas
   npm run audit:questions         # régénère docs/AUDIT_QUESTIONS.md
   ```
   Lire `scripts/reports/extract-candidates.md` : chaque ligne non standard ou cellule non analysable y est signalée.
3. **Mettre à jour `src/data/meta.json`** (`dataDate`, `version`). La date s'affiche dans le bandeau permanent et sur la page de résultats.
4. **Identifiants de mesures** : ils sont numérotés par candidat·e dans l'ordre du fichier (`marine-le-pen-03`). L'insertion d'une mesure décale donc les suivantes. Si le linter signale une `sourceMeasure` inconnue ou décalée, corriger les références dans `src/data/questions.json` (vérifier le texte dans `docs/AUDIT_QUESTIONS.md`).
5. Faire relire les nouveaux codages par au moins deux personnes de sensibilités différentes, puis commiter.

## Échéances connues

| Date | Événement | Action |
|---|---|---|
| 9-10 et 16-17 octobre 2026 | Primaire « Choisir 2027 » (PS, Place publique) | Après le résultat, passer le ou la lauréat·e en « Déclaré ». Si ce n'est pas Raphaël Glucksmann, ajouter un tableau de codage à sa fiche dès que des mesures sourcées existent (sinon ses positions restent « non renseigné »). Retirer les autres de la section « Primaire » : supprimer leur ligne du panorama ou passer leur statut en « Incertain ». Le bloc « Primaire » de la page de résultats disparaît dès qu'aucune candidature n'a ce statut. |
| Décembre 2026 | Déclarations formelles attendues (Éric Zemmour, Xavier Bertrand, François Hollande) | Mettre à jour les statuts (« Déclaré (date) »), ajouter les fiches et codages sourcés. |
| Date à confirmer | Arrêt de la Cour de cassation sur le pourvoi de Marine Le Pen | Si l'inéligibilité est prononcée : remplacer la fiche §3.1 par une fiche « Jordan Bardella » (le parser associe un titre de fiche au nom du panorama), avec ses propres sources ; conserver le codage seulement s'il est explicitement repris pour lui dans le fichier 01. Sinon, retirer la mention de remplacement. Le champ `alternates` est ajouté par le script pour `marine-le-pen` : l'adapter dans `scripts/extract-candidates.ts`. |
| Au fil de l'eau | Publication des programmes officiels | Remplacer les mesures issues de programmes antérieurs, relever la confiance (H) quand la source est primaire, citer les documents dans `*Sources*`. |
| Mars 2027 | Liste officielle du Conseil constitutionnel (500 parrainages) | Ne garder dans le panorama que les candidatures validées (les autres en « Incertain » ou supprimées), mettre à jour les statuts, puis `dataDate`. |

## Contrôles avant mise en ligne

- `npm test` et `npm run test:e2e` au vert (neutralité, personas, réseau, accessibilité, charte).
- Aucune position n'est inventée : chaque valeur non nulle de `candidates.json` doit correspondre à une cellule du fichier 01. Le rapport d'extraction liste les cas limites.
- La date affichée sur la page de résultats correspond à la date du fichier 01.
