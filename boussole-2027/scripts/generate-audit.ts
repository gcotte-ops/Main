/**
 * Génère docs/AUDIT_QUESTIONS.md : chaque item, ses chargements, son explication, ses auteurs et les
 * mesures du fichier 01 dont il s'inspire, pour relecture par un panel pluraliste.
 * Usage : npm run audit:questions
 */
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { loadDataset } from '../src/domain/load';
import { allAgreeBias, lintQuestions } from '../src/domain/lint';
import type { Question } from '../src/domain/schemas';

const d = loadDataset();
const ROOT = join(import.meta.dirname, '..');
const thinker = new Map(d.thinkers.map((t) => [t.id, t.name]));
const measure = new Map(d.measures.map((m) => [m.id, m]));
const candidate = new Map(d.candidates.map((c) => [c.id, c.name]));
const axisLabel = new Map(d.axes.map((a) => [a.id, a]));
const fmtW = (l: Record<string, number | undefined>) => Object.entries(l).map(([a, w]) => `${a} ${w! > 0 ? '+' : ''}${String(w).replace('.', ',')}`).join(' ; ') || '—';
const lint = lintQuestions(d.questions, { axes: d.axes, candidates: d.candidates, measures: d.measures, thinkers: d.thinkers });

const block = (q: Question) => {
  const a = axisLabel.get(q.primaryAxis)!;
  const out = [
    `#### ${q.id} — ${q.type === 'likert' ? 'Likert' : q.type === 'dilemma' ? 'Dilemme' : 'Allocation'} · ${a.label} (${q.primaryAxis})${q.reversed ? ' · inversé' : ''}${q.factual ? ' · dimension factuelle' : ''}`,
    '',
    `> ${q.text}`,
    '',
  ];
  if (q.type === 'likert') out.push(`- **Chargements** (accord) : ${fmtW(q.loadings ?? {})}`);
  else q.options!.forEach((o, i) => out.push(`- **${q.type === 'dilemma' ? (i ? 'B' : 'A') : `Option ${i + 1}`}** : ${o.label} — ${fmtW(o.loadings)}`));
  if (q.facet) out.push(`- **Facette** : ${q.facet} (${q.facetLoading! > 0 ? '+' : ''}${String(q.facetLoading).replace('.', ',')})`);
  out.push(`- **Thème** : ${q.theme} · **bloc** : ${q.block}`);
  out.push(`- **Auteurs** : ${q.literature.map((t) => thinker.get(t)).join(' ; ')}`);
  if (q.sourceMeasure?.length)
    out.push(`- **Mesures du fichier 01** : ${q.sourceMeasure.map((m) => { const x = measure.get(m)!; return `${x.text} (${x.candidateIds.map((c) => candidate.get(c)).join(', ')}, ${x.section})`; }).join(' ; ')}`);
  if (q.contradicts?.length) out.push(`- **Même logique que** : ${q.contradicts.join(', ')} — coexistence : ${q.coexistence}`);
  out.push(`- **Explication** : ${q.explanation}`, '', '**Relecture** : ☐ formulation neutre (steelman) ☐ une seule idée ☐ chargements justes ☐ explication équilibrée — remarques :', '');
  return out.join('\n');
};

const bias = allAgreeBias(d.questions);
const quotas = lint.stats.quotas as Record<string, { n: number; reversed: number }>;
const md = [
  '# Audit des questions — Boussole 2027',
  '',
  `_Document généré par \`npm run audit:questions\` — ne pas modifier à la main. Données au ${d.meta.dataDate}._`,
  '',
  'Ce document est destiné à un panel de relecture pluraliste (sensibilités politiques différentes). Pour chaque item : l\'énoncé, les chargements (signe = pôle favorisé par l\'accord ou par l\'option), l\'explication affichée en mode « Apprendre », les auteurs et, le cas échéant, les mesures de programme dont l\'item reformule le principe (les candidat·es ne sont jamais nommé·es dans l\'énoncé).',
  '',
  '## Synthèse',
  '',
  `- ${d.questions.length} items : ${JSON.stringify(lint.stats.byType)}`,
  `- ${lint.stats.cross} items à chargements croisés ; ${lint.stats.anchored} items ancrés dans une mesure du fichier 01`,
  `- Linter : ${lint.errors.length} erreur(s), ${lint.warnings.length} avertissement(s)`,
  '',
  '| Axe | Pôle − | Pôle + | Items | Inversés | Biais « tout d\'accord » |',
  '|---|---|---|---|---|---|',
  ...Object.entries(quotas).map(([a, q]) => { const ax = axisLabel.get(a as never)!; return `| ${a} | ${ax.poleMinus} | ${ax.polePlus} | ${q.n} | ${q.reversed} | ${bias[a as never] ?? '—'} |`; }),
  '',
  '## Items par axe principal',
  '',
  ...d.axes.filter((a) => a.enabled).flatMap((a) => [`### ${a.label} (${a.id})`, '', ...d.questions.filter((q) => q.primaryAxis === a.id).map(block)]),
].join('\n');
writeFileSync(join(ROOT, 'docs/AUDIT_QUESTIONS.md'), md + '\n');
console.log(`docs/AUDIT_QUESTIONS.md : ${d.questions.length} items`);
