# Boussole 2027

Application web de 100 questions qui situe chacun·e sur 10 axes principaux et 4 axes secondaires. Elle restitue ces positions sous forme de graphiques et de textes, avec les traditions intellectuelles proches, les meilleures objections et les tensions internes du profil. Elle propose enfin une comparaison **indicative** avec les candidat·es à l'élection présidentielle de 2027.

**Outil de réflexion, pas une consigne de vote.** Tout le calcul se fait dans le navigateur : aucune réponse n'est envoyée ni stockée par défaut, aucun cookie, aucun traceur, aucune police chargée depuis un tiers.

## Installation

Node.js 22 ou plus récent.

```bash
cd boussole-2027
npm install
npm run dev            # http://localhost:5173
npm run build          # vérification des types + build statique dans dist/
npm run preview        # sert dist/ sur http://localhost:4173
```

Le build est un site statique (routage par fragment `#/…`) déployable sur n'importe quel hébergeur statique (base relative `./`).

## Scripts

| Commande | Rôle |
|---|---|
| `npm test` | Tests unitaires (Vitest) : schémas, extraction, formule de score, bootstrap, distances, tensions, textes, neutralité (10 000 répondants), personas, linter, option LLM, psychométrie |
| `npm run test:e2e` | Tests Playwright : parcours complet, réseau, stockage, accessibilité (axe-core, WCAG 2.2 AA), charte (polices, part de jaune) |
| `npm run extract:candidates` | Fichier 01 → `src/data/candidates.json` et `measures.json` (+ rapport `scripts/reports/extract-candidates.md`) |
| `npm run extract:thinkers` | Fichier 02 → `src/data/thinkers.json` (+ rapport) |
| `npm run lint:questions` | Linter des 100 items |
| `npm run simulate:neutrality` | Test de neutralité |
| `npm run simulate:personas [runs] [sigma]` | Test des personas (candidat·es et archétypes) |
| `npm run audit:questions` | Génère `docs/AUDIT_QUESTIONS.md` pour relecture pluraliste |
| `npm run psychometrics -- pilote.csv` | Alpha, oméga, AFE sur des données pilotes (`--simuler N` pour un auto-test) |
| `npx tsx scripts/check-axis-levels.ts` | Contrôle des 70 textes par axe et niveau |

## Organisation

```
docs/        fichiers sources 01 et 02, METHODOLOGIE.md, AUDIT_QUESTIONS.md (généré), MISE_A_JOUR.md
scripts/     extraction, linter, simulations, audit, psychométrie
src/data/    axes, questions, candidates, measures, thinkers, archetypes, meta, texts/ (validés par Zod au chargement)
src/domain/  schémas Zod, chargement et références croisées, règles du linter
src/engine/  score, bootstrap, diagnostics, correspondances, indices, ACP, simulations, synthèse (moteur de règles)
src/state/   questionnaire, sauvegarde locale facultative, lien de partage (scores seulement)
src/ui/      composants de question, graphiques SVG, exports PNG/PDF, option LLM
src/pages/   accueil, questionnaire, résultats, méthodologie, confidentialité, profil partagé
src/styles/  tokens.css (unique source des couleurs et tailles de la charte), global.css
api/         interpret.ts : fonction serverless facultative (désactivée par défaut)
tests/       unit/ (Vitest), e2e/ (Playwright)
```

## Charte graphique

Les valeurs de la charte sont définies dans `src/styles/tokens.css`, le seul fichier autorisé à contenir des couleurs : un test échoue si une couleur hors palette apparaît ailleurs.

- **Couleurs** :
  - bleu foncé `#07072d` et sa variante `#000F2E` ;
  - bleu clair `#eaf0f9` ;
  - jaune `#ffc40b`, réservé aux accents et à la position de l'utilisateur·ice, jamais en texte sur fond clair ;
  - gris neutres et nuances de bleu dérivées pour les graphiques.
- **Polices** : Fraunces pour les titres (h1 à 35 px), Open Sans en 11 pt pour le texte, interligne 1,5. Toutes deux sont auto-hébergées via `@fontsource`.

## Option LLM (désactivée par défaut)

1. Au build du client : `VITE_ENABLE_LLM=true`.
2. Côté serveur, déployer `api/interpret.ts` (signature Web `Request → Response`) avec `ENABLE_LLM=true`, `ANTHROPIC_API_KEY` et, facultativement, `ANTHROPIC_MODEL` (défaut : `claude-opus-5-5`).

Seuls les scores entiers par axe sont envoyés, après accord explicite (schéma strict, aucune réponse individuelle). En cas de refus du modèle, le serveur Anthropic relance la requête sur un modèle de repli (`fallbacks: "default"`). En cas d'erreur, l'application conserve la synthèse produite localement.

## Mise à jour des candidat·es

Voir `docs/MISE_A_JOUR.md`. Données actuelles : fichier 01, état au 25 septembre 2026.
