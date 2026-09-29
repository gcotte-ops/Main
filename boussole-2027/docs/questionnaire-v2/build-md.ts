/**
 * Génère QUESTIONNAIRE_V2.md à partir des fichiers JSON du brouillon v2.
 * Usage : npx tsx docs/questionnaire-v2/build-md.ts
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import axes from '../../src/data/axes.json';
import candidates from '../../src/data/candidates.json';
import measures from '../../src/data/measures.json';
import thinkers from '../../src/data/thinkers.json';

const DIR = import.meta.dirname;
type W = Record<string, number>;
interface Aff { id: string; texte: string; poids: W; mesures?: string[]; factuel?: boolean; paire?: string }
interface Bloc { id: string; titre: string; theme: string; contexte: string; affirmations: Aff[]; auteurs: string[]; explication: string }
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

const THEMES: [string, string[]][] = [
  ['Économie et travail', ['B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B43']],
  ['Écologie et énergie', ['B08', 'B09', 'B10', 'B11']],
  ['Religion et laïcité', ['B12', 'B13', 'B14', 'B15']],
  ['Nation, monde et mémoire', ['B16', 'B17', 'B18', 'B19']],
  ['Mœurs, famille et identité', ['B20', 'B21', 'B22', 'B23', 'B24']],
  ['Immigration et altérité', ['B25', 'B26', 'B27', 'B28']],
  ['Europe et relations internationales', ['B29', 'B30', 'B31', 'B32']],
  ['Démocratie, pouvoir et changement', ['B33', 'B34', 'B35', 'B36', 'B39', 'B40', 'B42', 'B44']],
  ['Sécurité et justice', ['B37', 'B38']],
  ['Territoires', ['B41']],
];
const byId = new Map(blocs.map((b) => [b.id, b]));
const placed = new Set(THEMES.flatMap(([, ids]) => ids));
const missing = blocs.filter((b) => !placed.has(b.id)).map((b) => b.id);
if (missing.length) throw new Error(`blocs non classés : ${missing.join(', ')}`);

const blocMd = (b: Bloc) => {
  const allMes = [...new Set(b.affirmations.flatMap((a) => a.mesures ?? []))];
  return [
    `### ${b.id} · ${b.titre}`,
    '',
    `**Contexte** : ${b.contexte}`,
    '',
    '| # | Affirmation | Poids |',
    '|---|---|---|',
    ...b.affirmations.map((a) => `| ${a.id.slice(-1)} | ${a.texte}${a.factuel ? ' *(dimension factuelle)*' : ''}${a.paire ? ` *(même énoncé que ${a.paire}, autre contexte)*` : ''} | ${fmt(a.poids)} |`),
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
const axisRows = axes.filter((a) => a.enabled || a.id === 'CHG').map((a) => `| ${a.id} | ${a.label} | ${a.poleMinus} | ${a.polePlus} |${a.id === 'CHG' ? ' **à activer** |' : ' |'}`);

const md = `# Boussole 2027 — Questionnaire, version 2 (brouillon de travail)

_Document de travail généré le 29 septembre 2026 à partir de \`docs/questionnaire-v2/*.json\` par \`build-md.ts\`. Contrôlé par \`check-v2.ts\` avec le moteur de calcul actuel (inchangé)._

## 1. Ce qui change par rapport à la version 1

| Retour | Réponse dans cette version |
|---|---|
| Beaucoup de réponses « dépendent du contexte » (Europe actuelle vs idéale ; gouvernement de mon camp ou du camp adverse). | Questions **dédoublées par contexte** : B29 (l'UE telle qu'elle est) / B30 (l'Europe souhaitée) ; B33 (gouvernement du camp opposé) / B34 (gouvernement de votre camp). L'écart entre les deux réponses est une information en soi (attachement « de principe » ou « selon la conjoncture »). |
| Affirmations : toujours **4 propositions**, chacune avec neutre / je ne sais pas / plutôt / tout à fait. | Toutes les affirmations sont regroupées en **${blocs.length} blocs de 4 affirmations** (${nAff} au total), qui couvrent des positions différentes plutôt que deux pôles. Chaque affirmation reçoit sa propre réponse. |
| Questions : **au moins 4 choix**, jamais deux propositions stéréotypées (ex. libre-échange). | Les 14 dilemmes à deux options sont supprimés. **${choix.length} questions à choix** proposent 5 à 7 options, plus « aucune de ces réponses ». Le libre-échange est traité par le bloc B16 (4 positions : libre-échange, protectionnisme national, protectionnisme européen, commerce sous conditions sociales et écologiques) et le choix C02. |
| Trop abstrait, pas assez appliqué au terrain. | Des **situations concrètes** : une usine qui délocalise (B03), une maternité qui ferme (B06), une zone à faibles émissions (B10), des agriculteurs qui manifestent (B11), une sortie scolaire (B13), des caricatures (B14), une famille en difficulté (B24), des contrôles au faciès (B28), un cambriolage de récidiviste (B37), un pays voisin envahi (C06), le budget de votre commune (A06). |
| Trop fermé, trop centré sur démocratie libérale vs autoritarisme ; il manque les volets révolutionnaire, anarchiste, fasciste. | Nouvelles options explicites : révolution et sabotage (B42), abolition du capitalisme ou de l'État (B43), pouvoir autoritaire, chef qui incarne la nation au-dessus des partis et des classes, démocratie des conseils (B44), six régimes au choix (C01), mode de changement (C14). **Proposition : activer l'axe CHG** (réformiste ↔ révolutionnaire), déjà prévu dans l'architecture. |
| Le vocabulaire réel manque (« grand remplacement », « lutte des classes »…). | Le vocabulaire en usage apparaît, **toujours dans une affirmation que le camp qui l'emploie pourrait signer**, et il est expliqué dans le mode Apprendre. Termes : lutte des classes, grand remplacement, remigration, préférence nationale, assistanat, écologie punitive, mondialisme, wokisme, patriarcat, racisme systémique, islamophobie, ensauvagement, violences policières, oligarchie, bourgeoisie, bien-pensants, impérialisme. |
| Répartitions de points : passer de 5 à 10. | **10 répartitions** : 5 conservées (A01 à A05) et 5 nouvelles (A06 budget communal, A07 école, A08 qui paie la transition, A09 combats prioritaires, A10 où économiser). |
| Fabien Roussel n'est pas si « socialiste ». | Hors questionnaire : son codage ECO +2 vient du fichier 01 (§3.10). À revoir au moment de la mise à jour des données candidat·es (par exemple +1,5), sans toucher au calcul. |
| Ne pas modifier l'algorithme. | Le calcul des scores, de la confiance, des correspondances et des graphiques est **inchangé** (voir §4 pour les deux petits ajouts de format nécessaires à la réintégration). |

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

## 4. Réintégration dans l'application (plus tard)

- **Calcul inchangé** : chaque affirmation se comporte exactement comme un item Likert actuel. Chaque répartition utilise la formule actuelle des allocations.
- **Choix à N options** : ils utilisent la même formule que les dilemmes actuels (contribution = 2 × poids de l'option choisie, maximum = 2 × plus grand poids en valeur absolue). Il faudra seulement accepter plus de deux options dans le format de données et dans l'écran de question.
- **Blocs** : c'est un regroupement d'affichage (4 affirmations par écran). Il ne change pas le calcul.
- **Axe CHG** : il suffit de passer \`enabled: true\` dans \`axes.json\` et de rédiger ses 5 textes de restitution. Les 18 archétypes n'ont pas de position CHG ; il faudra la leur ajouter pour qu'elle compte dans l'affinité.
- **Linter** : la liste de mots interdits (« grand remplacement », « remigration », « assistanat », « wokisme »…) devra être remplacée par la règle ci-dessus, « vocabulaire marqué, porté par son camp et expliqué ».
- **Contrôle actuel** (\`npx tsx docs/questionnaire-v2/check-v2.ts\`, avec le moteur actuel) :
  - neutralité sur 10 000 répondants aléatoires : moyenne de chaque axe entre −2,2 et +3,7 ;
  - répondant « tout d'accord » : au plus 23 en valeur absolue ;
  - personas : les 18 archétypes et les 15 candidat·es codé·es se retrouvent dans le top 3 dans 99 à 100 % des tirages.

## 5. Points de vigilance

- **« Grand remplacement »** (B25b) : l'affirmation est marquée « dimension factuelle ». L'explication rappelle l'origine de l'expression et sa réfutation par les démographes. L'outil décrit une adhésion, il ne qualifie pas la personne.
- **Options national-autoritaires et révolutionnaires** (B42, B43, B44, C01, C14) : elles sont formulées pour que leurs partisans s'y reconnaissent. L'explication nomme les doctrines (fascisme, communisme révolutionnaire, anarchisme) sans jugement moral.
- **Quelques axes restent courts** : IDE (8 affirmations principales), TER (6), UE et GMO (8). Ce sont les axes à enrichir en priorité si vous ajoutez des blocs.

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
