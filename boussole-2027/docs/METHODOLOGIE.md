# Méthodologie — Boussole 2027

> **Outil de réflexion, pas une consigne de vote.** Boussole 2027 aide chacun·e à situer et à comprendre sa propre orientation politique ; la comparaison avec les candidat·es est indicative. Données candidat·es : état au **25 septembre 2026** (fichier 01).

La page « Méthodologie » de l'application reprend ce document en le générant à partir des données : les chiffres y sont toujours à jour.

## 1. Axes

| Code | Axe | Pôle −100 | Pôle +100 | Statut |
|---|---|---|---|---|
| ECO | Économie | Néolibéral | Socialiste | principal |
| IDE | Identité | Individualiste | Communautariste | principal |
| ENV | Environnement | Dénialiste | Activiste | principal |
| REL | Religion | Anticlérical | Traditionnaliste | principal |
| ETA | État | Nationaliste | Internationaliste | principal |
| CUL | Culture / mœurs | Conservateur | Libertaire | principal |
| ALT | Altérité | Fermeture ethno-nationale | Ouverture / égalitarisme antiraciste | principal |
| UE | Union européenne | Anti-UE | Pro-UE (fédéraliste) | principal |
| GMO | Gouvernance mondiale | Interventionniste | Laisser-faire / non-interventionniste | principal |
| GOV | Gouvernance | Autoritaire | Démocratie libérale (État de droit, contre-pouvoirs) | principal |
| SEC | Ordre et libertés | Sécuritaire | Garantiste | secondaire |
| INS | Institutions | Présidentialisme représentatif | Parlementarisme / démocratie directe | secondaire |
| TER | Territoires | Jacobin | Girondin / municipaliste | secondaire |
| POP | Populisme | Peuple homogène contre élites | Pluralisme | secondaire |
| CHG | Mode de changement | Réformiste | Révolutionnaire | secondaire (depuis le questionnaire v2) |
| GEN, TEC, MEM | Genre et famille ; Technique ; Histoire nationale | — | — | optionnels, non mesurés (architecture prévue, `enabled: false`) |

Les intitulés des pôles sont **ceux du fichier 01**, conservés tels quels. Quelques précisions de lecture :

- « Néolibéral » désigne le pôle du marché le moins régulé ; il ne se confond pas avec « libéral » (le libéralisme social, par exemple, se situe près du centre).
- « Dénialiste » désigne la contestation du consensus scientifique sur l'origine humaine du réchauffement. Le scepticisme sur les coûts ou les moyens (Lomborg) se situe au niveau 1, pas au pôle.
- « Autoritaire » ↔ « Démocratie libérale » : un gouvernement faible n'est pas synonyme d'État de droit ; l'axe mesure l'attachement aux règles qui encadrent le pouvoir, indépendamment de l'économie.

### Reformulations et facettes (fichier 01, §5)

