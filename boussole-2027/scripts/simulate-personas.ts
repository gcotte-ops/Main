/**
 * Test des personas (spécification §10) : pour chaque candidat·e avec ≥ 7 axes codés et chaque
 * archétype, un persona répond selon son vecteur (+ bruit gaussien) ; il doit figurer dans le
 * top 3 des correspondances dans ≥ 90 % des simulations.
 * Usage : npm run simulate:personas [runs] [sigma]
 */
import archetypes from '../src/data/archetypes.json';
import candidates from '../src/data/candidates.json';
import questions from '../src/data/questions.json';
import { ArchetypeSchema, CandidateSchema, QuestionSchema } from '../src/domain/schemas';
import { simulateArchetypePersonas, simulateCandidatePersonas } from '../src/engine/simulate';

const runs = Number(process.argv[2] ?? 200);
const sigma = Number(process.argv[3] ?? 0.6);
const qs = questions.map((q) => QuestionSchema.parse(q));
const cs = candidates.map((c) => CandidateSchema.parse(c));
const as = archetypes.map((a) => ArchetypeSchema.parse(a));
let ok = true;
const show = (title: string, rows: { name: string; top3Rate: number; top1Rate: number }[]) => {
  console.log(`\n${title}\n${'nom'.padEnd(42)} top 3   top 1`);
  for (const r of rows) {
    const bad = r.top3Rate < 0.9;
    if (bad) ok = false;
    console.log(`${r.name.padEnd(42)} ${(100 * r.top3Rate).toFixed(0).padStart(4)} % ${(100 * r.top1Rate).toFixed(0).padStart(4)} %${bad ? '  ✗' : ''}`);
  }
};
show(`Candidat·es (≥ 7 axes codés), ${runs} simulations, σ = ${sigma}`, simulateCandidatePersonas(qs, cs, runs, 7, 7, sigma));
show(`Archétypes, ${runs} simulations, σ = ${sigma}`, simulateArchetypePersonas(qs, as, runs, 11, sigma));
console.log(ok ? '\nPersonas : OK' : '\nPersonas : ÉCHEC');
process.exit(ok ? 0 : 1);
