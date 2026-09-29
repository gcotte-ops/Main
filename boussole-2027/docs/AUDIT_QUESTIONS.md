# Audit des questions — Boussole 2027

_Document généré par `npm run audit:questions` — ne pas modifier à la main. Données au 2026-09-25. Source du questionnaire : `docs/questionnaire-v2/*.json`._

Ce document est destiné à un panel de relecture pluraliste (sensibilités politiques différentes). Pour chaque bloc : le contexte, les 4 affirmations et leurs chargements (signe = pôle favorisé par l'accord), l'explication affichée en mode « Apprendre », les auteurs et, le cas échéant, les mesures de programme dont une affirmation reformule le principe (les candidat·es ne sont jamais nommé·es). Même présentation pour les questions à choix (signe = pôle favorisé par l'option) et les répartitions.

## Synthèse

- 44 blocs, 201 items : {"likert":176,"dilemma":0,"choice":15,"allocation":10}
- 100 items à chargements croisés ; 67 items ancrés dans une mesure du fichier 01
- Linter : 0 erreur(s), 2 avertissement(s)

| Axe | Pôle − | Pôle + | Items (axe principal) | Inversés | Biais « tout d'accord » |
|---|---|---|---|---|---|
| ECO | Néolibéral | Socialiste | 37 | 15 | 11 |
| IDE | Individualiste | Communautariste | 9 | 4 | -1 |
| ENV | Dénialiste | Activiste | 16 | 6 | 18 |
| REL | Anticlérical | Traditionnaliste | 11 | 4 | 23 |
| ETA | Nationaliste | Internationaliste | 14 | 8 | -20 |
| CUL | Conservateur | Libertaire | 13 | 6 | -2 |
| ALT | Fermeture ethno-nationale | Ouverture / égalitarisme antiraciste | 26 | 12 | -8 |
| UE | Anti-UE | Pro-UE (fédéraliste) | 10 | 3 | 16 |
| GMO | Interventionniste | Laisser-faire / non-interventionniste | 10 | 3 | 10 |
| GOV | Autoritaire | Démocratie libérale (État de droit, contre-pouvoirs) | 10 | 5 | -20 |
| SEC | Sécuritaire | Garantiste | 11 | 5 | -17 |
| INS | Présidentialisme représentatif | Parlementarisme / démocratie directe | 8 | 3 | 21 |
| TER | Jacobin | Girondin / municipaliste | 7 | 2 | 16 |
| POP | Peuple homogène contre élites | Pluralisme | 10 | 6 | -23 |
| CHG | Réformiste | Révolutionnaire | 9 | 3 | 21 |

## Vocabulaire marqué

Ces termes sont employés parce qu'ils sont en usage dans le débat. Le linter vérifie qu'ils sont expliqués en mode Apprendre ; le panel vérifie que l'affirmation pourrait être signée par le camp qui les emploie.

- ☐ B04a : « lutte des classes »
- ☐ B07d : « assistanat »
- ☐ B10b : « écologie punitive »
- ☐ B17d : « mondialisme »
- ☐ B21c : « patriarcat »
- ☐ B21d : « wokisme »
- ☐ B25b : « grand remplacement »
- ☐ B26a : « préférence nationale »
- ☐ B27d : « remigration »
- ☐ B28c : « ensauvagement »
- ☐ B28d : « islamophobie »
- ☐ B32d : « impérialisme »
- ☐ B35d : « oligarchie »
- ☐ B38c : « violences policières »
- ☐ C03 : « remigration »
- ☐ C12 : « oligarchie »
- ☐ C12 : « bourgeoisie »

## Économie et travail

#### B01 — Retraites

**Contexte** : Le système de retraite doit à nouveau être réformé. Que pensez-vous de chacune de ces pistes ?

- **Thème** : retraites · **Auteurs** : Bernard Friot ; Milton Friedman ; Gøsta Esping-Andersen
- **Explication** (mode Apprendre) : Les défenseurs d'un retour à 62 ou 60 ans invoquent la pénibilité et une espérance de vie en bonne santé très inégale selon les métiers ; Bernard Friot voit dans la pension un « salaire continué ». Les partisans d'un report ou de la capitalisation soulignent le vieillissement démographique et le poids des retraites dans les dépenses publiques ; la liberté de choix séduit les libéraux mais pénalise ceux qui ne peuvent pas travailler plus longtemps.

##### B01a — Affirmation · Économie (ECO)

> Revenir à un départ à 62 ans, voire 60 ans, financé par des cotisations patronales plus élevées.

- **Chargements** (accord) : ECO +0,8
- **Mesures du fichier 01** : retraite à 60 ans (Jean-Luc Mélenchon, §3.2) ; retour vers 62 ans, départ à 60 ans pour les carrières longues (début avant 20 ans, 40 annuités) (Marine Le Pen, §3.1) ; retraite à 62 ans (60 ans pour carrières longues/pénibles) (Marine Tondelier, §3.8) ; retraite à 60 ans à taux plein (Fabien Roussel, §3.10)

##### B01b — Affirmation · Économie (ECO) · inversé

> Relever progressivement l'âge de départ pour tenir compte de l'allongement de la durée de vie.

- **Chargements** (accord) : ECO -0,7
- **Mesures du fichier 01** : report de l'âge évoqué (65, voire 67 ans) sans calendrier arrêté (Édouard Philippe, §3.3) ; taux plein automatique à 65 ans (indexé ensuite sur l'espérance de vie) (Bruno Retailleau, §3.5) ; Retraite à 65 ans + capitalisation (David Lisnard, §3.11)

##### B01c — Affirmation · Économie (ECO) · inversé

> Introduire une part de retraite par capitalisation, c'est-à-dire une épargne individuelle placée sur les marchés.

- **Chargements** (accord) : ECO -0,8
- **Mesures du fichier 01** : 10–15 % de capitalisation d'ici 15 ans, inspirée de l'Agirc-Arrco (Édouard Philippe, §3.3) ; capitalisation « pour les jeunes » (25–30 % de leur future pension, rendement ≥ 4 %) (Bruno Retailleau, §3.5) ; réforme systémique des retraites (fin de l'âge légal fixe, part de capitalisation, selon agrégateurs ★) (Gabriel Attal, §3.4)

##### B01d — Affirmation · Économie (ECO) · inversé

> Laisser chacun choisir librement son âge de départ, avec une pension ajustée en conséquence.

- **Chargements** (accord) : ECO -0,4 ; CUL +0,2
- **Mesures du fichier 01** : réforme systémique des retraites (fin de l'âge légal fixe, part de capitalisation, selon agrégateurs ★) (Gabriel Attal, §3.4)

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B02 — Patrimoine et héritage

**Contexte** : Faut-il taxer davantage les patrimoines et les héritages ?

- **Thème** : fiscalite-patrimoine · **Auteurs** : Gabriel Zucman ; Thomas Piketty ; Arthur Laffer
- **Explication** (mode Apprendre) : Gabriel Zucman et Thomas Piketty montrent que les très grandes fortunes paient proportionnellement peu d'impôt et que l'héritage est la première source d'inégalités non choisies. Leurs contradicteurs invoquent le risque d'exil fiscal, la difficulté d'évaluer les entreprises non cotées et l'argument d'Arthur Laffer : trop d'impôt tue l'impôt. La transmission familiale est aussi défendue comme un lien entre générations.

##### B02a — Affirmation · Économie (ECO)

> Un impôt minimal de 2 % par an sur les fortunes de plus de 100 millions d'euros serait juste.

- **Chargements** (accord) : ECO +0,8
- **Mesures du fichier 01** : taxe Zucman (2 % au-delà de 100 M€) (Jean-Luc Mélenchon, §3.2) ; taxe Zucman (Olivier Faure, Jérôme Guedj, Ségolène Royal, §3.7) ; taxe Zucman, taxation des méga-héritages (1 % des successions), fin des exonérations sur le kérosène (Raphaël Glucksmann, §3.7) ; taxe Zucman (Marine Tondelier, §3.8)

##### B02b — Affirmation · Économie (ECO)

> Les héritages devraient être plafonnés : au-delà d'un certain montant, tout devrait revenir à la collectivité.

- **Chargements** (accord) : ECO +1
- **Mesures du fichier 01** : héritage maximal de 12 M€ (Jean-Luc Mélenchon, §3.2)

##### B02c — Affirmation · Économie (ECO) · inversé

> Transmettre son patrimoine à ses enfants est un droit que l'impôt ne devrait presque pas toucher.

- **Chargements** (accord) : ECO -0,8 ; IDE +0,3
- **Mesures du fichier 01** : baisse des droits de succession et liberté de tester (David Lisnard, §3.11) ; dons familiaux exonérés jusqu'à 150 000 € (Bruno Retailleau, §3.5)

##### B02d — Affirmation · Économie (ECO) · inversé

> Trop taxer le capital fait fuir les investisseurs et finit par pénaliser l'emploi.

- **Chargements** (accord) : ECO -0,8
- **Mesures du fichier 01** : aucun nouvel impôt (Édouard Philippe, §3.3)

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B03 — Une usine qui délocalise

**Contexte** : Une usine rentable de votre région annonce sa fermeture pour produire à l'étranger. Que pensez-vous de ces réponses ?

- **Thème** : emploi · **Auteurs** : Karl Polanyi ; Pierre-Joseph Proudhon ; Friedrich Hayek
- **Explication** (mode Apprendre) : Pour Karl Polanyi, une société se protège quand le marché menace ses équilibres ; la reprise en coopérative prolonge la tradition mutuelliste de Proudhon. Pour Friedrich Hayek, l'État qui fige les emplois empêche l'économie de se réallouer vers des activités plus productives, et la liberté d'entreprendre est une liberté fondamentale.

##### B03a — Affirmation · Économie (ECO)

> L'État devrait pouvoir interdire les licenciements dans une entreprise qui fait des bénéfices.

- **Chargements** (accord) : ECO +0,9
- **Mesures du fichier 01** : interdiction des licenciements boursiers (Jean-Luc Mélenchon, §3.2) ; Interdiction des licenciements boursiers (François Ruffin, §3.9) ; suspension des plans sociaux (Fabien Roussel, §3.10)

##### B03b — Affirmation · Économie (ECO)

> Les salariés devraient pouvoir reprendre l'usine en coopérative, avec l'aide de fonds publics.

- **Chargements** (accord) : ECO +0,6

##### B03c — Affirmation · Économie (ECO) · inversé

> Mieux vaut aider les salariés à se reconvertir que chercher à retenir l'entreprise.

- **Chargements** (accord) : ECO -0,5

##### B03d — Affirmation · Économie (ECO) · inversé

> C'est la liberté de l'entreprise : l'État n'a pas à s'en mêler.

- **Chargements** (accord) : ECO -0,9

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B04 — Comprendre la société française

**Contexte** : Pour comprendre les grands conflits de la société française, quelle lecture vous paraît juste ?

- **Thème** : lecture-sociale · **Auteurs** : Karl Marx et Friedrich Engels ; Christophe Guilluy ; Raymond Boudon
- **Explication** (mode Apprendre) : Marx fait de la lutte des classes le moteur de l'histoire ; Christophe Guilluy décrit une fracture territoriale entre métropoles et « France périphérique », contestée méthodologiquement. Raymond Boudon explique les parcours par des choix individuels plutôt que par des classes ; d'autres, à droite, placent la question identitaire au centre du conflit politique.

##### B04a — Affirmation · Économie (ECO)

> La lutte des classes entre travailleurs et possédants reste la clé de lecture principale.

- **Chargements** (accord) : ECO +0,8 ; CHG +0,3

##### B04b — Affirmation · Populisme (POP) · inversé

> Le clivage principal oppose désormais les grandes métropoles gagnantes et la France périphérique.

- **Chargements** (accord) : POP -0,4

##### B04c — Affirmation · Économie (ECO) · inversé

> Chacun peut réussir par son travail : raisonner en classes sociales divise inutilement.

- **Chargements** (accord) : ECO -0,7 ; IDE -0,3

##### B04d — Affirmation · Altérité (ALT) · inversé

> Le clivage essentiel oppose ceux qui défendent l'identité nationale et ceux qui la dissolvent.

- **Chargements** (accord) : ALT -0,6 ; ETA -0,4

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B05 — Dette publique

**Contexte** : La dette publique française atteint un niveau historiquement élevé. Que faudrait-il faire ?

- **Thème** : dette · **Auteurs** : James Buchanan ; John Maynard Keynes ; Stephanie Kelton
- **Explication** (mode Apprendre) : James Buchanan défend des règles constitutionnelles pour empêcher les gouvernements de reporter les coûts sur les générations futures. Keynes, et plus radicalement Stephanie Kelton, jugent qu'une dépense utile soutient l'activité et que la dette d'un État n'est pas celle d'un ménage ; le débat porte aussi sur la répartition de l'effort entre dépenses et impôts.

##### B05a — Affirmation · Économie (ECO) · inversé

> Inscrire dans la Constitution une règle d'or qui interdise les déficits.

- **Chargements** (accord) : ECO -0,7 ; INS -0,2
- **Mesures du fichier 01** : règle d'or constitutionnelle (hors dépenses militaires) (Édouard Philippe, §3.3) ; règle d'or « à l'allemande » (Gabriel Attal, §3.4) ; règle d'or par révision constitutionnelle soumise à référendum dès 2027 (Bruno Retailleau, §3.5)

##### B05b — Affirmation · Économie (ECO) · inversé

> La réduire d'abord en baissant fortement les dépenses publiques et le nombre de fonctionnaires.

- **Chargements** (accord) : ECO -0,9
- **Mesures du fichier 01** : 250 000 à 300 000 postes publics supprimés (IA, fonctions support) (Bruno Retailleau, §3.5) ; suppression de 100 000 postes de fonctionnaires (départs volontaires, hors Éducation, Armées, Justice, Intérieur) (Gabriel Attal, §3.4) ; « Révolution de la liberté » : dépenses publiques sous 50 % du PIB en dix ans, 200 à 300 Md€ d'économies, 600 000 postes de fonctionnaires en moins (non-remplacement), suppression de ministères (dont l'Environnement), déclaration unique annuelle (David Lisnard, §3.11)

##### B05c — Affirmation · Économie (ECO)

> La réduire surtout en taxant davantage les plus riches et les grandes entreprises.

- **Chargements** (accord) : ECO +0,8

##### B05d — Affirmation · Économie (ECO)

> La dette n'est pas un problème urgent : l'investissement public utile doit primer.

- **Chargements** (accord) : ECO +0,6
- **Mesures du fichier 01** : rachat de dette par la BCE / dette perpétuelle (Jean-Luc Mélenchon, §3.2)

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B06 — Une maternité menacée

**Contexte** : La maternité de votre bassin de vie doit fermer faute de médecins. Que pensez-vous de ces réponses ?

- **Thème** : services-publics · **Auteurs** : William Beveridge ; Alexis de Tocqueville ; James C. Scott
- **Explication** (mode Apprendre) : La tradition de Beveridge veut un service public de santé égal pour tous, garanti par l'État. D'autres privilégient l'efficacité et la sécurité des soins par la concentration des moyens ; Tocqueville et James C. Scott défendent la décision au plus près des habitants, contre des plans uniformes décidés de loin.

##### B06a — Affirmation · Économie (ECO)

> L'État doit la maintenir ouverte, quel qu'en soit le coût.

- **Chargements** (accord) : ECO +0,6 ; TER -0,3

##### B06b — Affirmation · Économie (ECO)

> Il faut obliger les jeunes médecins à s'installer quelques années dans les territoires qui en manquent.

- **Chargements** (accord) : ECO +0,5
- **Mesures du fichier 01** : régulation de l'installation des médecins (Olivier Faure, Jérôme Guedj, Ségolène Royal, §3.7)

##### B06c — Affirmation · Économie (ECO) · inversé

> Mieux vaut regrouper les moyens dans de grands hôpitaux plus sûrs, avec de meilleurs transports.

- **Chargements** (accord) : ECO -0,3 ; TER -0,3

##### B06d — Affirmation · Territoires (TER)

> Les élus locaux et les habitants devraient décider eux-mêmes de l'organisation des soins sur leur territoire.

- **Chargements** (accord) : TER +0,7
- **Mesures du fichier 01** : décentralisation massive (David Lisnard, §3.11)

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B07 — Salaires et pouvoir d'achat

**Contexte** : Pour améliorer le pouvoir d'achat, que pensez-vous de ces mesures ?

- **Thème** : pouvoir-achat · **Auteurs** : John Maynard Keynes ; Milton Friedman ; Robert Castel
- **Explication** (mode Apprendre) : Pour les keynésiens, la hausse des bas salaires soutient la demande ; pour Milton Friedman, les prix administrés créent pénuries et effets pervers, et la baisse des charges favorise l'emploi. Le terme « assistanat », employé par ceux qui veulent conditionner les aides, est récusé par ceux qui, comme Robert Castel, voient dans la protection sociale un droit acquis par le travail.

##### B07a — Affirmation · Économie (ECO)

> Porter rapidement le SMIC à 1 600 € net par mois.

- **Chargements** (accord) : ECO +0,8
- **Mesures du fichier 01** : SMIC à 1 600 € net et indexation des salaires (Jean-Luc Mélenchon, §3.2) ; SMIC à 1 700 € net (François Ruffin, §3.9)

##### B07b — Affirmation · Économie (ECO) · inversé

> Plutôt qu'augmenter le SMIC, baisser les cotisations pour que le salaire net augmente.

- **Chargements** (accord) : ECO -0,6
- **Mesures du fichier 01** : baisse des charges plutôt que hausse du SMIC (David Lisnard, §3.11) ; baisse des cotisations pour rapprocher brut et net (Raphaël Glucksmann, §3.7) ; baisse des cotisations salariales (+~10 % de net) financée par +4 points de TVA (François Hollande, §3.14)

##### B07c — Affirmation · Économie (ECO)

> Bloquer les prix de l'énergie et des produits de première nécessité.

- **Chargements** (accord) : ECO +0,8
- **Mesures du fichier 01** : blocage des prix des produits de première nécessité et de l'énergie (Jean-Luc Mélenchon, §3.2)

##### B07d — Affirmation · Économie (ECO) · inversé

> Notre modèle social encourage l'assistanat : les aides devraient être conditionnées à une activité.

- **Chargements** (accord) : ECO -0,8
- **Mesures du fichier 01** : RSA conditionné (David Lisnard, §3.11) ; durcissement de l'assurance chômage (5 Md€) (Gabriel Attal, §3.4)

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B43 — Le capitalisme

**Contexte** : À propos du capitalisme, que pensez-vous de ces affirmations ?

- **Thème** : systeme-economique · **Auteurs** : Karl Marx et Friedrich Engels ; Eduard Bernstein ; Mikhaïl Bakounine
- **Explication** (mode Apprendre) : Marx et Engels veulent le dépassement du capitalisme par l'appropriation collective ; la social-démocratie (Bernstein, Blum) veut le réformer ; les libéraux (Hayek, Friedman) y voient le système le plus efficace et le plus compatible avec la liberté. Bakounine et les anarchistes récusent l'État comme le capital, au profit de communautés fédérées.

##### B43a — Affirmation · Économie (ECO)

> Le capitalisme doit être aboli et remplacé par la propriété collective des moyens de production.

- **Chargements** (accord) : ECO +0,9 ; CHG +0,4
- **Mesures du fichier 01** : Candidatures « ouvrières, communistes et révolutionnaires », conçues comme porte-voix des luttes plutôt que programmes de gouvernement : hausse générale des salaires et indexation, interdiction des licenciements, expropriation des grands groupes, contrôle ouvrier, services publics (Nathalie Arthaud, Anasse Kazib, Selma Labib, §3.13)

##### B43b — Affirmation · Mode de changement (CHG) · inversé

> Le capitalisme peut être transformé par des lois sociales et écologiques ambitieuses.

- **Chargements** (accord) : CHG -0,6 ; ECO +0,2

##### B43c — Affirmation · Économie (ECO) · inversé

> L'économie de marché est le meilleur système connu : il faut surtout la laisser fonctionner.

- **Chargements** (accord) : ECO -0,9 ; CHG -0,3

##### B43d — Affirmation · Territoires (TER)

> L'État lui-même est le problème : il faudrait le remplacer par des communautés libres et autogérées.

- **Chargements** (accord) : TER +0,6 ; CHG +0,5

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### C02 — Question à choix · Économie (ECO)

> Quel modèle économique vous semble le plus juste ?

- **Option 1** : Une économie de marché libre, avec un État réduit au minimum. — ECO -1
- **Option 2** : Une économie de marché avec un filet de sécurité limité aux plus fragiles. — ECO -0,6
- **Option 3** : Une économie de marché régulée, avec une protection sociale forte, à la nordique. — ECO +0,3
- **Option 4** : Une économie sociale et solidaire : coopératives, mutuelles et biens communs. — ECO +0,5 ; TER +0,3
- **Option 5** : Une planification écologique conduite par l'État. — ECO +0,6 ; ENV +0,4
- **Option 6** : La propriété collective des moyens de production, au-delà du capitalisme. — ECO +1 ; CHG +0,4
- **Option 7** : Une économie nationale protégée, au service d'abord des Français. — ETA -0,7 ; ECO +0,2
- **Option ajoutée** : Aucune de ces réponses / je ne sais pas — exclue du calcul
- **Thème** : systeme-economique
- **Auteurs** : Friedrich Hayek ; Gøsta Esping-Andersen ; Karl Marx et Friedrich Engels
- **Explication** : Du libéralisme de Hayek et Friedman au communisme de Marx, les options couvrent l'éventail des modèles économiques. Entre les deux se situent les trois mondes de l'État-providence décrits par Esping-Andersen, l'économie sociale et solidaire (Proudhon, Ostrom), la planification écologique (Gorz, Malm) et le nationalisme économique (List).

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### C09 — Question à choix · Économie (ECO)

> Les inégalités de richesse en France sont avant tout…

- **Option 1** : … le résultat normal du travail, du talent et du mérite. — ECO -0,8
- **Option 2** : … acceptables tant que les plus pauvres voient aussi leur situation s'améliorer. — ECO -0,3
- **Option 3** : … trop fortes, et à corriger par l'impôt et les services publics. — ECO +0,5
- **Option 4** : … le produit d'un système d'exploitation, qu'il faut dépasser. — ECO +0,9
- **Option 5** : … moins graves que les fractures entre territoires. — POP -0,3 ; TER +0,3
- **Option 6** : … moins graves que les problèmes d'immigration et d'insécurité. — ALT -0,5 ; SEC -0,3
- **Option ajoutée** : Aucune de ces réponses / je ne sais pas — exclue du calcul
- **Thème** : inegalites
- **Auteurs** : John Rawls ; Thomas Piketty ; Raymond Boudon
- **Explication** : John Rawls admet des inégalités si elles profitent aux plus défavorisés ; Raymond Boudon les explique par des choix individuels ; Thomas Piketty par la dynamique du capital ; Marx par l'exploitation. D'autres jugent que ces inégalités ne sont pas le clivage principal.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### C11 — Question à choix · Économie (ECO)

> Pour garantir un revenu à chacun, quel système préférez-vous ?

- **Option 1** : Un salaire à vie attaché à la personne, financé par la cotisation. — ECO +1
- **Option 2** : Un revenu universel versé à tous, sans condition. — ECO +0,6 ; CUL +0,2
- **Option 3** : Un revenu minimum pour ceux qui en ont besoin, sans contrepartie. — ECO +0,5
- **Option 4** : Un revenu minimum conditionné à des heures d'activité ou de formation. — ECO -0,5
- **Option 5** : Moins d'aides, pour inciter davantage au travail. — ECO -0,9
- **Option 6** : Des aides réservées aux Français. — ALT -0,8 ; ETA -0,3
- **Option ajoutée** : Aucune de ces réponses / je ne sais pas — exclue du calcul
- **Thème** : protection-sociale
- **Auteurs** : Bernard Friot ; Milton Friedman ; Robert Castel
- **Explication** : Bernard Friot propose un salaire attaché à la personne ; Milton Friedman un impôt négatif ; les partisans du revenu universel veulent libérer du travail contraint. D'autres conditionnent les aides à une activité ou les réservent aux nationaux.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### A02 — Répartition · Économie (ECO)

> Si l'État disposait de 10 milliards d'euros de plus chaque année, comment les répartiriez-vous ?

- **Option 1** : Baisser les impôts et les cotisations — ECO -0,5
- **Option 2** : Réduire la dette publique — ECO -0,4
- **Option 3** : Renforcer les services publics (école, hôpital) — ECO +0,5
- **Option 4** : Augmenter les aides sociales et les minima — ECO +0,5
- **Option 5** : Investir dans la transition écologique — ENV +0,4
- **Option 6** : Renforcer la défense — GMO -0,3
- **Thème** : dette
- **Auteurs** : James Buchanan ; John Maynard Keynes
- **Explication** : Pour James Buchanan, la dette reporte sur les générations futures le coût des dépenses présentes. Pour Keynes, la dépense publique utile soutient l'activité, surtout en période de ralentissement.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### A10 — Répartition · Altérité (ALT)

> L'État doit économiser 10 milliards d'euros. Où prendriez-vous l'argent ? Répartissez 10 points.

- **Option 1** : Défense — GMO +0,4
- **Option 2** : Aides aux entreprises — ECO +0,5
- **Option 3** : Prestations sociales — ECO -0,5
- **Option 4** : Fonctionnement de l'État et nombre de fonctionnaires — ECO -0,5
- **Option 5** : Contribution à l'Union européenne et aide au développement — UE -0,4 ; ETA -0,4
- **Option 6** : Aide médicale et aides aux étrangers — ALT -0,6
- **Option 7** : Subventions aux énergies renouvelables — ENV -0,5
- **Thème** : dette
- **Auteurs** : James Buchanan ; Mariana Mazzucato
- **Explication** : Choisir où économiser révèle les dépenses que l'on juge les moins légitimes. Mariana Mazzucato souligne le rôle de l'investissement public dans l'innovation ; les partisans de la baisse des dépenses visent d'abord le fonctionnement de l'État ou les transferts.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

## Écologie et énergie

#### B08 — Climat

**Contexte** : À propos du changement climatique, que pensez-vous de ces affirmations ?

- **Thème** : climat · **Auteurs** : Le déni climatique et sa sociologie ; Bjørn Lomborg ; Serge Latouche
- **Explication** (mode Apprendre) : La première affirmation a une dimension factuelle : le GIEC conclut que l'influence humaine est la cause principale du réchauffement observé. Bjørn Lomborg accepte ce constat mais juge les coûts surestimés ; les écomodernistes misent sur l'innovation ; Serge Latouche et les décroissants estiment qu'aucune technique ne dispense de consommer moins.

##### B08a — Affirmation · Environnement (ENV) · dimension factuelle

> Le réchauffement climatique actuel est principalement dû aux activités humaines.

- **Chargements** (accord) : ENV +1

##### B08b — Affirmation · Environnement (ENV) · inversé

> Le réchauffement est réel, mais ses conséquences sont exagérées par les médias et les militants.

- **Chargements** (accord) : ENV -0,7

##### B08c — Affirmation · Environnement (ENV) · inversé

> L'innovation technologique suffira à régler la crise climatique sans changer nos modes de vie.

- **Chargements** (accord) : ENV -0,5

##### B08d — Affirmation · Environnement (ENV)

> Il faudra réduire notre consommation et renoncer à une partie de notre confort.

- **Chargements** (accord) : ENV +0,8 ; ECO +0,2

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B09 — Énergie

**Contexte** : Pour l'énergie de demain, que pensez-vous de ces choix ?

- **Thème** : energie-nucleaire · **Auteurs** : Jean-Marc Jancovici ; Ivan Illich ; Écologies conservatrices
- **Explication** (mode Apprendre) : Jean-Marc Jancovici défend nucléaire et sobriété pour décarboner ; une grande partie de l'écologie politique, dans la lignée d'Illich, rejette une technique centralisée et risquée. L'opposition aux éoliennes mêle défense des paysages, portée par des écologies conservatrices, et scepticisme sur leur efficacité.

##### B09a — Affirmation · Environnement (ENV)

> La France devrait construire de nombreux nouveaux réacteurs nucléaires.

- **Chargements** (accord) : ENV.nucleaire +0,8
- **Mesures du fichier 01** : relance nucléaire (série d'EPR) (Marine Le Pen, §3.1) ; prolongation du parc, six EPR2, relance des réacteurs à neutrons rapides (Bruno Retailleau, §3.5) ; mix 100 % public et décarboné, construction d'EPR (jusqu'à 20 évoqués) (Fabien Roussel, §3.10) ; Nucléaire (6+ EPR, SMR) (David Lisnard, §3.11)

##### B09b — Affirmation · Environnement (ENV)

> La France devrait sortir progressivement du nucléaire et miser sur les énergies renouvelables.

- **Chargements** (accord) : ENV +0,2 ; ENV.nucleaire -0,8
- **Mesures du fichier 01** : Sortie planifiée du nucléaire (fin des programmes EPR2 et SMR, arrêt progressif du parc), 44 % d'EnR dans l'électricité en 2030 (Marine Tondelier, §3.8) ; sortie planifiée du nucléaire vers 100 % renouvelables (Jean-Luc Mélenchon, §3.2)

##### B09c — Affirmation · Environnement (ENV) · inversé

> Les éoliennes défigurent les paysages : il faut un moratoire sur leur installation.

- **Chargements** (accord) : ENV -0,5 ; CUL -0,2
- **Mesures du fichier 01** : moratoire sur l'éolien (Marine Le Pen, §3.1)

##### B09d — Affirmation · Environnement (ENV)

> La priorité est la sobriété : consommer moins d'énergie, quelle qu'en soit la source.

- **Chargements** (accord) : ENV +0,8

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B10 — Une zone à faibles émissions

**Contexte** : Votre ville instaure une zone à faibles émissions qui interdit les véhicules anciens. Qu'en pensez-vous ?

- **Thème** : mobilite · **Auteurs** : Christophe Guilluy ; André Gorz ; Andreas Malm et Kohei Saito
- **Explication** (mode Apprendre) : La pollution de l'air cause de nombreux décès prématurés, d'où ces zones. L'expression « écologie punitive », employée par leurs opposants, traduit le sentiment d'injustice des ménages périphériques dépendants de la voiture, documenté par Christophe Guilluy. André Gorz et Andreas Malm lient au contraire la question écologique à la question sociale : les plus riches émettent le plus.

##### B10a — Affirmation · Environnement (ENV)

> C'est une mesure nécessaire pour protéger la santé des habitants.

- **Chargements** (accord) : ENV +0,7

##### B10b — Affirmation · Environnement (ENV) · inversé

> C'est de l'« écologie punitive » qui frappe d'abord les ménages modestes.

- **Chargements** (accord) : ENV -0,6
- **Mesures du fichier 01** : fin des ZFE (Marine Le Pen, §3.1)

##### B10c — Affirmation · Économie (ECO)

> Elle n'est acceptable qu'avec des aides massives pour changer de véhicule et des transports gratuits.

- **Chargements** (accord) : ECO +0,5

##### B10d — Affirmation · Économie (ECO)

> Ce sont les plus riches et les grandes entreprises qui polluent le plus : c'est à eux de payer d'abord.

- **Chargements** (accord) : ECO +0,6 ; ENV +0,2

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B11 — Agriculture et terres

**Contexte** : Des agriculteurs manifestent contre les normes environnementales. Que pensez-vous de ces positions ?

- **Thème** : agriculture · **Auteurs** : Rachel Carson ; Friedrich List ; Garrett Hardin et Elinor Ostrom
- **Explication** (mode Apprendre) : Depuis Rachel Carson, les défenseurs des normes rappellent leurs effets sur la santé et la biodiversité ; leurs critiques dénoncent une concurrence déloyale et un empilement de règles. Le protectionnisme agricole renoue avec Friedrich List ; la limitation de l'artificialisation des sols oppose préservation des terres et besoins de logement des communes.

##### B11a — Affirmation · Environnement (ENV) · inversé

> Leurs revendications sont justes : les normes environnementales sont devenues excessives.

- **Chargements** (accord) : ENV -0,7

##### B11b — Affirmation · État (ETA) · inversé

> Il faut garder les normes, et taxer les importations qui ne les respectent pas.

- **Chargements** (accord) : ETA -0,5 ; ENV +0,2
- **Mesures du fichier 01** : souveraineté alimentaire dans la PAC (François Ruffin, §3.9)

##### B11c — Affirmation · Environnement (ENV)

> Il faut sortir des pesticides comme le glyphosate, en accompagnant les agriculteurs, même si cela coûte cher.

- **Chargements** (accord) : ENV +0,8
- **Mesures du fichier 01** : interdiction du glyphosate (Jean-Luc Mélenchon, §3.2)

##### B11d — Affirmation · Environnement (ENV) · inversé

> Les communes qui manquent de logements devraient pouvoir construire sur des terres agricoles.

- **Chargements** (accord) : ENV -0,5
- **Thème** : logement-zan
- **Mesures du fichier 01** : abrogation de la loi SRU, fin de l'interdiction de louer les logements F/G, suppression du ZAN, MaPrimeRénov' remplacée par des prêts à taux zéro, expulsions accélérées en cas d'impayés (Marine Le Pen, §3.1) ; suppression des quotas SRU et du ZAN (Bruno Retailleau, §3.5)

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### C04 — Question à choix · Environnement (ENV)

> Face à la crise écologique, quelle stratégie vous paraît la meilleure ?

- **Option 1** : La croissance verte, par l'innovation et les mécanismes de marché. — ENV +0,3 ; ECO -0,5
- **Option 2** : La planification publique, avec le nucléaire et les renouvelables. — ENV +0,5 ; ECO +0,4 ; ENV.nucleaire +0,6
- **Option 3** : La sobriété et la décroissance de la production matérielle. — ENV +0,9 ; ECO +0,3
- **Option 4** : Une écologie locale et enracinée : terroirs, paysages, circuits courts. — ENV +0,5 ; IDE +0,3 ; TER +0,3
- **Option 5** : L'adaptation aux changements plutôt que la réduction des émissions. — ENV -0,5
- **Option 6** : D'autres priorités (pouvoir d'achat, emploi, sécurité) passent avant l'écologie. — ENV -0,8
- **Option ajoutée** : Aucune de ces réponses / je ne sais pas — exclue du calcul
- **Thème** : climat
- **Auteurs** : Écomodernisme ; Serge Latouche ; Bjørn Lomborg
- **Explication** : L'écomodernisme mise sur la technique, Jancovici sur le nucléaire et la sobriété, Latouche sur la décroissance, les écologies conservatrices sur l'enracinement local ; Bjørn Lomborg privilégie l'adaptation. Les enquêtes montrent que la priorité donnée à l'écologie varie fortement selon les revenus et les territoires.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### A08 — Répartition · Environnement (ENV)

> Qui devrait payer en priorité la transition écologique ? Répartissez 10 points.

- **Option 1** : Les plus riches et les grandes entreprises — ECO +0,5
- **Option 2** : Tout le monde, par une taxe carbone redistribuée — ENV +0,4 ; ECO -0,2
- **Option 3** : L'État, par l'emprunt — ECO +0,3
- **Option 4** : Les pays qui polluent le plus (Chine, États-Unis…) — ETA -0,3
- **Option 5** : Les consommateurs, selon ce qu'ils achètent — ECO -0,4
- **Option 6** : Personne : il faut ralentir la transition — ENV -0,6
- **Thème** : climat
- **Auteurs** : Gabriel Zucman ; Bjørn Lomborg
- **Explication** : Le partage de l'effort écologique est au cœur des tensions sociales, du mouvement des gilets jaunes aux débats sur la taxation des plus riches. Beaucoup d'économistes du climat défendent une taxe carbone redistribuée ; d'autres jugent qu'il faut d'abord faire payer les plus gros émetteurs.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

## Religion, laïcité et école

#### B12 — Place des religions

**Contexte** : À propos de la place des religions dans la société, que pensez-vous de ces affirmations ?

- **Thème** : religion · **Auteurs** : Chantal Delsol ; Voltaire ; Jürgen Habermas
- **Explication** (mode Apprendre) : Pour Chantal Delsol, l'héritage chrétien structure la culture et la morale françaises. La tradition voltairienne voit dans l'influence religieuse une menace pour l'émancipation ; Habermas estime que les croyants peuvent contribuer au débat public si leurs arguments restent compréhensibles par tous.

##### B12a — Affirmation · Religion (REL)

> La France devrait davantage assumer ses racines chrétiennes dans la vie publique.

- **Chargements** (accord) : REL +0,8

##### B12b — Affirmation · Religion (REL) · inversé

> Les religions font aujourd'hui plus de mal que de bien à la société.

- **Chargements** (accord) : REL -0,9

##### B12c — Affirmation · Religion (REL)

> Les croyants devraient peser davantage dans les débats de société, comme la fin de vie ou la bioéthique.

- **Chargements** (accord) : REL +0,6

##### B12d — Affirmation · Religion (REL) · inversé

> La foi est une affaire strictement privée, qui n'a pas sa place dans la vie publique.

- **Chargements** (accord) : REL -0,7 ; REL.laicite +0,5

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B13 — Laïcité : une sortie scolaire

**Contexte** : Une mère portant le voile souhaite accompagner une sortie scolaire. Que pensez-vous de ces positions ?

- **Thème** : laicite · **Auteurs** : Jean Baubérot et Henri Peña-Ruiz ; Élisabeth Badinter ; Olivier Roy et Gilles Kepel
- **Explication** (mode Apprendre) : Jean Baubérot défend une laïcité libérale, qui oblige l'État et non les citoyens ; Henri Peña-Ruiz et Élisabeth Badinter une laïcité plus exigeante envers les signes religieux. Gilles Kepel et Olivier Roy débattent de la nature de l'islamisme ; les opposants à l'interdiction du voile y voient une atteinte à la liberté de conscience visant une seule religion.

##### B13a — Affirmation · Altérité (ALT)

> Elle doit pouvoir le faire : la laïcité s'impose aux enseignants, pas aux parents.

- **Chargements** (accord) : ALT +0,6 ; REL.laicite -0,6

##### B13b — Affirmation · Altérité (ALT) · inversé

> Elle ne devrait pas : l'école et ses activités doivent rester à l'abri de tout signe religieux.

- **Chargements** (accord) : ALT -0,3 ; REL.laicite +0,7

##### B13c — Affirmation · Altérité (ALT) · inversé

> Le port du voile islamique devrait être interdit dans tout l'espace public.

- **Chargements** (accord) : ALT -0,8 ; REL.laicite +0,5
- **Mesures du fichier 01** : Interdiction du voile islamique dans l'espace public, sanctionnée par une amende, soumise à référendum (annonce J.-P. Tanguy 30/08/2026, précision J. Bardella 31/08/2026) (Marine Le Pen, §3.1)

##### B13d — Affirmation · Altérité (ALT) · inversé

> Le vrai sujet n'est pas le voile mais l'islamisme, qui progresse dans certains quartiers.

- **Chargements** (accord) : ALT -0,5 ; SEC -0,3
- **Mesures du fichier 01** : interdiction des Frères musulmans, du voile à l'université, contrôle des écoles hors contrat (David Lisnard, §3.11)

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B14 — Critique des religions

**Contexte** : Un journal publie des caricatures d'une figure religieuse. Que pensez-vous de ces positions ?

- **Thème** : laicite · **Auteurs** : Voltaire ; Charles Taylor
- **Explication** (mode Apprendre) : Dans la tradition voltairienne, le droit de critiquer les croyances, jusqu'au blasphème, est une conquête ; le droit français ne punit pas le blasphème mais sanctionne les injures visant des personnes. Charles Taylor plaide pour une politique de la reconnaissance attentive aux minorités, ce qui peut passer par des accommodements comme les jours fériés.

##### B14a — Affirmation · Religion (REL) · inversé

> La critique des religions, y compris par la caricature, doit rester entièrement libre.

- **Chargements** (accord) : REL -0,6 ; CUL +0,4 ; REL.laicite +0,3

##### B14b — Affirmation · Religion (REL)

> Mieux vaut éviter de publier des caricatures qui blessent inutilement les croyants.

- **Chargements** (accord) : REL +0,5 ; CUL -0,2

##### B14c — Affirmation · Religion (REL)

> La loi devrait sanctionner les propos qui offensent une religion.

- **Chargements** (accord) : REL +0,7 ; GOV -0,3

##### B14d — Affirmation · Altérité (ALT)

> Les grandes fêtes de chaque religion présente en France devraient pouvoir être des jours fériés.

- **Chargements** (accord) : ALT +0,5 ; REL.laicite -0,5

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B15 — École et transmission

**Contexte** : À propos de l'école et de la transmission des convictions, que pensez-vous de ces affirmations ?

- **Thème** : ecole · **Auteurs** : Ferdinand Buisson et Aristide Briand ; Emmanuel Mounier et Jacques Maritain ; Alasdair MacIntyre
- **Explication** (mode Apprendre) : Les fondateurs de l'école laïque (Buisson) veulent former des esprits autonomes ; le personnalisme chrétien (Mounier, Maritain) et MacIntyre estiment que la morale se transmet dans des traditions vivantes. Le chèque éducation, défendu par Milton Friedman, oppose liberté de choix des familles et mixité sociale.

##### B15a — Affirmation · Religion (REL) · inversé

> L'État devrait cesser de financer les écoles privées confessionnelles.

- **Chargements** (accord) : REL -0,6 ; ECO +0,2

##### B15b — Affirmation · Religion (REL)

> Il est bon que des parents transmettent une foi à leurs enfants plutôt que les laisser choisir seuls.

- **Chargements** (accord) : REL +0,8

##### B15c — Affirmation · Religion (REL)

> Sans repères religieux, une société perd une partie de sa morale commune.

- **Chargements** (accord) : REL +0,8 ; CUL -0,3

##### B15d — Affirmation · Économie (ECO) · inversé

> Les parents devraient choisir librement l'école de leurs enfants, publique ou privée, grâce à un chèque éducation.

- **Chargements** (accord) : ECO -0,6 ; REL +0,2
- **Mesures du fichier 01** : chèque éducation et libre choix de l'établissement (David Lisnard, §3.11)

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### C07 — Question à choix · Religion (REL)

> Quelle conception de la laïcité est la plus proche de la vôtre ?

- **Option 1** : L'État est neutre, et les citoyens sont libres d'exprimer leur religion, y compris en public. — ALT +0,2 ; REL.laicite -0,6
- **Option 2** : La neutralité doit aussi s'appliquer dans l'école et les services publics, pour les usagers. — REL.laicite +0,6
- **Option 3** : Il faut réduire l'influence des religions dans la société. — REL -0,8 ; REL.laicite +0,5
- **Option 4** : L'État devrait reconnaître les religions et accepter des accommodements (horaires, menus, fêtes). — ALT +0,4 ; REL +0,2 ; REL.laicite -0,7
- **Option 5** : La laïcité doit d'abord protéger l'identité chrétienne de la France face à l'islam. — REL +0,6 ; ALT -0,6 ; REL.laicite +0,3
- **Option 6** : La loi devrait davantage s'inspirer des valeurs religieuses. — REL +0,9
- **Option ajoutée** : Aucune de ces réponses / je ne sais pas — exclue du calcul
- **Thème** : laicite
- **Auteurs** : Jean Baubérot et Henri Peña-Ruiz ; Patrick Buisson ; Jürgen Habermas
- **Explication** : Jean Baubérot décrit plusieurs « laïcités » : libérale, de combat, de reconnaissance, et aussi une « laïcité identitaire » mobilisée contre l'islam par une partie de la droite (Patrick Buisson). Habermas imagine une société post-séculière où les croyants participent au débat public.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### A07 — Répartition · État (ETA)

> Qu'est-ce que l'école devrait transmettre en priorité ? Répartissez 10 points.

- **Option 1** : Les savoirs fondamentaux (lire, écrire, compter) — CUL -0,2
- **Option 2** : L'esprit critique et la citoyenneté — CUL +0,3
- **Option 3** : L'histoire et la culture nationales — ETA -0,4
- **Option 4** : L'égalité des chances entre milieux sociaux — ECO +0,4
- **Option 5** : Des métiers et l'apprentissage — ECO -0,2
- **Option 6** : L'écologie et le respect du vivant — ENV +0,4
- **Option 7** : La discipline et le respect de l'autorité — SEC -0,3 ; CUL -0,3
- **Thème** : ecole
- **Auteurs** : Condorcet ; Pierre Bourdieu ; Alain Finkielkraut
- **Explication** : Condorcet voulait une instruction qui émancipe, et Pierre Bourdieu montre que l'école reproduit les inégalités. Alain Finkielkraut défend la transmission des savoirs contre le relativisme.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

## Nation, monde et mémoire

#### B16 — Commerce international

**Contexte** : Face à la concurrence internationale, quelle politique commerciale vous semble souhaitable ?

- **Thème** : mondialisation · **Auteurs** : David Ricardo ; Friedrich List ; Joseph Stiglitz et Dani Rodrik
- **Explication** (mode Apprendre) : David Ricardo a montré que l'échange profite à tous les partenaires ; Friedrich List que les pays aujourd'hui riches se sont d'abord protégés. Dani Rodrik souligne qu'une mondialisation poussée entre en tension avec la démocratie ; l'altermondialisme et l'écologie politique veulent des échanges moins nombreux et mieux régulés, à l'échelle nationale ou européenne.

##### B16a — Affirmation · État (ETA)

> Le libre-échange enrichit tous les pays : il faut continuer à ouvrir les marchés.

- **Chargements** (accord) : ETA +0,6 ; ECO -0,5

##### B16b — Affirmation · État (ETA) · inversé

> La France devrait protéger ses industries par ses propres droits de douane.

- **Chargements** (accord) : ETA -0,8 ; ECO +0,2
- **Mesures du fichier 01** : Protectionnisme écologique et social (François Ruffin, §3.9)

##### B16c — Affirmation · Union européenne (UE)

> C'est à l'échelle européenne qu'il faut protéger l'industrie, avec des taxes aux frontières de l'Union.

- **Chargements** (accord) : UE +0,6

##### B16d — Affirmation · Économie (ECO)

> Le commerce devrait obéir à des règles sociales et écologiques strictes, quitte à échanger beaucoup moins.

- **Chargements** (accord) : ECO +0,4 ; ENV +0,3

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B17 — La nation et le monde

**Contexte** : À propos de votre rapport à la nation et au reste du monde, que pensez-vous de ces affirmations ?

- **Thème** : identite · **Auteurs** : Emmanuel Kant ; Pierre Manent ; Léon Trotsky
- **Explication** (mode Apprendre) : Le cosmopolitisme, de Kant à Martha Nussbaum, fait de l'humanité la première communauté morale ; l'internationalisme ouvrier place la solidarité de classe au-dessus des frontières. Pierre Manent voit dans la nation le cadre indispensable de la démocratie ; le mot « mondialisme », employé par les souverainistes, désigne pour eux un projet d'effacement des nations.

##### B17a — Affirmation · État (ETA)

> Je me sens citoyen·ne du monde avant d'être citoyen·ne de mon pays.

- **Chargements** (accord) : ETA +1

##### B17b — Affirmation · État (ETA) · inversé

> Les intérêts des Français doivent passer avant ceux des autres peuples.

- **Chargements** (accord) : ETA -0,9 ; ALT -0,3
- **Mesures du fichier 01** : Référendum sur l'immigration et la « priorité nationale » (inscription constitutionnelle) (Marine Le Pen, §3.1)

##### B17c — Affirmation · État (ETA)

> Un ouvrier français a plus en commun avec un ouvrier étranger qu'avec un patron français.

- **Chargements** (accord) : ETA +0,6 ; ECO +0,5

##### B17d — Affirmation · État (ETA) · inversé

> Le « mondialisme » des élites menace la souveraineté des peuples.

- **Chargements** (accord) : ETA -0,7

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B18 — Souveraineté et coopération

**Contexte** : Lors de la dernière crise sanitaire, certains médicaments ont manqué. Que pensez-vous de ces orientations ?

- **Thème** : mondialisation · **Auteurs** : Robert Keohane et Joseph Nye ; Charles de Gaulle ; Amartya Sen
- **Explication** (mode Apprendre) : Keohane et Nye montrent que des problèmes globaux appellent des institutions communes ; la tradition gaulliste privilégie la coopération entre nations souveraines. Amartya Sen rappelle que le développement des autres pays est aussi une condition de la sécurité commune ; la relocalisation des biens essentiels a gagné des partisans à gauche comme à droite.

##### B18a — Affirmation · État (ETA) · inversé

> La France doit produire elle-même ses médicaments et biens essentiels, même s'ils coûtent plus cher.

- **Chargements** (accord) : ETA -0,6 ; ECO +0,3

##### B18b — Affirmation · État (ETA)

> Face aux pandémies et au climat, il faut des institutions internationales dotées de vrais pouvoirs.

- **Chargements** (accord) : ETA +0,8 ; GMO.multilateralisme -0,5

##### B18c — Affirmation · État (ETA)

> L'aide au développement des pays pauvres devrait être fortement augmentée.

- **Chargements** (accord) : ETA +0,7 ; ALT +0,2
- **Mesures du fichier 01** : APD −10 % (Bruno Retailleau, §3.5)

##### B18d — Affirmation · État (ETA) · inversé

> La France devrait coopérer avec d'autres nations souveraines plutôt que dépendre d'institutions supranationales.

- **Chargements** (accord) : ETA -0,5 ; UE -0,3

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B19 — Histoire nationale

**Contexte** : À propos de l'histoire de France et de sa transmission, que pensez-vous de ces affirmations ?

- **Thème** : memoire-coloniale · **Auteurs** : Aimé Césaire ; Ernest Renan ; Alain Finkielkraut
- **Explication** (mode Apprendre) : Aimé Césaire et les études postcoloniales soulignent les violences coloniales et leurs héritages ; Alain Finkielkraut craint une « repentance » qui délégitime la transmission. Ernest Renan rappelait qu'une nation repose sur des souvenirs partagés, mais aussi sur ce qu'elle choisit d'oublier.

##### B19a — Affirmation · Altérité (ALT)

> La France devrait reconnaître plus clairement les torts de la colonisation.

- **Chargements** (accord) : ALT +0,5 ; ETA +0,4
- **Mesures du fichier 01** : « histoire commune de la colonisation et de la décolonisation » (Raphaël Glucksmann, §3.7)

##### B19b — Affirmation · État (ETA) · inversé

> La France n'a pas à se repentir de son histoire : elle doit en être fière.

- **Chargements** (accord) : ETA -0,6 ; ALT -0,4

##### B19c — Affirmation · État (ETA) · inversé

> L'école devrait d'abord transmettre un récit national qui rassemble.

- **Chargements** (accord) : ETA -0,5 ; CUL -0,4

##### B19d — Affirmation · Altérité (ALT)

> Le racisme d'aujourd'hui est en partie un héritage de la colonisation.

- **Chargements** (accord) : ALT +0,7

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

## Mœurs, famille et identité

#### B20 — Fin de vie et bioéthique

**Contexte** : À propos de la fin de vie et de la procréation, que pensez-vous de ces positions ?

- **Thème** : fin-de-vie · **Auteurs** : John Stuart Mill ; Hans Jonas ; Catharine MacKinnon et Andrea Dworkin
- **Explication** (mode Apprendre) : John Stuart Mill fonde la liberté de disposer de sa vie tant qu'on ne nuit pas à autrui. Les opposants à l'aide à mourir, croyants ou non, craignent des pressions sur les plus vulnérables. L'opposition à la GPA réunit conservateurs et féministes abolitionnistes (MacKinnon, Dworkin) : elle ne se range pas sur un seul pôle.

##### B20a — Affirmation · Culture / mœurs (CUL)

> Une personne atteinte d'une maladie incurable devrait pouvoir obtenir une aide active à mourir.

- **Chargements** (accord) : CUL +0,8 ; REL -0,3
- **Mesures du fichier 01** : droit de mourir dans la dignité constitutionnalisé (Jean-Luc Mélenchon, §3.2)

##### B20b — Affirmation · Culture / mœurs (CUL) · inversé

> Il faut d'abord développer les soins palliatifs : l'aide à mourir ouvre une pente risquée.

- **Chargements** (accord) : CUL -0,6 ; REL +0,3

##### B20c — Affirmation · Culture / mœurs (CUL)

> La gestation pour autrui devrait être autorisée et encadrée en France.

- **Chargements** (accord) : CUL +0,8

##### B20d — Affirmation · Culture / mœurs (CUL) · inversé

> La gestation pour autrui est une marchandisation du corps des femmes qui doit rester interdite.

- **Chargements** (accord) : CUL -0,4
- **Mesures du fichier 01** : refus de la GPA (Jean-Luc Mélenchon, §3.2)

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B21 — Famille et genre

**Contexte** : À propos de la famille et des rapports entre les sexes, que pensez-vous de ces affirmations ?

- **Thème** : gpa-pma · **Auteurs** : Simone de Beauvoir ; Roger Scruton ; Judith Butler
- **Explication** (mode Apprendre) : Simone de Beauvoir et Judith Butler voient dans les rôles de genre des constructions sociales ; les féminismes parlent de « patriarcat » pour désigner une domination systémique. Roger Scruton et la pensée conservatrice défendent la famille comme institution héritée. Le mot « wokisme », employé par les critiques de certains courants antiracistes et féministes, est récusé par ceux qu'il désigne.

##### B21a — Affirmation · Culture / mœurs (CUL) · inversé

> Il est préférable pour un enfant d'être élevé par un père et une mère.

- **Chargements** (accord) : CUL -0,9 ; REL +0,2
- **Mesures du fichier 01** : PMA accessible aux personnes trans (Jean-Luc Mélenchon, §3.2)

##### B21b — Affirmation · Culture / mœurs (CUL)

> Le changement de sexe à l'état civil devrait être possible sur simple déclaration, sans passer par un juge.

- **Chargements** (accord) : CUL +0,8
- **Mesures du fichier 01** : changement de sexe à l'état civil déjudiciarisé (Jean-Luc Mélenchon, §3.2)

##### B21c — Affirmation · Culture / mœurs (CUL)

> Notre société reste organisée par une domination masculine, le patriarcat, qu'il faut combattre.

- **Chargements** (accord) : CUL +0,6 ; ALT +0,2

##### B21d — Affirmation · Culture / mœurs (CUL) · inversé

> Le « wokisme » menace la liberté d'expression et la transmission des savoirs à l'école.

- **Chargements** (accord) : CUL -0,7

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B22 — Mœurs et liberté

**Contexte** : À propos de la liberté individuelle et des normes collectives, que pensez-vous de ces affirmations ?

- **Thème** : cannabis · **Auteurs** : John Stuart Mill ; Edmund Burke ; Hannah Arendt
- **Explication** (mode Apprendre) : Le principe de non-nuisance de Mill fonde le libéralisme des mœurs ; Burke et la tradition conservatrice valorisent la sagesse des institutions héritées. Hannah Arendt voit dans la crise de l'autorité une crise de la transmission ; les partisans de la légalisation du cannabis invoquent l'échec de la prohibition, ses opposants la santé des jeunes.

##### B22a — Affirmation · Culture / mœurs (CUL)

> La consommation de cannabis par les adultes devrait être légalisée et encadrée par l'État.

- **Chargements** (accord) : CUL +0,8 ; SEC +0,3
- **Mesures du fichier 01** : légalisation du cannabis sous monopole d'État (Jean-Luc Mélenchon, §3.2) ; « tolérance zéro » envers les consommateurs (Édouard Philippe, §3.3)

##### B22b — Affirmation · Culture / mœurs (CUL) · inversé

> La société est allée trop loin dans la remise en cause des traditions.

- **Chargements** (accord) : CUL -0,9

##### B22c — Affirmation · Culture / mœurs (CUL) · inversé

> L'autorité des parents et des enseignants s'est trop affaiblie.

- **Chargements** (accord) : CUL -0,6 ; SEC -0,4

##### B22d — Affirmation · Culture / mœurs (CUL)

> Tant qu'on ne nuit à personne, chacun doit pouvoir vivre comme il l'entend, même si cela choque.

- **Chargements** (accord) : CUL +0,7 ; IDE -0,3

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B23 — Appartenances

**Contexte** : À propos de ce qui fait votre identité, que pensez-vous de ces affirmations ?

- **Thème** : identite · **Auteurs** : Charles Taylor ; Benjamin Constant ; Dominique Schnapper
- **Explication** (mode Apprendre) : Les communautariens (Taylor, MacIntyre) jugent que l'identité se forme dans des traditions qui précèdent l'individu ; les libéraux (Constant, Mill) valorisent la liberté de se choisir. L'universalisme républicain (Schnapper) veut une citoyenneté qui transcende les appartenances ; les défenseurs des langues régionales y voient une uniformité imposée.

##### B23a — Affirmation · Identité (IDE)

> Mes appartenances (famille, religion, région, communauté) définissent davantage qui je suis que mes choix personnels.

- **Chargements** (accord) : IDE +1

##### B23b — Affirmation · Identité (IDE) · inversé

> Chacun devrait pouvoir se définir librement, indépendamment de son origine ou de sa famille.

- **Chargements** (accord) : IDE -0,8 ; CUL +0,3

##### B23c — Affirmation · Identité (IDE) · inversé

> La loi ne devrait reconnaître que des individus, jamais des communautés.

- **Chargements** (accord) : IDE -0,8 ; ALT -0,2

##### B23d — Affirmation · Identité (IDE)

> Les langues et cultures régionales devraient bénéficier de droits propres (enseignement, statut officiel).

- **Chargements** (accord) : IDE +0,7

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B24 — Une famille en difficulté

**Contexte** : Une famille de votre quartier traverse de graves difficultés. À qui revient-il d'abord de l'aider ?

- **Thème** : solidarite · **Auteurs** : Doctrine sociale de l'Église ; William Beveridge ; Robert Nozick
- **Explication** (mode Apprendre) : La doctrine sociale de l'Église et Tocqueville valorisent les corps intermédiaires (principe de subsidiarité) ; Beveridge veut une solidarité nationale obligatoire, garantie par des droits. Robert Nozick fait de la responsabilité individuelle et des engagements volontaires la base d'une société juste ; d'autres réservent la solidarité à ceux qui partagent une même appartenance.

##### B24a — Affirmation · Identité (IDE)

> D'abord à la famille, aux voisins, aux associations ou aux paroisses.

- **Chargements** (accord) : IDE +0,7 ; ECO -0,3

##### B24b — Affirmation · Identité (IDE) · inversé

> À l'État, qui doit garantir des droits égaux pour tous sans dépendre de la charité.

- **Chargements** (accord) : IDE -0,6 ; ECO +0,5

##### B24c — Affirmation · Identité (IDE) · inversé

> Chacun est d'abord responsable de sa propre situation.

- **Chargements** (accord) : IDE -0,7 ; ECO -0,4

##### B24d — Affirmation · Identité (IDE)

> La solidarité doit d'abord s'exercer entre membres d'une même communauté (nation, culture ou religion).

- **Chargements** (accord) : IDE +0,7 ; ALT -0,3

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### C13 — Question à choix · Culture / mœurs (CUL)

> Quel modèle familial l'État devrait-il soutenir en priorité ?

- **Option 1** : La famille traditionnelle : un père et une mère mariés, avec leurs enfants. — CUL -0,9 ; REL +0,3
- **Option 2** : La natalité des familles françaises avant tout. — CUL -0,4 ; ALT -0,5
- **Option 3** : Les familles modestes d'abord, quel que soit leur modèle. — ECO +0,6
- **Option 4** : Toutes les formes de famille, à égalité. — CUL +0,8
- **Option 5** : Aucun : l'État n'a pas à privilégier un modèle de vie. — IDE -0,6 ; CUL +0,3
- **Option ajoutée** : Aucune de ces réponses / je ne sais pas — exclue du calcul
- **Thème** : famille
- **Auteurs** : Roger Scruton ; Simone de Beauvoir ; Christine Delphy
- **Explication** : Les conservateurs défendent la famille comme institution transmise, quand les féminismes (Beauvoir, Delphy) critiquent la division des rôles qu'elle organise. Le natalisme national relie famille et identité ; les libéraux refusent que l'État privilégie un modèle.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### C15 — Question à choix · Identité (IDE)

> En cas de désaccord entre la règle commune et les pratiques d'une minorité (religieuse, culturelle, régionale), l'État devrait…

- **Option 1** : … imposer la même règle à tous, sans exception. — IDE -0,7 ; TER -0,3
- **Option 2** : … négocier des accommodements raisonnables. — IDE +0,5 ; ALT +0,4
- **Option 3** : … laisser chaque communauté s'organiser selon ses propres règles. — IDE +0,9
- **Option 4** : … protéger d'abord la culture majoritaire du pays. — IDE +0,4 ; ALT -0,7
- **Option 5** : … laisser chaque individu choisir, sans règle collective. — IDE -0,8 ; CUL +0,4
- **Option ajoutée** : Aucune de ces réponses / je ne sais pas — exclue du calcul
- **Thème** : identite
- **Auteurs** : Charles Taylor ; Will Kymlicka et Bhikhu Parekh ; Dominique Schnapper
- **Explication** : Charles Taylor et le Québec ont popularisé les « accommodements raisonnables », et Will Kymlicka défend des droits collectifs pour les minorités. L'universalisme républicain (Schnapper) fait primer la règle commune ; d'autres privilégient la culture majoritaire ou la liberté individuelle pure.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

## Immigration et altérité

#### B25 — Immigration

**Contexte** : À propos de l'immigration en France, que pensez-vous de ces affirmations ?

- **Thème** : immigration · **Auteurs** : Hervé Le Bras et François Héran ; David Goodhart ; Ernest Renan
- **Explication** (mode Apprendre) : La deuxième affirmation a une dimension factuelle. L'expression « grand remplacement », forgée par Renaud Camus, désigne la thèse d'une substitution organisée de la population ; les démographes (Hervé Le Bras, François Héran) la réfutent, en rappelant que l'immigration transforme la population sans la remplacer. David Goodhart décrit l'inquiétude culturelle des « Somewheres » ; les partisans de l'immigration invoquent le vieillissement et les métiers en tension.

##### B25a — Affirmation · Altérité (ALT) · inversé

> L'immigration des dernières décennies a trop transformé la France.

- **Chargements** (accord) : ALT -0,8 ; CUL -0,2

##### B25b — Affirmation · Altérité (ALT) · inversé · dimension factuelle

> L'expression « grand remplacement » décrit une réalité démographique en cours en France.

- **Chargements** (accord) : ALT -1

##### B25c — Affirmation · Altérité (ALT)

> L'immigration est une chance économique et démographique pour la France.

- **Chargements** (accord) : ALT +0,8

##### B25d — Affirmation · Altérité (ALT) · inversé

> Il faut choisir les immigrés selon les besoins de l'économie, par des quotas, sans considération d'origine.

- **Chargements** (accord) : ALT -0,3 ; ECO -0,2
- **Mesures du fichier 01** : quotas d'immigration économique (Édouard Philippe, §3.3) ; quotas par secteur votés au Parlement (Gabriel Attal, §3.4)

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B26 — Droits des étrangers

**Contexte** : À propos des droits des étrangers et de la nationalité, que pensez-vous de ces mesures ?

- **Thème** : nationalite · **Auteurs** : Dominique Schnapper ; Will Kymlicka et Bhikhu Parekh ; Hervé Le Bras et François Héran
- **Explication** (mode Apprendre) : La « préférence nationale » veut réserver des protections financées par la collectivité aux nationaux ; ses opposants invoquent l'égalité devant la loi et les cotisations versées par les étrangers en situation régulière. Le droit du sol traduit une conception élective de la nation ; sa suppression voudrait que la nationalité résulte d'un choix et d'une adhésion.

##### B26a — Affirmation · Altérité (ALT) · inversé

> Les aides sociales devraient être réservées aux Français (« préférence nationale »).

- **Chargements** (accord) : ALT -0,8 ; ETA -0,5 ; ECO +0,2
- **Mesures du fichier 01** : Réserver les aides sociales aux Français et conditionner les prestations de solidarité à 5 ans de travail en France (Marine Le Pen, §3.1) ; suppression du regroupement familial, du droit du sol, des aides non contributives pour les extra-Européens (Éric Zemmour, §3.6) ; sortie de Schengen, suppression de l'AME, du droit du sol (référendum) et des aides non contributives pour les étrangers (Nicolas Dupont-Aignan, §3.12)

##### B26b — Affirmation · Altérité (ALT)

> Les étrangers sans titre de séjour qui travaillent en France depuis plusieurs années devraient être régularisés.

- **Chargements** (accord) : ALT +0,8
- **Mesures du fichier 01** : régularisation des travailleurs, étudiants et parents d'enfants scolarisés (Jean-Luc Mélenchon, §3.2) ; reconduites « plus ciblées », maintien de l'accueil humanitaire, régularisation (« faire nation par le faire ensemble ») (François Ruffin, §3.9)

##### B26c — Affirmation · Altérité (ALT) · inversé

> Un enfant né en France de parents étrangers ne devrait plus devenir français automatiquement.

- **Chargements** (accord) : ALT -0,8
- **Mesures du fichier 01** : Suppression du droit du sol (Marine Le Pen, §3.1) ; remise en cause du droit du sol automatique (David Lisnard, §3.11) ; suppression du regroupement familial, du droit du sol, des aides non contributives pour les extra-Européens (Éric Zemmour, §3.6)

##### B26d — Affirmation · Altérité (ALT)

> Les étrangers installés durablement devraient pouvoir voter aux élections municipales.

- **Chargements** (accord) : ALT +0,7 ; ETA +0,2
- **Mesures du fichier 01** : droit de vote des étrangers aux élections locales (programme 2022) (Jean-Luc Mélenchon, §3.2)

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B27 — Racisme et discriminations

**Contexte** : À propos du racisme et des discriminations en France, que pensez-vous de ces affirmations ?

- **Thème** : discriminations · **Auteurs** : Colette Guillaumin ; Racisme symbolique et moderne ; Stéphane Beaud et Gérard Noiriel
- **Explication** (mode Apprendre) : Les enquêtes par testing montrent des écarts persistants d'accès à l'emploi et au logement selon l'origine supposée. La notion de « racisme systémique » (Colette Guillaumin, théorie critique de la race) insiste sur les mécanismes institutionnels ; Beaud et Noiriel mettent en garde, depuis la gauche, contre l'oubli de la classe sociale. La « remigration » est une proposition issue des courants identitaires, reprise dans le débat électoral.

##### B27a — Affirmation · Altérité (ALT)

> Les discriminations liées à l'origine restent un problème important en France.

- **Chargements** (accord) : ALT +1

##### B27b — Affirmation · Altérité (ALT)

> Le racisme en France est systémique : il imprègne les institutions, pas seulement des individus.

- **Chargements** (accord) : ALT +0,8

##### B27c — Affirmation · Altérité (ALT) · inversé

> On parle trop de racisme : la France est l'un des pays les moins racistes du monde.

- **Chargements** (accord) : ALT -0,7

##### B27d — Affirmation · Altérité (ALT) · inversé

> Il faudrait une politique de « remigration » organisant le retour d'une partie des immigrés dans leur pays d'origine.

- **Chargements** (accord) : ALT -1
- **Mesures du fichier 01** : « remigration » et « immigration négative » (départs > arrivées) (Éric Zemmour, §3.6) ; ministère de la Remigration (Éric Zemmour, §3.6)

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B28 — Contrôles de police dans un quartier

**Contexte** : Dans un quartier populaire, les policiers contrôlent souvent les mêmes jeunes. Que pensez-vous de ces affirmations ?

- **Thème** : police-libertes · **Auteurs** : Michel Foucault ; Norbert Elias ; Pierre-André Taguieff
- **Explication** (mode Apprendre) : Des études et le Défenseur des droits documentent une probabilité de contrôle plus forte selon l'apparence ; les syndicats de police y voient le reflet de la géographie de la délinquance. Le mot « ensauvagement », employé par les partisans de la fermeté, et le mot « islamophobie », employé par une partie de la gauche et contesté par d'autres (Taguieff) au motif qu'il confondrait critique d'une religion et racisme, sont des marqueurs forts du débat.

##### B28a — Affirmation · Altérité (ALT)

> Les contrôles au faciès existent : il faut remettre un récépissé à chaque personne contrôlée.

- **Chargements** (accord) : ALT +0,6 ; SEC +0,4

##### B28b — Affirmation · Altérité (ALT) · inversé

> Les policiers contrôlent là où la délinquance est la plus forte : ce n'est pas du racisme.

- **Chargements** (accord) : ALT -0,5 ; SEC -0,4

##### B28c — Affirmation · Ordre et libertés (SEC) · inversé

> L'« ensauvagement » de certains quartiers justifie une présence policière massive et permanente.

- **Chargements** (accord) : SEC -0,7 ; ALT -0,3

##### B28d — Affirmation · Altérité (ALT)

> L'« islamophobie » est aujourd'hui une forme de racisme répandue en France.

- **Chargements** (accord) : ALT +0,7

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### C03 — Question à choix · Altérité (ALT)

> Quelle politique migratoire vous semble la plus souhaitable ?

- **Option 1** : Liberté de circulation et d'installation, sans frontières fermées. — ALT +1 ; ETA +0,5
- **Option 2** : Un accueil large, avec des régularisations et des voies légales d'immigration. — ALT +0,8
- **Option 3** : Le niveau actuel, avec une politique d'intégration renforcée. — ALT +0,2
- **Option 4** : Une immigration choisie selon les besoins de l'économie. — ALT -0,2 ; ECO -0,3
- **Option 5** : Une forte réduction de l'immigration, y compris familiale. — ALT -0,7
- **Option 6** : L'arrêt de l'immigration et le départ organisé d'une partie des immigrés (« remigration »). — ALT -1 ; ETA -0,3
- **Option ajoutée** : Aucune de ces réponses / je ne sais pas — exclue du calcul
- **Thème** : immigration
- **Auteurs** : Hervé Le Bras et François Héran ; David Goodhart ; Will Kymlicka et Bhikhu Parekh
- **Explication** : Les options vont du « no border » défendu par une partie de l'extrême gauche à la « remigration » des courants identitaires, en passant par l'immigration choisie et la réduction forte. François Héran plaide pour une politique fondée sur les données ; David Goodhart pour la prise en compte de l'attachement culturel.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### C10 — Question à choix · Altérité (ALT)

> Qu'est-ce qui fait avant tout qu'une personne est française ?

- **Option 1** : Adhérer aux valeurs de la République et parler la langue française. — IDE -0,4 ; ALT +0,2
- **Option 2** : Être né et avoir grandi en France. — ALT +0,5
- **Option 3** : Avoir des parents ou des ancêtres français. — ALT -0,8 ; IDE +0,5
- **Option 4** : Partager une culture, une histoire et une religion héritées. — IDE +0,6 ; ALT -0,5 ; REL +0,3
- **Option 5** : Avoir la nationalité, rien de plus : c'est un statut juridique. — IDE -0,6 ; ETA +0,3
- **Option 6** : Se sentir français : c'est un choix personnel. — IDE -0,6 ; ALT +0,4
- **Option ajoutée** : Aucune de ces réponses / je ne sais pas — exclue du calcul
- **Thème** : nationalite
- **Auteurs** : Ernest Renan ; Maurice Barrès ; Dominique Schnapper
- **Explication** : Deux conceptions de la nation s'opposent classiquement : la nation élective de Renan, « plébiscite de tous les jours », et la nation de « la terre et des morts » de Barrès. Dominique Schnapper décrit une communauté de citoyens ; d'autres réduisent la nationalité à un statut juridique ou à un sentiment.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

## Europe et relations internationales

#### B29 — L'Union européenne telle qu'elle est

**Contexte** : Pensez à l'Union européenne telle qu'elle fonctionne aujourd'hui, avec ses dirigeants et ses politiques actuelles.

- **Thème** : ue · **Auteurs** : Jacques Delors ; Giandomenico Majone et Wolfgang Streeck ; Philippe Séguin
- **Explication** (mode Apprendre) : Ce bloc porte sur l'Union actuelle, le suivant sur l'Europe que vous souhaiteriez : on peut soutenir l'idée européenne tout en rejetant la politique menée aujourd'hui. Wolfgang Streeck juge l'Union structurellement libérale ; Jacques Delors voulait une Europe sociale ; Philippe Séguin voyait dans les traités une dépossession de la souveraineté démocratique.

##### B29a — Affirmation · Union européenne (UE)

> La politique économique menée actuellement par l'Union européenne me convient globalement.

- **Chargements** (accord) : UE +0,6 ; ECO -0,3

##### B29b — Affirmation · Économie (ECO)

> L'Union actuelle est trop libérale, mais il faut la transformer de l'intérieur plutôt que la quitter.

- **Chargements** (accord) : UE +0,3 ; ECO +0,5

##### B29c — Affirmation · Union européenne (UE) · inversé

> L'Union européenne est irréformable : la France devrait en sortir.

- **Chargements** (accord) : UE -1
- **Mesures du fichier 01** : « sortie organisée » de l'UE (arrêt de la contribution nette ~15 Md€, frontières nationales, primauté du droit français) vers une « Europe des nations » (Nicolas Dupont-Aignan, §3.12) ; sortie de l'UE, de l'euro et de l'OTAN (François Asselineau, §3.14) ; Frexit comme mesure « non négociable » (Florian Philippot, §3.14)

##### B29d — Affirmation · Union européenne (UE) · inversé

> Le droit français devrait primer sur le droit européen, même contre les traités.

- **Chargements** (accord) : UE -0,8 ; ETA -0,4
- **Mesures du fichier 01** : primauté constitutionnelle du droit national sur le droit européen (Marine Le Pen, §3.1)

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B30 — L'Europe que vous souhaiteriez (affiché après B29)

**Contexte** : Imaginez maintenant une Union européenne dont les orientations politiques vous conviendraient.

- **Thème** : ue · **Auteurs** : Altiero Spinelli ; Charles de Gaulle ; Jürgen Habermas
- **Explication** (mode Apprendre) : Altiero Spinelli et Jürgen Habermas défendent une démocratie européenne post-nationale ; De Gaulle une « Europe des nations » qui coopèrent sans abandon de souveraineté. L'écart entre vos réponses aux deux blocs indique si votre position tient à l'Europe elle-même ou à la politique qu'elle mène aujourd'hui.

##### B30a — Affirmation · Union européenne (UE)

> Dans ce cas, je souhaiterais une Europe fédérale, avec un gouvernement et un budget communs.

- **Chargements** (accord) : UE +0,9
- **Mesures du fichier 01** : « saut fédéral », suppression du veto, élargissement (dont Ukraine), emprunt commun de 500 Md€, fonds européen de défense (Raphaël Glucksmann, §3.7) ; convention constituante pour refondre les traités, traité environnemental européen, Europe fédérale (Marine Tondelier, §3.8)

##### B30b — Affirmation · Union européenne (UE) · inversé

> Même dans ce cas, je préférerais une Europe des nations où chaque pays garde le dernier mot.

- **Chargements** (accord) : UE -0,7
- **Mesures du fichier 01** : refus du fédéralisme et des élargissements (Marine Le Pen, §3.1)

##### B30c — Affirmation · Union européenne (UE)

> L'Europe devrait se doter d'une défense commune, y compris d'une dissuasion nucléaire partagée.

- **Chargements** (accord) : UE +0,6 ; GMO -0,4
- **Thème** : dissuasion
- **Mesures du fichier 01** : extension de la dissuasion nucléaire française aux partenaires de l'UE (décision d'emploi française) (Raphaël Glucksmann, §3.7) ; Opposé à l'extension européenne de la dissuasion et à une armée européenne fédérale (Fabien Roussel, §3.10)

##### B30d — Affirmation · Union européenne (UE)

> L'Union devrait emprunter en commun pour financer la transition écologique et l'industrie.

- **Chargements** (accord) : UE +0,7 ; ECO +0,2
- **Mesures du fichier 01** : « saut fédéral », suppression du veto, élargissement (dont Ukraine), emprunt commun de 500 Md€, fonds européen de défense (Raphaël Glucksmann, §3.7)

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B31 — Guerre en Ukraine

**Contexte** : À propos de la guerre en Ukraine, que pensez-vous de ces positions ?

- **Thème** : otan-ukraine · **Auteurs** : Robert Kagan ; Hans Morgenthau, Kenneth Waltz et John Mearsheimer ; Michael Walzer
- **Explication** (mode Apprendre) : Pour Robert Kagan et les partisans d'un soutien accru, laisser une agression réussir menacerait toute l'Europe. Les réalistes (Mearsheimer) craignent l'escalade avec une puissance nucléaire et plaident pour un compromis ; Michael Walzer pose la question d'une paix juste, qui ne récompense pas l'agresseur.

##### B31a — Affirmation · Gouvernance mondiale (GMO) · inversé

> La France devrait augmenter fortement son aide militaire à l'Ukraine.

- **Chargements** (accord) : GMO -0,8 ; GMO.intervention -0,6
- **Mesures du fichier 01** : aide militaire à l'Ukraine « drastiquement » augmentée, soutien à la Moldavie et à l'Arménie (Raphaël Glucksmann, §3.7) ; fermeté face à la Russie, soutien à l'Ukraine, OTAN non remise en cause (Gabriel Attal, §3.4)

##### B31b — Affirmation · Gouvernance mondiale (GMO)

> La paix passe par une négociation, même si elle implique des concessions territoriales.

- **Chargements** (accord) : GMO +0,7 ; GMO.intervention +0,5
- **Mesures du fichier 01** : gaullisme diplomatique, priorité à la négociation en Ukraine, distance critique envers l'OTAN, renforcement de l'ONU et de la CPI (Dominique de Villepin, §3.14)

##### B31c — Affirmation · Gouvernance mondiale (GMO) · inversé

> La France devrait être prête à envoyer des troupes pour garantir un accord de paix.

- **Chargements** (accord) : GMO -0,7 ; UE +0,2

##### B31d — Affirmation · Gouvernance mondiale (GMO)

> Cette guerre ne concerne pas la France : elle devrait rester neutre.

- **Chargements** (accord) : GMO +0,8

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B32 — Alliances et interventions

**Contexte** : À propos de la place de la France dans le monde, que pensez-vous de ces affirmations ?

- **Thème** : otan-ukraine · **Auteurs** : Droit d'ingérence et responsabilité de protéger ; Hubert Védrine ; Immanuel Wallerstein et Noam Chomsky
- **Explication** (mode Apprendre) : La « responsabilité de protéger » veut que la souveraineté cède devant les crimes de masse ; Hubert Védrine se méfie d'un interventionnisme moralisateur. Noam Chomsky et la gauche anti-impérialiste voient dans beaucoup d'interventions la défense d'intérêts de puissance ; la tradition gaulliste défend une France indépendante des blocs. Le mot « impérialisme », hérité de Lénine, désigne pour ceux qui l'emploient une politique de domination d'une puissance sur d'autres pays ; ses critiques lui reprochent d'ignorer les appels à l'aide des populations menacées.

##### B32a — Affirmation · Gouvernance mondiale (GMO)

> La France devrait quitter l'OTAN.

- **Chargements** (accord) : GMO +0,6 ; GMO.multilateralisme +0,8
- **Mesures du fichier 01** : sortie de l'OTAN « par étapes » (réaffirmée sur LCI le 08/05/2026), d'abord du commandement intégré (Jean-Luc Mélenchon, §3.2) ; sortie de l'UE, de l'euro et de l'OTAN (François Asselineau, §3.14) ; Sortie du commandement intégré de l'OTAN (position constante depuis 2017, reportée tant que dure la guerre en Ukraine en 2022) (Marine Le Pen, §3.1)

##### B32b — Affirmation · Gouvernance mondiale (GMO) · inversé

> La France doit être prête à intervenir militairement pour empêcher des crimes de masse à l'étranger.

- **Chargements** (accord) : GMO -0,9 ; GMO.intervention -0,8

##### B32c — Affirmation · Gouvernance mondiale (GMO)

> La France devrait être non alignée, à égale distance des États-Unis, de la Chine et de la Russie.

- **Chargements** (accord) : GMO +0,6 ; GMO.multilateralisme +0,6
- **Mesures du fichier 01** : non-alignement (Jean-Luc Mélenchon, §3.2)

##### B32d — Affirmation · Gouvernance mondiale (GMO)

> Les interventions militaires occidentales relèvent souvent d'un impérialisme déguisé.

- **Chargements** (accord) : GMO +0,7 ; ECO +0,2

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### C05 — Question à choix · Union européenne (UE)

> Quel avenir souhaitez-vous pour la France dans l'Union européenne ?

- **Option 1** : Une fédération européenne, avec un gouvernement commun. — UE +1
- **Option 2** : Une Union maintenue mais réorientée vers le social et l'écologie. — UE +0,4 ; ECO +0,4
- **Option 3** : L'Union telle qu'elle est, avec des réformes ponctuelles. — UE +0,4 ; ECO -0,2
- **Option 4** : Une Europe des nations, où l'Union rend des compétences aux États. — UE -0,6
- **Option 5** : Rester dans l'Union mais désobéir aux traités qui bloquent nos choix. — UE -0,5 ; ECO +0,3
- **Option 6** : Sortir de l'Union européenne (Frexit). — UE -1 ; ETA -0,3
- **Option ajoutée** : Aucune de ces réponses / je ne sais pas — exclue du calcul
- **Thème** : ue
- **Auteurs** : Altiero Spinelli ; Frédéric Lordon ; Philippe Séguin
- **Explication** : Du fédéralisme de Spinelli au Frexit, en passant par la « désobéissance » aux traités défendue par une partie de la gauche (Lordon) et l'Europe des nations de tradition gaulliste (Séguin). Vous pouvez choisir en pensant à l'Union réelle, pas seulement à l'idéal.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### C06 — Question à choix · Gouvernance mondiale (GMO)

> Si un pays voisin de l'Union européenne était envahi demain, la France devrait d'abord…

- **Option 1** : … envoyer des troupes aux côtés de ses alliés. — GMO -0,9 ; GMO.intervention -0,8
- **Option 2** : … livrer des armes et sanctionner l'agresseur, sans combattre elle-même. — GMO -0,5 ; GMO.intervention -0,3
- **Option 3** : … n'agir que dans le cadre d'une décision de l'ONU. — GMO -0,2 ; GMO.multilateralisme -0,7
- **Option 4** : … pousser à une négociation rapide, même au prix de concessions. — GMO +0,6 ; GMO.intervention +0,5
- **Option 5** : … rester strictement neutre. — GMO +0,9 ; ETA -0,3
- **Option ajoutée** : Aucune de ces réponses / je ne sais pas — exclue du calcul
- **Thème** : defense
- **Auteurs** : Michael Walzer ; Robert Keohane et Joseph Nye ; Hubert Védrine
- **Explication** : La théorie de la guerre juste (Walzer) encadre le recours à la force, et le multilatéralisme (Keohane, Nye) le subordonne aux institutions internationales. Le réalisme et le pacifisme privilégient la négociation ou la neutralité.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### A03 — Répartition · Gouvernance mondiale (GMO)

> Répartissez 10 points entre ces priorités de politique étrangère.

- **Option 1** : Soutenir l'Ukraine et les alliés européens — GMO -0,5 ; UE +0,2
- **Option 2** : Construire une défense européenne — UE +0,4 ; GMO -0,2
- **Option 3** : Aide au développement et coopération — ETA +0,4
- **Option 4** : Diplomatie et non-alignement — GMO +0,5
- **Option 5** : Protection des frontières nationales — ALT -0,3 ; ETA -0,3
- **Thème** : defense
- **Auteurs** : Raymond Aron ; Hubert Védrine
- **Explication** : Raymond Aron distinguait puissance, sécurité et prestige comme objectifs des États. Ces priorités traduisent des conceptions différentes de l'intérêt national.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### A04 — Répartition · Union européenne (UE)

> Répartissez 10 points entre les domaines où l'Union européenne devrait agir davantage, ou pas du tout.

- **Option 1** : Aucun : rendre des compétences aux États — UE -0,6
- **Option 2** : Défense commune — UE +0,5
- **Option 3** : Climat et énergie — UE +0,3 ; ENV +0,3
- **Option 4** : Protection sociale et salaires minimums — UE +0,3 ; ECO +0,3
- **Option 5** : Contrôle des frontières extérieures — UE +0,2 ; ALT -0,3
- **Option 6** : Protection de l'industrie face à la concurrence mondiale — UE +0,2 ; ETA -0,2
- **Thème** : ue
- **Auteurs** : Jacques Delors ; Giandomenico Majone et Wolfgang Streeck
- **Explication** : Jacques Delors voulait une Europe qui protège autant qu'elle ouvre. Wolfgang Streeck juge au contraire qu'elle soustrait l'économie aux choix démocratiques.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

## Démocratie, pouvoir et changement

#### B33 — Si le gouvernement était du camp opposé

**Contexte** : Imaginez que le prochain gouvernement soit issu du camp politique le plus éloigné du vôtre.

- **Thème** : democratie · **Auteurs** : Montesquieu ; Juan Linz, Steven Levitsky et Daniel Ziblatt ; Jean-Jacques Rousseau
- **Explication** (mode Apprendre) : Ce bloc et le suivant posent les mêmes questions dans deux contextes opposés. Il est humain de vouloir plus de contre-pouvoirs face à un adversaire ; Montesquieu, Levitsky et Ziblatt rappellent que des règles ne protègent que si elles s'appliquent à tous les camps. Rousseau fonde au contraire la légitimité sur la volonté générale du peuple souverain.

##### B33a — Affirmation · Gouvernance (GOV)

> Les juges devraient pouvoir censurer ses lois contraires à la Constitution.

- **Chargements** (accord) : GOV +0,7

##### B33b — Affirmation · Gouvernance (GOV)

> La presse et l'opposition devraient pouvoir le critiquer en toute liberté.

- **Chargements** (accord) : GOV +0,7

##### B33c — Affirmation · Gouvernance (GOV) · inversé

> S'il a été élu, il doit pouvoir appliquer son programme sans que juges ou experts l'en empêchent.

- **Chargements** (accord) : GOV -0,7

##### B33d — Affirmation · Mode de changement (CHG)

> Des blocages, des grèves massives ou la désobéissance civile seraient légitimes pour lui résister.

- **Chargements** (accord) : CHG +0,6

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B34 — Si le gouvernement était de votre camp (affiché après B33)

**Contexte** : Imaginez maintenant que le prochain gouvernement soit issu de votre camp politique.

- **Thème** : democratie · **Auteurs** : Robert Dahl ; Carl Schmitt ; Hannah Arendt
- **Explication** (mode Apprendre) : Robert Dahl fait des contre-pouvoirs une condition de la démocratie ; Carl Schmitt définit le souverain comme celui qui décide de l'exception. Hannah Arendt rappelle qu'un pouvoir sans limites détruit l'espace public qui permettait de le contester. L'écart entre vos réponses aux deux blocs mesure si votre attachement aux contre-pouvoirs dépend du camp au pouvoir.

##### B34a — Affirmation · Gouvernance (GOV) · même énoncé que B33a

> Les juges devraient pouvoir censurer ses lois contraires à la Constitution.

- **Chargements** (accord) : GOV +0,7

##### B34b — Affirmation · Gouvernance (GOV) · inversé

> Il devrait pouvoir gouverner par ordonnances ou par référendum pour aller vite, même contre l'avis du Conseil constitutionnel.

- **Chargements** (accord) : GOV -0,8
- **Mesures du fichier 01** : l'entourage évoque le référendum comme moyen d'« enjamber » le Conseil constitutionnel (Marine Le Pen, §3.1) ; dissolution de l'Assemblée dès l'élection et trois référendums : dose de capitalisation dans les retraites, règle d'or budgétaire, habilitation à légiférer par ordonnances (santé, éducation, justice) (Lille, mars 2026) (Édouard Philippe, §3.3)

##### B34c — Affirmation · Gouvernance (GOV) · inversé

> En cas de crise grave, il devrait pouvoir suspendre certaines libertés publiques sans contrôle du juge.

- **Chargements** (accord) : GOV -0,8 ; SEC -0,3

##### B34d — Affirmation · Gouvernance (GOV)

> Les contre-pouvoirs (juges, presse, associations) sont indispensables, même quand ils freinent mon camp.

- **Chargements** (accord) : GOV +0,8 ; POP +0,3

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B35 — Le peuple et les élites

**Contexte** : À propos du pouvoir et de la représentation, que pensez-vous de ces affirmations ?

- **Thème** : populisme · **Auteurs** : Cas Mudde et Jan-Werner Müller ; Ernesto Laclau et Chantal Mouffe ; Christopher Lasch
- **Explication** (mode Apprendre) : Ces énoncés reprennent les échelles de populisme de Cas Mudde et d'Agnes Akkerman. Laclau et Mouffe veulent construire un « peuple » contre l'« oligarchie » ; Christopher Lasch décrit la sécession des élites. Jan-Werner Müller objecte que parler au nom du peuple tout entier nie la légitimité des désaccords.

##### B35a — Affirmation · Populisme (POP) · inversé

> Les responsables politiques sont déconnectés des préoccupations des gens ordinaires.

- **Chargements** (accord) : POP -0,7

##### B35b — Affirmation · Populisme (POP) · inversé

> Le peuple, et non les responsables politiques, devrait prendre les décisions les plus importantes.

- **Chargements** (accord) : POP -0,7

##### B35c — Affirmation · Populisme (POP)

> En démocratie, il est important de faire des compromis entre des points de vue différents.

- **Chargements** (accord) : POP +0,8

##### B35d — Affirmation · Populisme (POP) · inversé

> Une oligarchie de grandes fortunes et de dirigeants confisque le pouvoir au peuple.

- **Chargements** (accord) : POP -0,6 ; ECO +0,4

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B36 — Adversaires et information

**Contexte** : À propos du débat démocratique et de l'information, que pensez-vous de ces affirmations ?

- **Thème** : populisme · **Auteurs** : Jonathan Haidt ; Immanuel Wallerstein et Noam Chomsky ; Claude Lefort
- **Explication** (mode Apprendre) : Jonathan Haidt montre que les convictions reposent sur des intuitions morales différentes, toutes compréhensibles. Noam Chomsky analyse la « fabrication du consentement » par les médias ; la défense d'une « démocratie militante » qui interdit certains partis divise même les libéraux. Claude Lefort rappelle qu'en démocratie, nul ne peut prétendre incarner seul le peuple.

##### B36a — Affirmation · Populisme (POP)

> Ceux qui ne partagent pas mes opinions politiques ont souvent de bonnes raisons de penser ce qu'ils pensent.

- **Chargements** (accord) : POP +0,8

##### B36b — Affirmation · Populisme (POP) · inversé

> Certains partis devraient être interdits parce qu'ils menacent la démocratie.

- **Chargements** (accord) : POP -0,5 ; GOV -0,2

##### B36c — Affirmation · Populisme (POP) · inversé

> Les grands médias défendent les intérêts des puissants plutôt que ceux du public.

- **Chargements** (accord) : POP -0,6

##### B36d — Affirmation · Populisme (POP)

> Les scientifiques et les experts devraient peser davantage dans les décisions publiques.

- **Chargements** (accord) : POP +0,5

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B39 — Institutions

**Contexte** : À propos des institutions de la République, que pensez-vous de ces réformes ?

- **Thème** : referendum-conseil-constitutionnel · **Auteurs** : Charles de Gaulle ; Jean-Jacques Rousseau ; Cornelius Castoriadis
- **Explication** (mode Apprendre) : De Gaulle a voulu un exécutif fort pour mettre fin à l'instabilité de la IVe République. Rousseau et Castoriadis défendent une souveraineté exercée directement par les citoyens ; la proportionnelle représente mieux la diversité des opinions mais oblige aux coalitions.

##### B39a — Affirmation · Institutions (INS)

> Les citoyens devraient pouvoir déclencher un référendum par pétition (référendum d'initiative citoyenne).

- **Chargements** (accord) : INS +0,8 ; POP -0,3
- **Mesures du fichier 01** : RIC (y compris révocatoire) (Jean-Luc Mélenchon, §3.2) ; RIC (Nicolas Dupont-Aignan, §3.12) ; RIC, proportionnelle (Marine Le Pen, §3.1) ; démocratie directe / référendum d'initiative citoyenne (Clara Egger, §3.14)

##### B39b — Affirmation · Institutions (INS)

> Les députés devraient être élus à la proportionnelle.

- **Chargements** (accord) : INS +0,7
- **Mesures du fichier 01** : proportionnelle (Jean-Luc Mélenchon, §3.2) ; RIC, proportionnelle (Marine Le Pen, §3.1)

##### B39c — Affirmation · Institutions (INS) · inversé

> Le président de la République doit garder un rôle central : c'est la force de la Ve République.

- **Chargements** (accord) : INS -0,8 ; CHG -0,3

##### B39d — Affirmation · Institutions (INS)

> Il faut une VIe République, rédigée par une Assemblée constituante élue.

- **Chargements** (accord) : INS +0,7
- **Mesures du fichier 01** : VIe République par Assemblée constituante (Jean-Luc Mélenchon, §3.2)

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B40 — Qui décide ?

**Contexte** : Pour les grandes décisions publiques, que pensez-vous de ces méthodes ?

- **Thème** : democratie · **Auteurs** : Bernard Manin et Yves Sintomer ; Joseph Schumpeter ; Pierre Rosanvallon
- **Explication** (mode Apprendre) : Bernard Manin et Yves Sintomer rappellent que le tirage au sort était la procédure démocratique par excellence à Athènes. Joseph Schumpeter défend une démocratie de compétition entre élites responsables devant les électeurs ; Pierre Rosanvallon analyse les formes de contrôle citoyen entre les élections.

##### B40a — Affirmation · Institutions (INS)

> Des citoyens tirés au sort devraient participer aux grandes décisions, comme dans les conventions citoyennes.

- **Chargements** (accord) : INS +0,8

##### B40b — Affirmation · Institutions (INS) · inversé

> Les grandes décisions doivent rester aux élus, qui en répondent devant les électeurs.

- **Chargements** (accord) : INS -0,8 ; CHG -0,3

##### B40c — Affirmation · Institutions (INS) · inversé

> Pour réformer vite, le gouvernement devrait pouvoir légiférer davantage par ordonnances.

- **Chargements** (accord) : INS -0,7 ; GOV -0,3
- **Mesures du fichier 01** : dissolution de l'Assemblée dès l'élection et trois référendums : dose de capitalisation dans les retraites, règle d'or budgétaire, habilitation à légiférer par ordonnances (santé, éducation, justice) (Lille, mars 2026) (Édouard Philippe, §3.3)

##### B40d — Affirmation · Institutions (INS)

> Le vote devrait être obligatoire et le vote blanc reconnu comme un suffrage exprimé.

- **Chargements** (accord) : INS +0,4
- **Mesures du fichier 01** : vote obligatoire et reconnaissance du vote blanc (Jean-Luc Mélenchon, §3.2)

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B42 — Comment changer la société ?

**Contexte** : Pour faire avancer une cause à laquelle on tient, quelles méthodes vous semblent légitimes ?

- **Thème** : changement · **Auteurs** : Eduard Bernstein ; Rosa Luxemburg ; Andreas Malm et Kohei Saito
- **Explication** (mode Apprendre) : Eduard Bernstein a fondé la social-démocratie sur la réforme graduelle ; Rosa Luxemburg lui répondait que seule une rupture transformerait la société. La désobéissance civile, de Thoreau à Martin Luther King, accepte la sanction pour faire reconnaître une injustice ; Andreas Malm légitime le sabotage d'infrastructures fossiles, ce que d'autres écologistes refusent.

##### B42a — Affirmation · Mode de changement (CHG) · inversé

> Seules les élections et les réformes votées au Parlement sont des voies légitimes de changement.

- **Chargements** (accord) : CHG -0,8 ; GOV +0,3

##### B42b — Affirmation · Mode de changement (CHG)

> Une révolution, y compris hors du cadre légal, peut être nécessaire pour renverser un ordre injuste.

- **Chargements** (accord) : CHG +0,9

##### B42c — Affirmation · Mode de changement (CHG)

> La désobéissance civile non violente (blocages, occupations) est légitime pour des causes comme le climat.

- **Chargements** (accord) : CHG +0,6

##### B42d — Affirmation · Mode de changement (CHG)

> Le sabotage d'installations polluantes peut être légitime face à l'urgence climatique.

- **Chargements** (accord) : CHG +0,8

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B44 — Changer de régime ?

**Contexte** : Certains pensent que le pays a besoin d'un changement profond. Que pensez-vous de ces positions ?

- **Thème** : changement · **Auteurs** : Edmund Burke ; Hannah Arendt ; Cornelius Castoriadis
- **Explication** (mode Apprendre) : Burke et Oakeshott défendent la réforme prudente. L'appel à un chef qui incarne la nation au-dessus des partis et des classes est au cœur des doctrines fascistes et, plus largement, national-autoritaires, dont Hannah Arendt a analysé les ressorts. La démocratie des conseils et des mandats révocables, défendue par Castoriadis, se réclame de la Commune de Paris.

##### B44a — Affirmation · Gouvernance (GOV) · inversé

> Seul un pouvoir autoritaire pourrait redresser le pays, comme à certaines périodes de l'histoire.

- **Chargements** (accord) : GOV -0,9

##### B44b — Affirmation · Mode de changement (CHG) · inversé

> Il faut changer les choses progressivement, en préservant ce qui fonctionne.

- **Chargements** (accord) : CHG -0,8 ; CUL -0,2

##### B44c — Affirmation · Gouvernance (GOV) · inversé

> La nation a besoin d'un chef qui l'incarne, au-dessus des partis et des intérêts de classe.

- **Chargements** (accord) : GOV -0,8

##### B44d — Affirmation · Mode de changement (CHG)

> Le peuple devrait gouverner directement par des assemblées locales et des délégués révocables.

- **Chargements** (accord) : CHG +0,6 ; INS +0,4

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### C01 — Question à choix · Gouvernance (GOV)

> Quel régime politique vous semble le plus souhaitable ?

- **Option 1** : Une démocratie représentative avec des contre-pouvoirs forts (juges, presse, Parlement). — GOV +0,8
- **Option 2** : Une démocratie plus directe, où les citoyens votent régulièrement les lois par référendum. — INS +0,7 ; GOV +0,2 ; POP -0,2
- **Option 3** : Une démocratie des conseils : assemblées de travailleurs et d'habitants, délégués révocables. — INS +0,6 ; CHG +0,5 ; ECO +0,4
- **Option 4** : Une société sans État : une fédération de communes libres et autogérées. — TER +0,8 ; CHG +0,5
- **Option 5** : Un pouvoir fort et stable, dirigé par un chef qui incarne la nation. — GOV -0,9 ; ETA -0,4
- **Option 6** : Un gouvernement d'experts compétents, moins dépendant des élections. — GOV -0,4 ; POP +0,4 ; INS -0,4
- **Option ajoutée** : Aucune de ces réponses / je ne sais pas — exclue du calcul
- **Thème** : democratie
- **Auteurs** : Robert Dahl ; Cornelius Castoriadis ; Mikhaïl Bakounine
- **Explication** : Cette question ouvre l'éventail au-delà de l'opposition entre démocratie libérale et autoritarisme : démocratie directe (Rousseau), démocratie des conseils (Castoriadis, la Commune), anarchisme (Bakounine, Bookchin), pouvoir national-autoritaire (doctrines fascistes et bonapartistes), technocratie. Chacune a ses défenseurs et ses critiques.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### C12 — Question à choix · Populisme (POP)

> Qui détient réellement le pouvoir en France aujourd'hui ?

- **Option 1** : Les électeurs, par leurs votes. — POP +0,7
- **Option 2** : Les élus et le gouvernement, sous le contrôle des juges et de la presse. — POP +0,5 ; GOV +0,2
- **Option 3** : Une oligarchie financière et médiatique. — POP -0,7 ; ECO +0,4
- **Option 4** : La bourgeoisie, en tant que classe dominante. — ECO +0,7 ; POP -0,3
- **Option 5** : Bruxelles et les institutions européennes. — UE -0,6 ; POP -0,4
- **Option 6** : Les juges, les médias et une élite « bien-pensante » coupée du peuple. — POP -0,6 ; GOV -0,3 ; CUL -0,3
- **Option ajoutée** : Aucune de ces réponses / je ne sais pas — exclue du calcul
- **Thème** : populisme
- **Auteurs** : Robert Dahl ; Pierre Bourdieu ; Cas Mudde et Jan-Werner Müller
- **Explication** : Robert Dahl décrit une polyarchie où le pouvoir est dispersé ; Pierre Bourdieu et la tradition marxiste décrivent une domination de classe. Les mots « oligarchie » et « bourgeoisie » désignent, chez ceux qui les emploient, une minorité fortunée qui concentrerait le pouvoir économique et politique ; leurs contradicteurs y voient une simplification qui ignore la diversité des élites et le poids du vote. Les populismes de droite et de gauche désignent des élites différentes (financières, européennes, judiciaires ou médiatiques).

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### C14 — Question à choix · Mode de changement (CHG)

> Si vos idées devaient l'emporter, ce serait plutôt…

- **Option 1** : … par des réformes progressives votées au Parlement. — CHG -0,9
- **Option 2** : … par un changement lent des mentalités, avant la politique. — CHG -0,5
- **Option 3** : … par une victoire électorale et un programme radical appliqué vite. — CHG +0,3 ; GOV -0,2
- **Option 4** : … par des mobilisations massives : grèves, manifestations, occupations. — CHG +0,5 ; ECO +0,2
- **Option 5** : … par une révolution. — CHG +1
- **Option 6** : … par un pouvoir fort qui imposerait les réformes nécessaires. — GOV -0,8 ; CHG +0,3
- **Option ajoutée** : Aucune de ces réponses / je ne sais pas — exclue du calcul
- **Thème** : changement
- **Auteurs** : Eduard Bernstein ; Antonio Gramsci ; Lénine
- **Explication** : Bernstein défend la réforme, Gramsci la conquête préalable de l'hégémonie culturelle, Lénine la révolution conduite par un parti d'avant-garde. Le syndicalisme révolutionnaire mise sur la grève générale, les courants autoritaires sur un pouvoir fort.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

## Sécurité et justice

#### B37 — Un cambriolage de trop

**Contexte** : Un multirécidiviste commet un nouveau cambriolage. Que pensez-vous de ces réponses ?

- **Thème** : justice · **Auteurs** : Thomas Hobbes ; Michel Foucault ; Patricia Hill Collins, bell hooks et Angela Davis
- **Explication** (mode Apprendre) : La tradition sécuritaire, depuis Hobbes, fait de la protection des personnes la première mission de l'État. Michel Foucault et Angela Davis, figure de l'abolitionnisme carcéral, critiquent la prison comme institution ; entre les deux, l'individualisation des peines est un principe constitutionnel que les peines planchers limitent.

##### B37a — Affirmation · Ordre et libertés (SEC) · inversé

> Il faut des peines minimales automatiques pour les récidivistes.

- **Chargements** (accord) : SEC -0,8
- **Mesures du fichier 01** : peines planchers, fin des remises automatiques (Marine Le Pen, §3.1) ; peines planchers (Bruno Retailleau, §3.5) ; peines planchers ciblées (Édouard Philippe, §3.3)

##### B37b — Affirmation · Ordre et libertés (SEC)

> Le juge doit pouvoir adapter chaque peine à la personne et à la situation.

- **Chargements** (accord) : SEC +0,8

##### B37c — Affirmation · Ordre et libertés (SEC)

> La prison fabrique de la récidive : il faut développer d'autres sanctions.

- **Chargements** (accord) : SEC +0,7

##### B37d — Affirmation · Ordre et libertés (SEC) · inversé

> Il faut construire beaucoup plus de places de prison pour que toutes les peines soient exécutées.

- **Chargements** (accord) : SEC -0,7
- **Mesures du fichier 01** : 85 000 places de prison d'ici 2028 (Marine Le Pen, §3.1) ; 40 000 places, uniforme des détenus, prisons sous tutelle de l'Intérieur (Nicolas Dupont-Aignan, §3.12)

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### B38 — Police, libertés et technologies

**Contexte** : À propos des moyens de la sécurité publique, que pensez-vous de ces mesures ?

- **Thème** : ia-numerique · **Auteurs** : Shoshana Zuboff et Evgeny Morozov ; Thomas Hobbes ; Norbert Elias
- **Explication** (mode Apprendre) : Shoshana Zuboff met en garde contre une surveillance numérique généralisée ; les partisans de la reconnaissance faciale y voient un outil contre le terrorisme et la criminalité. Norbert Elias décrit le monopole étatique de la violence comme une pacification ; la question est de savoir qui contrôle ceux qui l'exercent. L'expression « violences policières » désigne, pour ceux qui l'emploient, des abus récurrents liés à l'organisation même de la police ; les syndicats de policiers la contestent et parlent de fautes individuelles, sanctionnées comme telles.

##### B38a — Affirmation · Ordre et libertés (SEC)

> La reconnaissance faciale automatisée dans l'espace public devrait être interdite.

- **Chargements** (accord) : SEC +0,8 ; GOV +0,2
- **Mesures du fichier 01** : interdiction de la reconnaissance faciale (Jean-Luc Mélenchon, §3.2) ; reconnaissance faciale (Bruno Retailleau, §3.5)

##### B38b — Affirmation · Ordre et libertés (SEC) · inversé

> Pour lutter contre le narcotrafic, l'État devrait pouvoir instaurer un état d'urgence dans certains quartiers.

- **Chargements** (accord) : SEC -0,8 ; GOV -0,3
- **Thème** : narcotrafic
- **Mesures du fichier 01** : « état d'urgence anti-trafics » avec bouclage des quartiers 24 h/24, blindés de gendarmerie et coupure des télécommunications, via réforme constitutionnelle (Bruno Retailleau, §3.5) ; « état d'urgence narco » limité dans le temps et l'espace (reconnaissance faciale ciblée) (Édouard Philippe, §3.3)

##### B38c — Affirmation · Ordre et libertés (SEC)

> Les violences policières sont un problème structurel qui exige une autorité de contrôle indépendante.

- **Chargements** (accord) : SEC +0,7
- **Mesures du fichier 01** : remplacement de l'IGPN par une autorité indépendante (Jean-Luc Mélenchon, §3.2)

##### B38d — Affirmation · Ordre et libertés (SEC) · inversé

> Les forces de l'ordre devraient bénéficier d'une présomption de légitime défense.

- **Chargements** (accord) : SEC -0,8
- **Mesures du fichier 01** : présomption de légitime défense pour les forces de l'ordre (Marine Le Pen, §3.1)

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### C08 — Question à choix · Ordre et libertés (SEC)

> Face à la délinquance, quelle devrait être la priorité ?

- **Option 1** : Des sanctions plus sévères et plus de places de prison. — SEC -0,9
- **Option 2** : L'expulsion des délinquants étrangers et le contrôle des frontières. — SEC -0,6 ; ALT -0,6
- **Option 3** : Plus de police de proximité et de prévention dans les quartiers. — SEC +0,1 ; ECO +0,2
- **Option 4** : S'attaquer aux causes sociales : pauvreté, école, emploi. — SEC +0,6 ; ECO +0,4
- **Option 5** : Légaliser certaines drogues pour assécher les trafics. — SEC +0,6 ; CUL +0,5
- **Option 6** : Sortir progressivement de la prison au profit de la réparation et de la médiation. — SEC +1
- **Option ajoutée** : Aucune de ces réponses / je ne sais pas — exclue du calcul
- **Thème** : justice
- **Auteurs** : Thomas Hobbes ; Michel Foucault ; Patricia Hill Collins, bell hooks et Angela Davis
- **Explication** : Les réponses vont de la fermeté pénale à l'abolitionnisme carcéral (Angela Davis), en passant par la prévention, l'approche sociale et la légalisation. Chacune repose sur un diagnostic différent des causes de la délinquance.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

## Territoires

#### B41 — Territoires

**Contexte** : À propos de l'organisation du territoire, que pensez-vous de ces orientations ?

- **Thème** : decentralisation · **Auteurs** : Alexis de Tocqueville ; Jean-Pierre Chevènement ; Murray Bookchin
- **Explication** (mode Apprendre) : La tradition girondine, de Tocqueville à Rocard, défend la décision au plus près des habitants ; Murray Bookchin pousse cette logique jusqu'à des communes fédérées. La tradition jacobine (Chevènement) voit dans l'État central le garant de l'égalité entre territoires.

##### B41a — Affirmation · Territoires (TER)

> Les régions devraient pouvoir adapter certaines lois nationales à leur territoire.

- **Chargements** (accord) : TER +0,8
- **Mesures du fichier 01** : décentralisation massive (David Lisnard, §3.11)

##### B41b — Affirmation · Territoires (TER) · inversé

> Les règles et les services publics doivent être les mêmes partout en France, décidés par l'État.

- **Chargements** (accord) : TER -0,8 ; ECO +0,2

##### B41c — Affirmation · Territoires (TER)

> Les communes devraient pouvoir s'administrer largement elles-mêmes et se fédérer librement entre elles.

- **Chargements** (accord) : TER +0,8

##### B41d — Affirmation · Territoires (TER) · inversé

> La décentralisation a surtout créé des inégalités entre territoires.

- **Chargements** (accord) : TER -0,7

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### A05 — Répartition · Territoires (TER)

> Pour les politiques du quotidien (écoles, transports, logement), répartissez 10 points selon le niveau qui devrait décider.

- **Option 1** : La commune ou l'intercommunalité — TER +0,5
- **Option 2** : Le département — TER +0,2
- **Option 3** : La région — TER +0,4
- **Option 4** : L'État — TER -0,6
- **Option 5** : L'Union européenne — UE +0,4 ; TER -0,2
- **Thème** : decentralisation
- **Auteurs** : Alexis de Tocqueville ; Jean-Jacques Rousseau
- **Explication** : Tocqueville voyait dans la commune « l'école primaire de la liberté ». La tradition jacobine fait de l'État le garant de l'égalité entre les territoires.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### A06 — Répartition · Ordre et libertés (SEC)

> Votre commune dispose d'un budget supplémentaire. Répartissez 10 points entre ces usages.

- **Option 1** : Police municipale et vidéoprotection — SEC -0,5
- **Option 2** : Écoles, crèches et cantines — ECO +0,3
- **Option 3** : Transports en commun et pistes cyclables — ENV +0,5
- **Option 4** : Associations et centres sociaux — ECO +0,3 ; IDE +0,2
- **Option 5** : Baisse des impôts locaux — ECO -0,5
- **Option 6** : Patrimoine, églises et fêtes traditionnelles — CUL -0,3 ; IDE +0,3
- **Thème** : services-publics
- **Auteurs** : Murray Bookchin ; Robert Putnam
- **Explication** : À l'échelle locale, les arbitrages révèlent des priorités concrètes : sécurité, services, écologie, lien social ou patrimoine. Robert Putnam souligne le rôle du tissu associatif dans la confiance ; Murray Bookchin fait de la commune le lieu premier de la démocratie.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

## Vos priorités

#### A01 — Répartition · Environnement (ENV)

> Répartissez 10 points entre ces priorités pour le prochain quinquennat.

- **Option 1** : Climat et biodiversité — ENV +0,5
- **Option 2** : Pouvoir d'achat — ECO +0,3
- **Option 3** : Sécurité — SEC -0,4
- **Option 4** : Réduction de la dette — ECO -0,4
- **Option 5** : Maîtrise de l'immigration — ALT -0,4
- **Option 6** : Santé et hôpital — ECO +0,2
- **Thème** : priorites
- **Auteurs** : Ronald Inglehart
- **Explication** : Cette répartition mesure l'importance que vous accordez aux enjeux : elle pondère la comparaison avec les candidat·es. Ronald Inglehart distingue priorités « matérialistes » (sécurité, revenu) et « postmatérialistes » (environnement, expression de soi).

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

#### A09 — Répartition · Économie (ECO)

> Quels combats vous semblent les plus importants aujourd'hui ? Répartissez 10 points.

- **Option 1** : Contre les inégalités sociales — ECO +0,5
- **Option 2** : Contre le racisme et les discriminations — ALT +0,5
- **Option 3** : Pour l'égalité entre les femmes et les hommes — CUL +0,3
- **Option 4** : Pour la défense de l'identité et des traditions — CUL -0,4 ; ALT -0,3
- **Option 5** : Contre l'insécurité — SEC -0,5
- **Option 6** : Pour le climat — ENV +0,5
- **Option 7** : Pour la liberté d'expression — GOV +0,3
- **Thème** : priorites
- **Auteurs** : Nancy Fraser ; Ronald Inglehart
- **Explication** : Nancy Fraser distingue les luttes pour la redistribution et les luttes pour la reconnaissance. Cette répartition indique lesquelles comptent le plus pour vous.

**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :

