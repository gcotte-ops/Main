import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { loadDataset } from '../../src/domain/load';
import { buildResults } from '../../src/engine/narrative';
import { mulberry32 } from '../../src/engine/rng';
import { personaAnswers, randomAnswers } from '../../src/engine/simulate';
import { checkAxisLevels } from '../../scripts/check-axis-levels';

const d = loadDataset();
const words = (p: string[]) => p.join(' ').split(/\s+/).filter((w) => /[\p{L}\d]/u.test(w)).length;

describe('Données de restitution', () => {
  it('le jeu de données complet est valide et cohérent', () => {
    expect(d.questions).toHaveLength(100);
    expect(d.axisLevels).toHaveLength(70);
  });
  it('70 textes par axe et par niveau (80–120 mots, auteurs proches et contradicteurs)', () => {
    const raw = JSON.parse(readFileSync('src/data/texts/axis-levels.json', 'utf8'));
    expect(checkAxisLevels(raw, ['ECO', 'IDE', 'ENV', 'REL', 'ETA', 'CUL', 'ALT', 'UE', 'GMO', 'GOV', 'SEC', 'INS', 'TER', 'POP'])).toEqual([]);
  });
});

describe('Restitution (moteur de règles)', () => {
  const rng = mulberry32(3);
  const personas = [
    ...d.archetypes.map((a) => personaAnswers(d.questions, a.centroid, rng)),
    ...Array.from({ length: 5 }, () => randomAnswers(d.questions, rng)),
  ];

  it('pour chaque axe : au moins un auteur proche et un contradicteur', () => {
    for (const ans of personas) {
      const r = buildResults(d, ans, { draws: 50 });
      for (const a of r.axes) {
        expect(a.near.length, a.axis.id).toBeGreaterThanOrEqual(1);
        expect(a.opposed.length, a.axis.id).toBeGreaterThanOrEqual(1);
      }
    }
  });

  it('synthèse de 250 à 400 mots, 3 lectures (confirme, nuance, contredit), au plus 3 tensions', () => {
    for (const ans of personas) {
      const r = buildResults(d, ans, { draws: 0 });
      const n = words(r.synthesis);
      expect(n, r.synthesis.join('\n')).toBeGreaterThanOrEqual(250);
      expect(n).toBeLessThanOrEqual(400);
      expect(r.readings.map((x) => x.role)).toEqual(['confirme', 'nuance', 'contredit']);
      expect(r.tensions.length).toBeLessThanOrEqual(3);
      expect(r.top).toHaveLength(3);
      for (const t of r.top) expect(t.lineage.length).toBeGreaterThanOrEqual(2);
    }
  });

  it('la synthèse ne contient aucun jugement moral ni consigne de vote', () => {
    for (const ans of personas) {
      const txt = buildResults(d, ans, { draws: 0 }).synthesis.join(' ').toLowerCase();
      expect(txt).not.toMatch(/(?<!anti)raciste|xénophobe|extrémiste|votez|vous devriez voter|dangereu/);
    }
  });

  it('détecte la tension marché / tradition chez un persona libéral-conservateur', () => {
    const lc = d.archetypes.find((a) => a.id === 'liberal-conservatisme')!;
    const r = buildResults(d, personaAnswers(d.questions, lc.centroid, mulberry32(1), 0.3), { draws: 0 });
    expect(r.tensions.map((t) => t.id)).toContain('marche-tradition');
    expect(r.top[0]!.match.archetype.id).toBe('liberal-conservatisme');
  });
});
