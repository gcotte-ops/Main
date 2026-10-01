import { describe, expect, it } from 'vitest';
import { QuestionSchema, CandidateSchema, AxisSchema } from '../../src/domain/schemas';
import { parseDataset } from '../../src/domain/load';

const q = {
  id: 'Q001', text: "L'État devrait garantir un emploi à toute personne qui en demande un.", type: 'likert',
  primaryAxis: 'ECO', loadings: { ECO: 1 }, theme: 'emploi', block: 'economie', reversed: false,
  literature: ['keynes'], explanation: 'Pour : le droit au travail. Contre : coût et efficacité. Deux arguments exposés ici.',
};

describe('Schémas Zod', () => {
  it('accepte une question valide', () => {
    expect(QuestionSchema.safeParse(q).success).toBe(true);
  });
  it('refuse un poids hors [−1, 1] et un axe inconnu', () => {
    expect(QuestionSchema.safeParse({ ...q, loadings: { ECO: 1.4 } }).success).toBe(false);
    expect(QuestionSchema.safeParse({ ...q, loadings: { XXX: 1 } }).success).toBe(false);
  });
  it('refuse un dilemme sans deux options et une question à choix de moins de 4 options', () => {
    expect(QuestionSchema.safeParse({ ...q, id: 'D01', type: 'dilemma', options: [{ label: 'A seul', loadings: {} }] }).success).toBe(false);
    const opt = (i: number) => ({ label: `Option ${i}`, loadings: { ECO: i / 10 } });
    expect(QuestionSchema.safeParse({ ...q, id: 'C01', type: 'choice', options: [1, 2, 3].map(opt) }).success).toBe(false);
    expect(QuestionSchema.safeParse({ ...q, id: 'C01', type: 'choice', options: [1, 2, 3, 4].map(opt) }).success).toBe(true);
  });
  it('accepte les identifiants v2 (B01a, C01) et refuse les autres', () => {
    expect(QuestionSchema.safeParse({ ...q, id: 'B01a', group: 'B01' }).success).toBe(true);
    expect(QuestionSchema.safeParse({ ...q, id: 'B01e' }).success).toBe(false);
  });
  it('accepte une position de candidat « non renseignée » (null) et refuse une valeur hors échelle', () => {
    const c = {
      id: 'x', name: 'X', party: 'P', bloc: 'B', status: 'Déclaré', statusDetail: '', section: '§3.1',
      positions: { ECO: { value: null, confidence: 'F', justification: '', sources: [] } },
      measureIds: [], sources: [], lastUpdated: '2026-09-25',
    };
    expect(CandidateSchema.safeParse(c).success).toBe(true);
    expect(CandidateSchema.safeParse({ ...c, positions: { ECO: { ...c.positions.ECO, value: 150 } } }).success).toBe(false);
  });
  it('exige 5 libellés de niveau par axe', () => {
    const a = { id: 'ECO', code: 'Économie', label: 'Économie', poleMinus: 'Néolibéral', polePlus: 'Socialiste',
      description: 'x'.repeat(50), levels: ['a', 'b', 'c', 'd'], thinkers: { minus: ['hayek'], center: [], plus: ['marx'] }, primary: true, enabled: true };
    expect(AxisSchema.safeParse(a).success).toBe(false);
  });
  it('signale les références croisées cassées', () => {
    const base = { axes: [], questions: [q], groups: [], candidates: [], measures: [], thinkers: [], archetypes: [], axisLevels: [], tensions: [],
      meta: { dataDate: '2026-09-25', electionRound1: '', electionRound2: '', version: '0' } };
    expect(() => parseDataset(base)).toThrow(/auteur inconnu « keynes »/);
  });
});