1. **« Racisme / xénophobie » → « Altérité »**. Appliqué à une personne ou à un·e candidat·e, le premier intitulé est un jugement moral et un risque juridique. Les candidat·es sont codé·es sur leurs **mesures** (immigration, nationalité, droits des étrangers). Pour l'utilisateur·ice, certains items s'inspirent de la psychologie sociale (racisme symbolique, dominance sociale, autoritarisme : fichier 02, §24) ; la restitution explique des positions et **n'attribue jamais d'étiquette**.
2. **Identité** : « communautariste » au sens du *communitarianism* (Taylor, Sandel, MacIntyre) ; le pôle peut être rejoint par des identitaires de droite comme par une gauche de la reconnaissance.
3. **Gouvernance mondiale** : facettes `GMO.intervention` (recours à la force) et `GMO.multilateralisme` (alliances et institutions ↔ souverainisme stratégique).
4. **Religion** : facette `REL.laicite` (laïcité libérale de reconnaissance ↔ laïcité stricte d'émancipation), pour distinguer un anticléricalisme républicain d'un attachement identitaire.
5. **Environnement** : facette `ENV.nucleaire` (place du nucléaire), qui relève des moyens et non de l'intensité de l'engagement écologique.

Les facettes sont des sous-indices calculés sur les items qui portent un `facetLoading` ; elles n'entrent pas dans la correspondance avec les candidat·es.

## 2. Questions

Questionnaire v2 (source : `docs/questionnaire-v2/*.json`, document de travail `QUESTIONNAIRE_V2.md` ; `npm run build:questions` génère `src/data/questions.json` et `src/data/groups.json`) :

- **44 blocs de 4 affirmations** (176 items Likert) : un contexte (une mesure débattue ou une situation concrète), puis 4 affirmations qui couvrent des positions différentes plutôt que deux pôles. Réponses : pas du tout d'accord, plutôt pas d'accord, neutre (0), plutôt d'accord, tout à fait d'accord, « je ne sais pas » (exclut l'item).
- **15 questions à choix** : une option parmi 5 à 7, plus « Aucune de ces réponses / je ne sais pas » (exclut la question). Elles remplacent les 14 dilemmes à deux options de la v1 et ouvrent l'éventail (démocratie directe ou des conseils, anarchisme, pouvoir national-autoritaire, technocratie…).
- **10 répartitions de 10 points**. Les deux répartitions de la rubrique « priorités » (A01, A09) passent en dernier et sont les seules à pondérer la comparaison avec les candidat·es (saillance) ; les huit autres mesurent des positions.
- **Blocs appariés** : B29 / B30 (l'Union européenne telle qu'elle est / telle que vous la souhaiteriez) et B33 / B34 (gouvernement du camp opposé / de votre camp) s'affichent à la suite. Un même énoncé jugé en sens opposés dans les deux contextes (B33a / B34a) est signalé dans les résultats.
- Ordre de passage : rubriques thématiques tirées au hasard, écrans mélangés dans chaque rubrique (69 écrans, environ 35 minutes).
- Au moins 8 items par axe principal (dont au moins 3 inversés) et 5 par axe secondaire (dont au moins 2). L'axe principal d'un item (`primaryAxis`) est son axe de plus fort chargement ; `reversed` signifie que l'accord tire vers le pôle « moins ».
- 100 items chargent 2 ou 3 axes ; 67 items reformulent une mesure réelle du fichier 01 (`sourceMeasure`), sans nommer de candidat·e.
- Chaque bloc ou question cite 1 à 3 auteurs du fichier 02 et présente les arguments en présence.
- **Vocabulaire marqué** (« lutte des classes », « grand remplacement », « remigration », « assistanat », « wokisme »…) : autorisé seulement dans une affirmation que le camp qui l'emploie pourrait signer, et expliqué dans le mode Apprendre. L'outil décrit une adhésion, il ne qualifie pas la personne. Les textes de restitution, eux, n'emploient jamais ces termes en leur nom propre.
- `scripts/lint-questions.ts` vérifie : blocs de 4 affirmations, longueur (30 mots au plus), double négation, vocabulaire marqué expliqué, noms de candidat·es et de partis, plusieurs verbes d'opinion (avertissement), quotas, inversions, chargements, ancrage, thèmes de campagne, items appariés, auteurs existants et non restreints, biais d'un répondant « tout d'accord ». Les tests heuristiques ne remplacent pas la relecture humaine : voir `docs/AUDIT_QUESTIONS.md`, qui liste aussi chaque terme marqué à valider.

## 3. Score

Pour chaque axe *a*, chaque item répondu apporte un couple (contribution *n*, maximum *m*) :

- **Likert** (r ∈ {−2..+2}, poids w) : n = w·r, m = 2|w|.
- **Dilemme** (format v1, v ∈ {−2..+2}, v > 0 = option B) : n = |v|·w(option choisie), m = 2·max(|w_A|, |w_B|).
- **Question à choix** (N options, même formule avec une réponse toujours nette) : n = 2·w(option choisie), m = 2·max_o |w_o|. Vaut aussi pour les facettes portées par les options.
- **Allocation** (parts s_o, k options) : n = 2·Σ (s_o − 1/k)·w_o, m = 2·max |w_o − moyenne(w)|. Une répartition uniforme est neutre.

**S_a = 100 × Σn / Σm** ∈ [−100 ; +100], ce qui équivaut, pour les Likert, à Σ w·r / (2 Σ|w|).

- **Confiance** : n_eff = (Σm)² / Σm² (Kish). En dessous de 4, la position est dite « peu établie ». L'intervalle à 95 % est obtenu par bootstrap sur les items (500 tirages, graine fixe, calculé dans le navigateur).
- **Niveaux** : [−100, −60), [−60, −20), [−20, 20], (20, 60], (60, 100].
- **Cohérence** : les paires `contradicts` relèvent de la même logique ; un écart (réponses tirant vers des pôles opposés, |r| ≥ 1 des deux côtés) est signalé, au plus 3 fois, avec l'explication `coexistence`.
- **Biais de réponse** : accord > 80 % ou < 20 % des Likert (acquiescence) ; temps moyen < 1,5 s.
- **Saillance** : pour une allocation à k options, l'importance relative d'une option vaut s_o·k ; chaque axe qu'elle charge en reçoit une part proportionnelle à |w|. Le résultat est une moyenne bornée à [0,5 ; 2], de 1 par défaut. Il sert **uniquement** à la correspondance avec les candidat·es.

## 4. Restitution

- **Carte 2D** : abscisse ECO ; ordonnée « Ouverture–Fermeture » = 0,3·CUL + 0,3·ALT + 0,2·GOV + 0,2·ETA (poids renormalisés si un axe manque). Les deux mœurs et altérité pèsent davantage car ce sont les dimensions culturelles les plus directement mesurées ; gouvernance et État complètent l'opposition ouverture ↔ fermeture. Pour les candidat·es, la barre d'incertitude vaut ±10 (confiance élevée), ±20 (moyenne) ou ±35 (faible). **Vue ACP** : deux composantes, ajustées sur les archétypes et les candidat·es codé·es sur au moins 8 axes ; les valeurs manquantes sont remplacées par la moyenne (point signalé).
- **Archétypes** (18) : affinité = ½·(1 + cosinus)/2 + ½·(1 − RMS/200). Le top 3 est présenté avec sa filiation (2 à 3 auteurs), ainsi qu'un contradicteur (premier auteur de l'archétype le plus éloigné).
- **Indices** : intersectionnalité (ALT, GEN si mesuré, ECO, CUL vers leurs pôles égalitaires ; Crenshaw, Hill Collins, Fraser), fusionnisme (−ECO, −CUL, +REL), souverainisme social (+ECO, −ETA, −UE). Valeur = moyenne des composantes orientées ; l'indice est « marqué » si toutes dépassent +30.
- **Carte des intersections** : l'intensité d'une paire vaut min(|s_i|, |s_j|). Les combinaisons nommées par la littérature sont signalées à partir d'une intensité de 30.
- **Textes** : 75 textes (15 axes × 5 niveaux, 80 à 120 mots). Chacun contient une description neutre, des auteurs proches, la meilleure objection du pôle opposé et une question de réflexion. S'y ajoutent 15 règles de tension explicites (`texts/tensions.json`) et une synthèse de 250 à 400 mots. Trois lectures sont proposées : une qui confirme (filiation), une qui nuance (centre ou objection de l'axe le plus marqué) et une qui contredit.
- **Auteurs restreints** : les doctrines racistes réfutées (fichier 02, §11) et les auteurs condamnés pour provocation à la haine sont marqués `restricted`. Ils ne sont jamais proposés comme « proches » d'un profil.

