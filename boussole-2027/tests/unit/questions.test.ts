import { describe, expect, it } from 'vitest';
import axes from '../../src/data/axes.json';
import candidates from '../../src/data/candidates.json';
import measures from '../../src/data/measures.json';
import questionsJson from '../../src/data/questions.json';
import thinkers from '../../src/data/thinkers.json';
import { lintQuestions, negationCount } from '../../src/domain/lint';
import { QuestionSchema, type Axis, type Candidate, type Question, type Thinker } from '../../src/domain/schemas';
import { simulateNeutrality } from '../../src/engine/simulate';

const questions = questionsJson.map((q) => QuestionSchema.parse(q));
const ctx = { axes: axes as Axis[], candidates: candidates as Candidate[], measures, thinkers: thinkers as Thinker[] };

describe('questions.json', () => {
  it('passe le linter sans erreur (100 items, quotas, inversions, ancrage, thèmes)', () => {
    const r = lintQuestions(questions, ctx);
    expect(r.errors).toEqual([]);
    expect(questions).toHaveLength(100);
  });

  it('test de neutralité : 10 000 répondants aléatoires → |moyenne| ≤ 5 ; « tout d\'accord » → |score| ≤ 25', () => {
    const r = simulateNeutrality(questions, 10_000);
    for (const [dim, m] of Object.entries(r.meanByAxis)) if (!dim.includes('.')) expect(Math.abs(m!), dim).toBeLessThanOrEqual(5);
    for (const [dim, s] of Object.entries(r.allAgree)) if (!dim.includes('.') && s !== null) expect(Math.abs(s!), dim).toBeLessThanOrEqual(25);
  });
});

describe('Linter : détecte les défauts de rédaction', () => {
  const ok = questions.find((q) => q.id === 'Q001')!;
  const lint1 = (patch: Partial<Question>) => lintQuestions([{ ...ok, ...patch } as Question], ctx).errors.join('\n');

  it('longueur > 30 mots', () => {
    expect(lint1({ text: Array.from({ length: 31 }, () => 'mot').join(' ') })).toMatch(/31 mots/);
  });
  it('double négation', () => {
    expect(negationCount("Il ne faut pas refuser sans raison.")).toBe(2);
    expect(negationCount("La loi ne devrait reconnaître que des individus, jamais des groupes.")).toBe(1);
    expect(lint1({ text: "On ne devrait pas interdire sans débat." })).toMatch(/double négation/);
  });
  it('mots chargés et noms de candidat·es', () => {
    expect(lint1({ text: "Les assistés coûtent trop cher." })).toMatch(/mot chargé « assistés »/);
    expect(lint1({ text: "Il faut soutenir la politique de Mélenchon." })).toMatch(/nom de candidat/);
  });
  it('incohérence entre reversed et signe du chargement', () => {
    expect(lint1({ reversed: true })).toMatch(/reversed=true incohérent/);
  });
  it('auteur inconnu ou restreint', () => {
    expect(lint1({ literature: ['inconnu'] })).toMatch(/auteur inconnu/);
    expect(lint1({ literature: ['gobineau'] })).toMatch(/auteur restreint/);
  });
});
