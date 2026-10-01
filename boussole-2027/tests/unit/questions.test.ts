import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import axes from '../../src/data/axes.json';
import candidates from '../../src/data/candidates.json';
import measures from '../../src/data/measures.json';
import questionsJson from '../../src/data/questions.json';
import thinkers from '../../src/data/thinkers.json';
import { lintQuestions, negationCount } from '../../src/domain/lint';
import { QuestionSchema, type Axis, type Candidate, type Question, type Thinker } from '../../src/domain/schemas';
import { simulateNeutrality } from '../../src/engine/simulate';
import { buildQuestions, formatJson } from '../../scripts/build-questions';

const questions = questionsJson.map((q) => QuestionSchema.parse(q));
const ctx = { axes: axes as Axis[], candidates: candidates as Candidate[], measures, thinkers: thinkers as Thinker[] };

describe('questions.json', () => {
  it('passe le linter sans erreur (blocs de 4, quotas, inversions, ancrage, thèmes, vocabulaire marqué)', () => {
    const r = lintQuestions(questions, ctx);
    expect(r.errors).toEqual([]);
    expect(r.stats.byType).toEqual({ likert: 176, dilemma: 0, choice: 15, allocation: 10 });
    expect(r.stats.groups).toBe(44);
  });

  it('est à jour avec le questionnaire rédigé (docs/questionnaire-v2)', () => {
    const built = buildQuestions();
    expect(formatJson(built.questions)).toBe(readFileSync(join(import.meta.dirname, '../../src/data/questions.json'), 'utf8'));
    expect(formatJson(built.groups)).toBe(readFileSync(join(import.meta.dirname, '../../src/data/groups.json'), 'utf8'));
  });

  it('test de neutralité : 10 000 répondants aléatoires → |moyenne| ≤ 5 ; « tout d\'accord » → |score| ≤ 25', () => {
    const r = simulateNeutrality(questions, 10_000);
    for (const [dim, m] of Object.entries(r.meanByAxis)) if (!dim.includes('.')) expect(Math.abs(m!), dim).toBeLessThanOrEqual(5);
    for (const [dim, s] of Object.entries(r.allAgree)) if (!dim.includes('.') && s !== null) expect(Math.abs(s!), dim).toBeLessThanOrEqual(25);
  });
});

describe('Linter : détecte les défauts de rédaction', () => {
  const ok = questions.find((q) => q.id === 'B01a')!;
  const lint1 = (patch: Partial<Question>) => lintQuestions([{ ...ok, ...patch } as Question], ctx).errors.join('\n');

  it('longueur > 30 mots', () => {
    expect(lint1({ text: Array.from({ length: 31 }, () => 'mot').join(' ') })).toMatch(/31 mots/);
  });
  it('double négation', () => {
    expect(negationCount("Il ne faut pas refuser sans raison.")).toBe(2);
    expect(negationCount("La loi ne devrait reconnaître que des individus, jamais des groupes.")).toBe(1);
    expect(lint1({ text: "On ne devrait pas interdire sans débat." })).toMatch(/double négation/);
  });
  it('vocabulaire marqué non expliqué et noms de candidat·es', () => {
    expect(lint1({ text: "Les assistés coûtent trop cher." })).toMatch(/terme marqué « assistés » non expliqué/);
    expect(lint1({ text: "Les assistés coûtent trop cher.", explanation: `${ok.explanation} Le mot « assistés » est employé par ses partisans.` })).not.toMatch(/terme marqué/);
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