## 5. Correspondance avec les candidat·es

d = √( Σ c_a·s_a·(u_a − v_a)² / Σ c_a·s_a ), sur les axes principaux codés, avec c_a = confiance du codage (H 1 ; M 0,6 ; F 0,3) et s_a = saillance. Les axes `null` sont ignorés ; une candidature n'est classée qu'avec au moins 5 axes comparables. Affinité = 100·(1 − d/200).

Les données sont extraites **exclusivement** du fichier 01 (`scripts/extract-candidates.ts`) :

- le codage −2..+2 est converti en −100..+100 (× 50) ;
- une cellule sans confiance prend la confiance globale de la fiche ;
- « M à F » donne F (prudence) ;
- en l'absence de toute indication, la confiance est F ;
- « n.c. » et les cellules absentes donnent `null` (« non renseigné »).

Cas particuliers :

- **Extrême gauche** : le tableau commun est scindé ; CUL donne +75 pour Révolution permanente et +50 pour Lutte ouvrière, et reste `null` pour le NPA-R, que la cellule ne mentionne pas. GOV n'est pas codé.
- **RN** : une seule fiche, avec `alternates: ['Jordan Bardella']`, sans positions distinctes.
- **Primaire PS** : les cinq candidat·es sont affiché·es ; seul Raphaël Glucksmann est codé.
- Un statut non standard, ou marqué ⚠️, donne « Incertain », avec le détail d'origine conservé.

