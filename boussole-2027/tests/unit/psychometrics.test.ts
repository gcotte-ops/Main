import { describe, expect, it } from 'vitest';
import { cronbachAlpha, eigenSymmetric, exploratoryFactorAnalysis, mcdonaldOmega } from '../../src/stats/psychometrics';
import { gaussian, mulberry32 } from '../../src/engine/rng';

describe('Psychométrie', () => {
  const rng = mulberry32(5);
  // 300 répondants, deux facteurs latents, 4 items chacun.
  const data = Array.from({ length: 300 }, () => {
    const f1 = gaussian(rng), f2 = gaussian(rng);
    return [0, 1, 2, 3].map(() => f1 + 0.5 * gaussian(rng)).concat([0, 1, 2, 3].map(() => f2 + 0.5 * gaussian(rng)));
  });
  it('alpha et oméga élevés pour des items d\'un même facteur, faibles pour du bruit', () => {
    const block = data.map((r) => r.slice(0, 4));
    expect(cronbachAlpha(block)).toBeGreaterThan(0.85);
    expect(mcdonaldOmega(block)).toBeGreaterThan(0.85);
    const noise = Array.from({ length: 300 }, () => [0, 1, 2, 3].map(() => gaussian(rng)));
    expect(cronbachAlpha(noise)).toBeLessThan(0.2);
  });
  it('décomposition propre d\'une matrice connue', () => {
    const { values } = eigenSymmetric([[2, 1], [1, 2]]);
    expect(values[0]).toBeCloseTo(3, 6);
    expect(values[1]).toBeCloseTo(1, 6);
  });
  it('l\'AFE retrouve deux facteurs et sépare les deux blocs d\'items', () => {
    const efa = exploratoryFactorAnalysis(data);
    expect(efa.factors).toBe(2);
    const dominant = efa.loadings.map((l) => (Math.abs(l[0]!) > Math.abs(l[1]!) ? 0 : 1));
    expect(new Set(dominant.slice(0, 4)).size).toBe(1);
    expect(new Set(dominant.slice(4)).size).toBe(1);
    expect(dominant[0]).not.toBe(dominant[4]);
  });
});
