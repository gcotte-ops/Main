import { describe, expect, it } from 'vitest';
import candidatesJson from '../../src/data/candidates.json';
import measuresJson from '../../src/data/measures.json';
import { CandidateSchema, MeasureSchema, type Candidate } from '../../src/domain/schemas';

const candidates = candidatesJson as Candidate[];
const byId = (id: string) => candidates.find((c) => c.id === id)!;
const pos = (id: string, axis: keyof Candidate['positions']) => byId(id).positions[axis]!;

describe('candidates.json (extrait du fichier 01)', () => {
  it('toutes les entrées sont valides', () => {
    for (const c of candidates) expect(CandidateSchema.safeParse(c).success, c.id).toBe(true);
    for (const m of measuresJson) expect(MeasureSchema.safeParse(m).success, m.id).toBe(true);
  });
  it('convertit le codage −2..+2 en −100..+100 avec la confiance de la cellule', () => {
    expect(pos('marine-le-pen', 'ETA')).toMatchObject({ value: -100, confidence: 'H' });
    expect(pos('jean-luc-melenchon', 'ECO')).toMatchObject({ value: 100, confidence: 'H' });
    expect(pos('edouard-philippe', 'ECO')).toMatchObject({ value: -75, confidence: 'H' });
    expect(pos('raphael-glucksmann', 'GMO')).toMatchObject({ value: -100, confidence: 'H' });
  });
  it('applique la confiance globale, « M à F » donnant F', () => {
    expect(pos('francois-ruffin', 'ECO')).toMatchObject({ value: 75, confidence: 'F' });
    expect(pos('fabien-roussel', 'ECO')).toMatchObject({ value: 100, confidence: 'M' });
  });
  it('scinde le tableau commun de l\'extrême gauche sans inventer de valeur', () => {
    expect(pos('anasse-kazib', 'CUL').value).toBe(75);
    expect(pos('nathalie-arthaud', 'CUL').value).toBe(50);
    expect(pos('selma-labib', 'CUL').value).toBeNull();
    for (const id of ['anasse-kazib', 'nathalie-arthaud', 'selma-labib']) expect(pos(id, 'GOV').value).toBeNull();
  });
  it('laisse à null les candidat·es sans codage (dont 4 des 5 candidat·es de la primaire PS)', () => {
    for (const id of ['olivier-faure', 'jerome-guedj', 'emmanuel-maurel', 'segolene-royal', 'xavier-bertrand']) {
      expect(Object.values(byId(id).positions).every((p) => p?.value === null), id).toBe(true);
      expect(byId(id).status === 'Primaire' || id === 'xavier-bertrand').toBe(true);
    }
  });
  it('gère le remplacement RN (Le Pen / Bardella)', () => {
    expect(byId('marine-le-pen').alternates).toEqual(['Jordan Bardella']);
  });
  it('chaque position renvoie à une source du fichier 01', () => {
    for (const c of candidates)
      for (const p of Object.values(c.positions)) expect(p!.sources[0]).toMatch(/^Fichier 01 §/);
  });
  it('toutes les mesures référencées existent', () => {
    const ids = new Set(measuresJson.map((m) => m.id));
    for (const c of candidates) for (const m of c.measureIds) expect(ids.has(m), m).toBe(true);
  });
});