## 6. Validation

| Test | Critère | Résultat au 29/09/2026 |
|---|---|---|
| Neutralité (10 000 répondants aléatoires) | moyenne ∈ [−5 ; +5] par axe | entre −2,2 et +3,7 |
| Répondant « tout d'accord » | aucun axe au-delà de ±25 | au plus 23 en valeur absolue |
| Personas candidat·es (≥ 7 axes codés, 15) | top 3 dans ≥ 90 % des cas | 100 % (σ = 0,6) ; robuste jusqu'à σ = 1,2 ; échecs à σ = 1,6 (réponses très bruitées) |
| Personas archétypes (18) | top 3 dans ≥ 90 % des cas | 100 % (σ = 0,6) |
| Accessibilité | WCAG 2.2 AA (axe-core) | 0 violation sur toutes les pages |
| Réseau | aucune donnée de réponse ne quitte le navigateur | aucune requête hors origine, aucun POST |
| Charte | h1 Fraunces 35 px, Open Sans 11 pt, jaune ≤ 10 % | 0,6 % (accueil), 0,4 % (questionnaire), 0,1 % (résultats) |
| Lighthouse (accueil, mobile) | ≥ 90 | performance 98, accessibilité 100, bonnes pratiques 96, SEO 91 |

**Validité interne** : `npm run psychometrics -- pilote.csv` calcule l'alpha de Cronbach et l'oméga par axe, puis une analyse factorielle exploratoire (varimax), sur des données pilotes importées manuellement. L'option `--simuler` sert d'auto-test ; les valeurs obtenues sur des répondants simulés ne prouvent rien sur la validité réelle.

## 7. Limites

- Le codage des candidat·es est une hypothèse de calibrage à auditer, souvent de confiance moyenne ou faible, parfois tirée de programmes antérieurs. Aucun·e candidat·e n'est codé·e sur les axes secondaires.
- Les items, les textes et les archétypes sont une première version : ils doivent être relus par un panel pluraliste et validés sur un pilote (alpha, oméga, AFE).
- Les archétypes sont des repères construits à partir de la littérature, pas des catégories statistiques.
- Palette imposée par la charte : le jaune seul a un contraste insuffisant sur fond clair. Les marques de l'utilisateur·ice portent donc un contour bleu foncé, et chaque graphique a une forme distinctive et un tableau équivalent.
- Réduire des convictions à quatorze nombres simplifie nécessairement : les textes et les objections comptent autant que les scores.
