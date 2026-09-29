import { describe, expect, it } from 'vitest';
import thinkers from '../../src/data/thinkers.json';
import { ThinkerSchema } from '../../src/domain/schemas';

describe('thinkers.json (extrait du fichier 02)', () => {
  it('toutes les fiches sont valides et les identifiants uniques', () => {
    for (const t of thinkers) expect(ThinkerSchema.safeParse(t).success, t.id).toBe(true);
    expect(new Set(thinkers.map((t) => t.id)).size).toBe(thinkers.length);
    expect(thinkers.length).toBeGreaterThan(200);
  });
  it('contient les références de la lecture intersectionnelle (§12, §14)', () => {
    const ids = thinkers.map((t) => t.id);
    for (const id of ['crenshaw', 'hill-collins-hooks-davis', 'fraser']) expect(ids).toContain(id);
  });
  it('fusionne les renvois « voir §N » sans créer de doublon', () => {
    const marx = thinkers.find((t) => t.id === 'marx-engels')!;
    expect(marx.axes).toContain('REL');
    expect(thinkers.filter((t) => t.name.includes('Gramsci'))).toHaveLength(1);
  });
  it('marque comme restreintes les doctrines racistes réfutées, jamais les réfutations', () => {
    const restricted = thinkers.filter((t) => 'restricted' in t && t.restricted).map((t) => t.id);
    expect(restricted).toContain('gobineau');
    expect(restricted).toContain('camus');
    expect(restricted).not.toContain('refutations-racisme-scientifique');
    expect(restricted).not.toContain('guillaumin');
  });
});
