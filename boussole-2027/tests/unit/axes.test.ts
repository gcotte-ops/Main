import { describe, expect, it } from 'vitest';
import axes from '../../src/data/axes.json';
import thinkers from '../../src/data/thinkers.json';
import { ALL_AXES, AxisSchema } from '../../src/domain/schemas';

/** Libellés d'origine du fichier 01 (§0 et §5), conservés tels quels. */
const ORIGINAL: Record<string, [string, string]> = {
  ECO: ['Néolibéral', 'Socialiste'], IDE: ['Individualiste', 'Communautariste'], ENV: ['Dénialiste', 'Activiste'],
  REL: ['Anticlérical', 'Traditionnaliste'], ETA: ['Nationaliste', 'Internationaliste'], CUL: ['Conservateur', 'Libertaire'],
  ALT: ['Fermeture ethno-nationale', 'Ouverture / égalitarisme antiraciste'], UE: ['Anti-UE', 'Pro-UE (fédéraliste)'],
  GMO: ['Interventionniste', 'Laisser-faire / non-interventionniste'], GOV: ['Autoritaire', 'Démocratie libérale (État de droit, contre-pouvoirs)'],
  SEC: ['Sécuritaire', 'Garantiste'], INS: ['Présidentialisme représentatif', 'Parlementarisme / démocratie directe'],
  TER: ['Jacobin', 'Girondin / municipaliste'], POP: ['Peuple homogène contre élites', 'Pluralisme'],
};

describe('axes.json', () => {
  it('décrit les 18 axes, dont 14 actifs et 4 optionnels désactivés', () => {
    expect(axes.map((a) => a.id)).toEqual([...ALL_AXES]);
    for (const a of axes) expect(AxisSchema.safeParse(a).success, a.id).toBe(true);
    expect(axes.filter((a) => a.enabled)).toHaveLength(14);
    expect(axes.filter((a) => a.primary)).toHaveLength(10);
    expect(axes.filter((a) => !a.enabled).map((a) => a.id)).toEqual(['GEN', 'TEC', 'MEM', 'CHG']);
  });
  it('conserve les libellés de pôles du fichier 01', () => {
    for (const [id, [minus, plus]] of Object.entries(ORIGINAL)) {
      const a = axes.find((x) => x.id === id)!;
      expect([a.poleMinus, a.polePlus]).toEqual([minus, plus]);
    }
  });
  it('ne cite que des auteurs existants, jamais une fiche restreinte', () => {
    const map = new Map(thinkers.map((t) => [t.id, t]));
    for (const a of axes)
      for (const id of [...a.thinkers.minus, ...a.thinkers.center, ...a.thinkers.plus]) {
        expect(map.has(id), `${a.id} → ${id}`).toBe(true);
        expect((map.get(id) as { restricted?: boolean }).restricted, id).toBeFalsy();
      }
  });
});
