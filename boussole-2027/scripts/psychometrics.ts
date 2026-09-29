/**
 * Validité interne sur données pilotes (CSV importé manuellement, jamais collecté automatiquement).
 *
 * Format : une ligne par répondant·e, une colonne par item (Q001…, D01…), valeurs −2..+2, vide = sans avis.
 *   npm run psychometrics -- pilote.csv [nombre de facteurs]
 *   npm run psychometrics -- --simuler 400      (auto-test sur des répondants simulés, sans aucune donnée réelle)
 *
 * Sorties : alpha de Cronbach et oméga par axe (items recodés dans le sens du pôle « plus »),
 * valeurs propres, AFE (varimax) et axe prévu vs facteur dominant de chaque item.
 */
import { readFileSync } from 'node:fs';
import archetypes from '../src/data/archetypes.json';
import questions from '../src/data/questions.json';
import { ArchetypeSchema, PRIMARY_AXES, QuestionSchema, SECONDARY_AXES, type Question } from '../src/domain/schemas';
import { mulberry32 } from '../src/engine/rng';
import { personaAnswers } from '../src/engine/simulate';
import { cronbachAlpha, exploratoryFactorAnalysis, mcdonaldOmega, parseCsv } from '../src/stats/psychometrics';

const qs = questions.map((q) => QuestionSchema.parse(q)).filter((q) => q.type !== 'allocation');
let header: string[];
let rows: (number | null)[][];

if (process.argv[2] === '--simuler') {
  const n = Number(process.argv[3] ?? 400);
  const rng = mulberry32(99);
  const as = archetypes.map((a) => ArchetypeSchema.parse(a));
  header = qs.map((q) => q.id);
  rows = Array.from({ length: n }, (_, i) => {
    const a = as[i % as.length]!;
    const jitter = Object.fromEntries(Object.entries(a.centroid).map(([k, v]) => [k, Math.max(-100, Math.min(100, v + (rng() - 0.5) * 60))]));
    const ans = personaAnswers(qs, jitter, rng, 0.8);
    return qs.map((q) => { const x = ans[q.id]; return x?.kind === 'scale' ? x.value : null; });
  });
  console.log(`Auto-test sur ${n} répondants SIMULÉS (aucune donnée réelle).\n`);
} else {
  const file = process.argv[2];
  if (!file) { console.error('Usage : npm run psychometrics -- pilote.csv [facteurs] | --simuler N'); process.exit(1); }
  const csv = parseCsv(readFileSync(file, 'utf8'));
  header = csv.header;
  rows = csv.rows.map((r) => r.map((c) => (c === '' ? null : Number(c))));
}

const col = new Map(header.map((h, i) => [h, i]));
const value = (row: (number | null)[], q: Question) => { const i = col.get(q.id); return i === undefined ? null : row[i] ?? null; };
/** Recodage : l'accord (ou l'option B) est orienté vers le pôle « plus » de l'axe principal. */
const sign = (q: Question) => (q.reversed ? -1 : 1);

console.log('Axe  | items | répondant·es complet·es | alpha | oméga');
for (const axis of [...PRIMARY_AXES, ...SECONDARY_AXES]) {
  const items = qs.filter((q) => q.primaryAxis === axis && col.has(q.id));
  const complete = rows.map((r) => items.map((q) => value(r, q))).filter((r) => r.every((x) => x !== null && Number.isFinite(x))) as number[][];
  const recoded = complete.map((r) => r.map((x, j) => x * sign(items[j]!)));
  const a = cronbachAlpha(recoded), w = mcdonaldOmega(recoded);
  console.log(`${axis.padEnd(4)} | ${String(items.length).padStart(5)} | ${String(complete.length).padStart(23)} | ${Number.isFinite(a) ? a.toFixed(2) : ' n.d.'} | ${Number.isFinite(w) ? w.toFixed(2) : ' n.d.'}`);
}

const present = qs.filter((q) => col.has(q.id));
const data = rows.map((r) => present.map((q) => { const v = value(r, q); return v === null ? NaN : v * sign(q); }));
const k = process.argv[2] === '--simuler' ? 14 : process.argv[3] ? Number(process.argv[3]) : undefined;
const efa = exploratoryFactorAnalysis(data, k);
console.log(`\nValeurs propres (10 premières) : ${efa.eigenvalues.slice(0, 10).map((v) => v.toFixed(2)).join(' ')}`);
console.log(`Facteurs extraits : ${efa.factors} (varimax)\n`);
console.log('Item | axe prévu | facteur dominant | saturation');
const byFactor = new Map<number, Map<string, number>>();
present.forEach((q, i) => {
  const l = efa.loadings[i]!;
  let best = 0;
  l.forEach((x, j) => { if (Math.abs(x) > Math.abs(l[best]!)) best = j; });
  const m = byFactor.get(best) ?? new Map<string, number>();
  m.set(q.primaryAxis, (m.get(q.primaryAxis) ?? 0) + 1);
  byFactor.set(best, m);
  console.log(`${q.id} | ${q.primaryAxis.padEnd(9)} | F${String(best + 1).padEnd(15)} | ${l[best]!.toFixed(2)}`);
});
console.log('\nComposition des facteurs (axes prévus) :');
for (const [f, m] of [...byFactor].sort((a, b) => a[0] - b[0])) console.log(`F${f + 1} : ${[...m].sort((a, b) => b[1] - a[1]).map(([ax, n]) => `${ax}×${n}`).join(', ')}`);
