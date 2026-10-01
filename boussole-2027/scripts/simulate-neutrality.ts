/**
 * Test de neutralité (spécification §10) : 10 000 répondants aléatoires uniformes → moyenne de chaque
 * axe ∈ [−5 ; +5] ; répondant « tout d'accord » → aucun axe au-delà de ±25.
 * Usage : npm run simulate:neutrality
 */
import questions from '../src/data/questions.json';
import { QuestionSchema } from '../src/domain/schemas';
import { simulateNeutrality } from '../src/engine/simulate';

const qs = questions.map((q) => QuestionSchema.parse(q));
const r = simulateNeutrality(qs, Number(process.argv[2] ?? 10_000));
let ok = true;
console.log('dimension | moyenne (aléatoire) | « tout d\'accord »');
for (const d of Object.keys(r.meanByAxis).sort()) {
  const m = r.meanByAxis[d]!;
  const a = r.allAgree[d];
  const isAxis = !d.includes('.');
  const bad = isAxis && (Math.abs(m) > 5 || (a !== undefined && a !== null && Math.abs(a) > 25));
  if (bad) ok = false;
  console.log(`${d.padEnd(22)} | ${m.toFixed(2).padStart(7)} | ${a === undefined || a === null ? '—' : String(a).padStart(6)}${bad ? '  ✗' : ''}`);
}
console.log(ok ? '\nNeutralité : OK' : '\nNeutralité : ÉCHEC');
process.exit(ok ? 0 : 1);
