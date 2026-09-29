import { describe, expect, it } from 'vitest';
import archetypesJson from '../../src/data/archetypes.json';
import candidatesJson from '../../src/data/candidates.json';
import questionsJson from '../../src/data/questions.json';
import thinkers from '../../src/data/thinkers.json';
import { ArchetypeSchema, CandidateSchema, PRIMARY_AXES, QuestionSchema, SECONDARY_AXES } from '../../src/domain/schemas';
import { simulateArchetypePersonas, simulateCandidatePersonas } from '../../src/engine/simulate';

const archetypes = archetypesJson.map((a) => ArchetypeSchema.parse(a));
const candidates = candidatesJson.map((c) => CandidateSchema.parse(c));
const questions = questionsJson.map((q) => QuestionSchema.parse(q));

describe('archetypes.json', () => {
  it('au moins 16 archétypes, centroïdes complets sur les 14 axes actifs', () => {
    expect(archetypes.length).toBeGreaterThanOrEqual(16);
    for (const a of archetypes) for (const ax of [...PRIMARY_AXES, ...SECONDARY_AXES]) expect(a.centroid[ax], `${a.id}.${ax}`).toBeTypeOf('number');
  });
  it('filiation et contradicteurs existent ; aucune fiche restreinte en filiation', () => {
    const map = new Map(thinkers.map((t) => [t.id, t as { restricted?: boolean }]));
    for (const a of archetypes) {
      for (const id of [...a.lineage, ...a.counterpoints]) expect(map.has(id), `${a.id} → ${id}`).toBe(true);
      for (const id of a.lineage) expect(map.get(id)!.restricted, `${a.id} → ${id}`).toBeFalsy();
    }
  });
});

describe('Test des personas (≥ 90 % dans le top 3, σ = 0,6)', () => {
  it('candidat·es avec ≥ 7 axes codés', () => {
    const r = simulateCandidatePersonas(questions, candidates, 200);
    expect(r.length).toBeGreaterThanOrEqual(10);
    for (const x of r) expect(x.top3Rate, x.name).toBeGreaterThanOrEqual(0.9);
  });
  it('archétypes', () => {
    for (const x of simulateArchetypePersonas(questions, archetypes, 200)) expect(x.top3Rate, x.name).toBeGreaterThanOrEqual(0.9);
  });
});
