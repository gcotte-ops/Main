/**
 * Génère QUESTIONNAIRE_V2.md à partir des fichiers JSON du questionnaire v2 (source de l'application).
 * Les contrôles (neutralité, personas, quotas) sont recalculés avec le moteur de l'application.
 * Usage : npx tsx docs/questionnaire-v2/build-md.ts
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import axes from '../../src/data/axes.json';
import candidates from '../../src/data/candidates.json';
import measures from '../../src/data/measures.json';
import thinkers from '../../src/data/thinkers.json';
import { buildQuestions, RUBRIQUES } from '../../scripts/build-questions';
import { loadDataset } from '../../src/domain/load';
import { lintQuestions } from '../../src/domain/lint';
import { simulateArchetypePersonas, simulateCandidatePersonas, simulateNeutrality } from '../../src/engine/simulate';
import { BLOCK_LABELS } from '../../src/state/quiz';

const DIR = import.meta.dirname;
type W = Record<string, number>;
interface Aff { id: string; texte: string; theme?: string; poids: W; mesures?: string[]; factuel?: boolean; paire?: string }
interface Bloc { id: string; titre: string; theme: string; contexte: string; suite_de?: string; affirmations: Aff[]; auteurs: string[]; explication: string }
interface Choix { id: string; theme: string; question: string; options: { texte: string; poids: W }[]; auteurs: string[]; explication: string }
const load = <T>(f: string) => JSON.parse(readFileSync(join(DIR, f), 'utf8')) as T;
const blocs = [...load<Bloc[]>('blocs-1.json'), ...load<Bloc[]>('blocs-2.json')];
const choix = load<Choix[]>('choix.json');
const reps = load<Choix[]>('repartitions.json');

const tname = new Map(thinkers.map((t) => [t.id, t.name]));
const cname = new Map(candidates.map((c) => [c.id, c.name]));
const mes = new Map(measures.map((m) => [m.id, m]));
const fmt = (w: W) => Object.entries(w).map(([a, v]) => `${a} ${v > 0 ? '+' : '−'}${Math.abs(v)}`).join(', ');
const who = (ids: string[]) => ids.map((id) => tname.get(id) ?? id).join(' ; ');
const measureLine = (ids: string[]) =>
  ids.map((id) => { const m = mes.get(id)!; return `${m.text} (${m.candidateIds.map((c) => cname.get(c)).join(', ')}, ${m.section}) \`${id}\``; }).join(' ; ');

const THEMES: [string, string[]][] = Object.entries(RUBRIQUES)
  .map(([r, ids]) => [BLOCK_LABELS[r] ?? r, ids.filter((id) => id.startsWith('B'))] as [string, string[]])
  .filter(([, ids]) => ids.length);
const byId = new Map(blocs.map((b) => [b.id, b]));
const placed = new Set(THEMES.flatMap(([, ids]) => ids));
const missing = blocs.filter((b) => !placed.has(b.id)).map((b) => b.id);
if (missing.length) throw new Error(`blocs non classés : ${missing.join(', ')}`);

const blocMd = (b: Bloc) => {
  const allMes = [...new Set(b.affirmations.flatMap((a) => a.mesures ?? []))];
  return [
    `### ${b.id} · ${b.titre}${b.suite_de ? ` (affiché juste après ${b.suite_de})` : ''}`,
    '',
    `**Contexte** : ${b.contexte}`,
    '',
    '| # | Affirmation | Poids |',
    '|---|---|---|',
    ...b.affirmations.map((a) => `| ${a.id.slice(-1)} | ${a.texte}${a.factuel ? ' *(dimension factuelle)*' : ''}${a.paire ? ` *(même énoncé que ${a.paire}, autre contexte)*` : ''}${a.theme ? ` *(thème : ${a.theme})*` : ''} | ${fmt(a.poids)} |`),
    '',
    `- **Auteurs** : ${who(b.auteurs)}`,
    ...(allMes.length ? [`- **Mesures du fichier 01** : ${measureLine(allMes)}`] : []),
    `- **Explication (mode Apprendre)** : ${b.explication}`,
    '',
  ].join('\n');
};
const choixMd = (c: Choix, kind: 'choix' | 'rep') => [
  `### ${c.id} · ${c.question}`,
  '',
  '| # | Option | Poids |',
  '|---|---|---|',
  ...c.options.map((o, i) => `| ${i + 1} | ${o.texte} | ${fmt(o.poids)} |`),
  ...(kind === 'choix' ? ['| — | Aucune de ces réponses / je ne sais pas | (exclu du calcul) |'] : []),
  '',
  `- **Auteurs** : ${who(c.auteurs)}`,
  `- **Explication (mode Apprendre)** : ${c.explication}`,
  '',
].join('\n');

const nAff = blocs.reduce((s, b) => s + b.affirmations.length, 0);
const axisRows = axes.filter((a) => a.enabled).map((a) => `| ${a.id} | ${a.label} | ${a.poleMinus} | ${a.polePlus} |${a.id === 'CHG' ? ' ajouté en v2 |' : ' |'}`);

// Contrôles recalculés avec le moteur de l'application (données générées par build-questions).
const d = loadDataset();
const { questions } = buildQuestions();
const lint = lintQuestions(questions, { axes: d.axes, candidates: d.candidates, measures: d.measures, thinkers: d.thinkers });
const neutral = simulateNeutrality(questions, 10_000);
const axisMeans = Object.entries(neutral.meanByAxis).filter(([k]) => !k.includes('.')).map(([, v]) => v!);
const allAgree = Object.entries(neutral.allAgree).filter(([k, v]) => !k.includes('.') && v != null).map(([, v]) => Math.abs(v!));
const personas = [...simulateArchetypePersonas(questions, d.archetypes, 100), ...simulateCandidatePersonas(questions, d.candidates, 100)].map((p) => p.top3Rate);
const pct = (x: number) => `${Math.round(100 * x)} %`;
const fr = (x: number) => x.toFixed(1).replace('.', ',').replace('-', '−');
const quotas = lint.stats.quotas as Record<string, { n: number }>;
const short = Object.entries(quotas).sort((a, b) => a[1].n - b[1].n).slice(0, 4).map(([a, q]) => `${a} (${q.n})`).join(', ');

const md = `# Boussole 2027 — Questionnaire, version 2 (document de travail)

_Document généré à partir de \`docs/questionnaire-v2/*.json\` par \`build-md.ts\`. Ces fichiers JSON sont la source du questionnaire de l'application (voir §4). Les contrôles sont recalculés à chaque génération avec le moteur de l'application._

## 1. Ce qui change par rapport à la version 1

| Retour | Réponse dans cette version |
|---|---|
| Beaucoup de réponses « dépendent du contexte » (Europe actuelle vs idéale ; gouvernement de mon camp ou du camp adverse). | Questions **dédoublées par contexte** : B29 (l'UE telle qu'elle est) / B30 (l'Europe souhaitée) ; B33 (gouvernement du camp opposé) / B34 (gouvernement de votre camp). L'écart entre les deux réponses est une information en soi (attachement « de principe » ou « selon la conjoncture »). |
| Affirmations : toujours **4 propositions**, chacune avec neutre / je ne sais pas / plutôt / tout à fait. | Toutes les affirmations sont regroupées en **${blocs.length} blocs de 4 affirmations** (${nAff} au total), qui couvrent des positions différentes plutôt que deux pôles. Chaque affirmation reçoit sa propre réponse. |
| Questions : **au moins 4 choix**, jamais deux propositions stéréotypées (ex. libre-échange). | Les 14 dilemmes à deux options sont supprimés. **${choix.length} questions à choix** proposent 5 à 7 options, plus « aucune de ces réponses ». Le libre-échange est traité par le bloc B16 (4 positions : libre-échange, protectionnisme national, protectionnisme européen, commerce sous conditions sociales et écologiques) et le choix C02. |
| Trop abstrait, pas assez appliqué au terrain. | Des **situations concrètes** : une usine qui délocalise (B03), une maternité qui ferme (B06), une zone à faibles émissions (B10), des agriculteurs qui manifestent (B11), une sortie scolaire (B13), des caricatures (B14), une famille en difficulté (B24), des contrôles au faciès (B28), un cambriolage de récidiviste (B37), un pays voisin envahi (C06), le budget de votre commune (A06). |
| Trop fermé, trop centré sur démocratie libérale vs autoritarisme ; il manque les volets révolutionnaire, anarchiste, fasciste. | Nouvelles options explicites : révolution et sabotage (B42), abolition du capitalisme ou de l'État (B43), pouvoir autoritaire, chef qui incarne la nation au-dessus des partis et des classes, démocratie des conseils (B44), six régimes au choix (C01), mode de changement (C14). **L'axe CHG** (réformiste ↔ révolutionnaire), prévu dans l'architecture, est activé. |
| Le vocabulaire réel manque (« grand remplacement », « lutte des classes »…). | Le vocabulaire en usage apparaît, **toujours dans une affirmation que le camp qui l'emploie pourrait signer**, et il est expliqué dans le mode Apprendre. Termes : lutte des classes, grand remplacement, remigration, préférence nationale, assistanat, écologie punitive, mondialisme, wokisme, patriarcat, racisme systémique, islamophobie, ensauvagement, violences policières, oligarchie, bourgeoisie, bien-pensants, impérialisme. |
| Répartitions de points : passer de 5 à 10. | **10 répartitions** : 5 conservées (A01 à A05) et 5 nouvelles (A06 budget communal, A07 école, A08 qui paie la transition, A09 combats prioritaires, A10 où économiser). |
| Fabien Roussel n'est pas si « socialiste ». | Hors questionnaire : son codage ECO +2 vient du fichier 01 (§3.10). À revoir au moment de la mise à jour des données candidat·es (par exemple +1,5), sans toucher au calcul. |
| Ne pas modifier l'algorithme. | Le calcul des scores, de la confiance, des correspondances et des graphiques est **inchangé** (voir §4 : deux ajouts de format seulement). |

## 2. Formats de réponse

- **Bloc d'affirmations** : un contexte, puis 4 affirmations. Pour chacune :
  **Pas du tout d'accord · Plutôt pas d'accord · Neutre · Plutôt d'accord · Tout à fait d'accord · Je ne sais pas**.
  « Neutre » compte comme une position centrale (0) ; « Je ne sais pas » exclut l'affirmation du calcul.
- **Question à choix** : une seule option parmi 5 à 7, plus « Aucune de ces réponses / je ne sais pas », qui est exclue du calcul.
- **Répartition** : 10 points à distribuer entre 5 à 7 options. Les répartitions pèsent sur les scores (faiblement) et sur l'importance des enjeux dans la comparaison avec les candidat·es.

**Durée estimée** : environ 35 minutes. ${blocs.length} blocs à environ 35 s chacun, ${choix.length} choix à 15 s, ${reps.length} répartitions à 30 s. Une version courte (environ 20 minutes, un bloc sur deux) pourra être proposée en option.

## 3. Conventions pour modifier ce document

- **Poids** : \`AXE +0.8\` signifie que l'accord (ou le choix de l'option) tire vers le pôle « + » de l'axe, avec un poids de 0,8 (entre 0 et 1). Un signe « − » tire vers le pôle « − ». Deux ou trois axes au plus par affirmation, le premier étant l'axe principal.
- **Facettes** (sous-indices) : \`REL.laicite\` (+ = laïcité stricte), \`ENV.nucleaire\` (+ = relance du nucléaire), \`GMO.intervention\` (+ = non-intervention), \`GMO.multilateralisme\` (+ = souverainisme stratégique).
- **Équilibre** : pour chaque axe, garder à peu près autant d'affirmations qui tirent vers « + » que vers « − ». Le contrôle échoue si un répondant « tout d'accord » dépasse ±25.
- **Rédaction** : 30 mots au plus par affirmation, une seule idée, pas de double négation, aucun nom de candidat·e ni de parti. Un terme marqué n'est employé que dans une affirmation que ses utilisateurs pourraient signer, et il est expliqué.
- **Identifiants** : \`B01a\`, \`C03\`, \`A07\`. Pour ajouter une affirmation, créer un nouvel identifiant plutôt que réutiliser un ancien.

### Axes

| Code | Axe | Pôle − | Pôle + | |
|---|---|---|---|---|
${axisRows.join('\n')}

## 4. Intégration dans l'application

- **Chaîne de travail** : modifier les fichiers JSON de ce dossier, puis lancer \`npm run build:questions\` (génère \`src/data/questions.json\` et \`src/data/groups.json\`), \`npm run lint:questions\`, \`npm test\`, \`npm run audit:questions\` et \`npx tsx docs/questionnaire-v2/build-md.ts\` (ce document). Un test échoue si les fichiers générés ne sont pas à jour.
- **Classement** : chaque bloc, choix ou répartition appartient à une rubrique (\`RUBRIQUES\` dans \`scripts/build-questions.ts\`). Les rubriques sont présentées dans un ordre tiré au hasard, les écrans aussi à l'intérieur de chaque rubrique ; les deux répartitions de priorités (A01, A09) viennent en dernier. Un bloc marqué \`suite_de\` (B30, B34) est toujours affiché juste après l'autre bloc de sa paire.
- **Calcul inchangé** : chaque affirmation se comporte exactement comme un item Likert de la version 1. Chaque répartition utilise la formule des allocations.
- **Choix à N options** : même formule que les dilemmes de la version 1 (contribution = 2 × poids de l'option choisie, maximum = 2 × plus grand poids en valeur absolue). « Aucune de ces réponses » exclut la question.
- **Blocs** : un regroupement d'affichage (4 affirmations par écran), sans effet sur le calcul. Un champ \`theme\` sur une affirmation remplace le thème du bloc (B11d, B30c, B38b).
- **Saillance** : seules les répartitions de la rubrique « priorités » (A01, A09) pondèrent la comparaison avec les candidat·es. Les autres répartitions mesurent des positions et comptent dans les scores.
- **Cohérence** : un même énoncé posé dans deux contextes (\`paire\`, B34a / B33a) et jugé en sens opposés est signalé dans les résultats.
- **Axe CHG** : activé, avec 5 textes de restitution et une position pour chacun des 18 archétypes.
- **Linter** : la liste de mots interdits est remplacée par la règle « vocabulaire marqué, porté par son camp et expliqué ». Le linter vérifie que le terme figure dans l'explication ; la relecture humaine (\`docs/AUDIT_QUESTIONS.md\`) vérifie que l'affirmation pourrait être signée par le camp qui l'emploie.
- **Contrôles** (moteur de l'application, recalculés à chaque génération) :
  - linter : ${lint.errors.length} erreur(s), ${lint.warnings.length} avertissement(s) ;
  - neutralité sur 10 000 répondants aléatoires : moyenne de chaque axe entre ${fr(Math.min(...axisMeans))} et +${fr(Math.max(...axisMeans))} ;
  - répondant « tout d'accord » : au plus ${Math.round(Math.max(...allAgree))} en valeur absolue ;
  - personas : les ${d.archetypes.length} archétypes et les candidat·es codé·es sur au moins 7 axes se retrouvent dans le top 3 dans ${Math.min(...personas) === Math.max(...personas) ? pct(Math.min(...personas)) : `${pct(Math.min(...personas)).replace(' %', '')} à ${pct(Math.max(...personas))}`} des tirages.

## 5. Points de vigilance

- **« Grand remplacement »** (B25b) : l'affirmation est marquée « dimension factuelle ». L'explication rappelle l'origine de l'expression et sa réfutation par les démographes. L'outil décrit une adhésion, il ne qualifie pas la personne.
- **Options national-autoritaires et révolutionnaires** (B42, B43, B44, C01, C14) : elles sont formulées pour que leurs partisans s'y reconnaissent. L'explication nomme les doctrines (fascisme, communisme révolutionnaire, anarchisme) sans jugement moral.
- **Axes les plus courts** (items dont c'est l'axe principal) : ${short}. Ce sont les axes à enrichir en priorité si vous ajoutez des blocs.

---

# Partie 1 — Blocs d'affirmations (${blocs.length} blocs, ${nAff} affirmations)

${THEMES.map(([t, ids]) => `## ${t}\n\n${ids.map((id) => blocMd(byId.get(id)!)).join('\n')}`).join('\n')}

# Partie 2 — Questions à choix (${choix.length})

${choix.map((c) => choixMd(c, 'choix')).join('\n')}

# Partie 3 — Répartitions de points (${reps.length})

${reps.map((c) => choixMd(c, 'rep')).join('\n')}
`;
writeFileSync(join(DIR, 'QUESTIONNAIRE_V2.md'), md);
console.log(`QUESTIONNAIRE_V2.md : ${blocs.length} blocs, ${nAff} affirmations, ${choix.length} choix, ${reps.length} répartitions, ${md.split(/\s+/).length} mots`);
