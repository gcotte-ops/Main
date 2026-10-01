/**
 * Génère docs/AUDIT_QUESTIONS.md : chaque bloc et chaque item, ses chargements, son explication, ses auteurs et les
 * mesures du fichier 01 dont il s'inspire, pour relecture par un panel pluraliste.
 * Usage : npm run audit:questions
 */
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { loadDataset } from '../src/domain/load';
import { allAgreeBias, lintQuestions } from '../src/domain/lint';
import type { Question } from '../src/domain/schemas';
import { BLOCK_LABELS } from '../src/state/quiz';

const d = loadDataset();
const ROOT = join(import.meta.dirname, '..');
const thinker = new Map(d.thinkers.map((t) => [t.id, t.name]));
const measure = new Map(d.measures.map((m) => [m.id, m]));
const candidate = new Map(d.candidates.map((c) => [c.id, c.name]));
const axisLabel = new Map(d.axes.map((a) => [a.id, a]));
const fmtW = (l: Record<string, number | undefined>) => Object.entries(l).map(([a, w]) => `${a} ${w! > 0 ? '+' : ''}${String(w).replace('.', ',')}`).join(' ; ') || '—';
const lint = lintQuestions(d.questions, { axes: d.axes, candidates: d.candidates, measures: d.measures, thinkers: d.thinkers });

const TYPE: Record<Question['type'], string> = { likert: 'Affirmation', dilemma: 'Dilemme', choice: 'Question à choix', allocation: 'Répartition' };
const measures = (ids: string[]) =>
  ids.map((m) => { const x = measure.get(m)!; return `${x.text} (${x.candidateIds.map((c) => candidate.get(c)).join(', ')}, ${x.section})`; }).join(' ; ');
const REVIEW = '**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :';

/** Une affirmation, une question à choix ou une répartition. */
const item = (q: Question, inGroup = false) => {
  const a = axisLabel.get(q.primaryAxis)!;
  const out = [
    `${inGroup ? '#####' : '####'} ${q.id} — ${TYPE[q.type]} · ${a.label} (${q.primaryAxis})${q.reversed ? ' · inversé' : ''}${q.factual ? ' · dimension factuelle' : ''}${q.pair ? ` · même énoncé que ${q.pair}` : ''}`,
    '',
    `> ${q.text}`,
    '',
  ];
  if (q.type === 'likert') out.push(`- **Chargements** (accord) : ${fmtW({ ...(q.loadings ?? {}), ...(q.facet ? { [q.facet]: q.facetLoading } : {}) })}`);
  else q.options!.forEach((o, i) => out.push(`- **${q.type === 'dilemma' ? (i ? 'B' : 'A') : `Option ${i + 1}`}** : ${o.label} — ${fmtW({ ...o.loadings, ...(o.facets ?? {}) })}`));
  if (q.type === 'choice') out.push('- **Option ajoutée** : Aucune de ces réponses / je ne sais pas — exclue du calcul');
  if (!inGroup) out.push(`- **Thème** : ${q.theme}`, `- **Auteurs** : ${q.literature.map((t) => thinker.get(t)).join(' ; ')}`);
  else if (q.theme !== d.questions.find((x) => x.group === q.group)!.theme) out.push(`- **Thème** : ${q.theme}`);
  if (q.sourceMeasure?.length) out.push(`- **Mesures du fichier 01** : ${measures(q.sourceMeasure)}`);
  if (q.contradicts?.length) out.push(`- **Même logique que** : ${q.contradicts.join(', ')} — coexistence : ${q.coexistence}`);
  if (!inGroup) out.push(`- **Explication** : ${q.explanation}`, '', REVIEW);
  out.push('');
  return out.join('\n');
};

/** Un bloc : contexte, explication et auteurs communs, puis ses 4 affirmations. */
const group = (id: string) => {
  const g = d.groups.find((x) => x.id === id)!;
  const qs = d.questions.filter((q) => q.group === id);
  return [
    `#### ${g.id} — ${g.title}${g.follows ? ` (affiché après ${g.follows})` : ''}`,
    '',
    `**Contexte** : ${g.context}`,
    '',
    `- **Thème** : ${qs[0]!.theme} · **Auteurs** : ${qs[0]!.literature.map((t) => thinker.get(t)).join(' ; ')}`,
    `- **Explication** (mode Apprendre) : ${qs[0]!.explanation}`,
    '',
    ...qs.map((q) => item(q, true)),
    REVIEW,
    '',
  ].join('\n');
};

const bias = allAgreeBias(d.questions);
const quotas = lint.stats.quotas as Record<string, { n: number; reversed: number }>;
const rubriques = [...new Set(d.questions.map((q) => q.block))];
const md = [
  '# Audit des questions — Boussole 2027',
  '',
  `_Document généré par \`npm run audit:questions\` — ne pas modifier à la main. Données au ${d.meta.dataDate}. Source du questionnaire : \`docs/questionnaire-v2/*.json\`._`,
  '',
  'Ce document est destiné à un panel de relecture pluraliste (sensibilités politiques différentes). Pour chaque bloc : le contexte, les 4 affirmations et leurs chargements (signe = pôle favorisé par l\'accord), l\'explication affichée en mode « Apprendre », les auteurs et, le cas échéant, les mesures de programme dont une affirmation reformule le principe (les candidat·es ne sont jamais nommé·es). Même présentation pour les questions à choix (signe = pôle favorisé par l\'option) et les répartitions.',
  '',
  '## Synthèse',
  '',
  `- ${d.groups.length} blocs, ${d.questions.length} items : ${JSON.stringify(lint.stats.byType)}`,
  `- ${lint.stats.cross} items à chargements croisés ; ${lint.stats.anchored} items ancrés dans une mesure du fichier 01`,
  `- Linter : ${lint.errors.length} erreur(s), ${lint.warnings.length} avertissement(s)`,
  '',
  '| Axe | Pôle − | Pôle + | Items (axe principal) | Inversés | Biais « tout d\'accord » |',
  '|---|---|---|---|---|---|',
  ...Object.entries(quotas).map(([a, q]) => { const ax = axisLabel.get(a as never)!; return `| ${a} | ${ax.poleMinus} | ${ax.polePlus} | ${q.n} | ${q.reversed} | ${bias[a as never] ?? '—'} |`; }),
  '',
  '## Vocabulaire marqué',
  '',
  'Ces termes sont employés parce qu\'ils sont en usage dans le débat. Le linter vérifie qu\'ils sont expliqués en mode Apprendre ; le panel vérifie que l\'affirmation pourrait être signée par le camp qui les emploie.',
  '',
  ...(lint.stats.marked as string[]).map((m) => `- ☐ ${m}`),
  '',
  ...rubriques.flatMap((r) => {
    const qs = d.questions.filter((q) => q.block === r);
    const groups = [...new Set(qs.filter((q) => q.group).map((q) => q.group!))];
    return [`## ${BLOCK_LABELS[r] ?? r}`, '', ...groups.map(group), ...qs.filter((q) => !q.group).map((q) => item(q))];
  }),
].join('\n');
writeFileSync(join(ROOT, 'docs/AUDIT_QUESTIONS.md'), md + '\n');
console.log(`docs/AUDIT_QUESTIONS.md : ${d.groups.length} blocs, ${d.questions.length} items`);
