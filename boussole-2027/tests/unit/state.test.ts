import { describe, expect, it } from 'vitest';
import questionsJson from '../../src/data/questions.json';
import { QuestionSchema } from '../../src/domain/schemas';
import { initialState, questionOrder, quizReducer } from '../../src/state/quiz';
import { decodeScores, encodeScores } from '../../src/state/share';

const questions = questionsJson.map((q) => QuestionSchema.parse(q));

describe('Ordre des questions', () => {
  it('est déterministe pour une graine, couvre les 100 items, allocations en dernier', () => {
    const a = questionOrder(questions, 123);
    expect(a).toEqual(questionOrder(questions, 123));
    expect(new Set(a).size).toBe(100);
    expect(a.slice(-5).every((id) => id.startsWith('A'))).toBe(true);
    expect(questionOrder(questions, 124)).not.toEqual(a);
  });
  it('garde les blocs thématiques groupés', () => {
    const block = new Map(questions.map((q) => [q.id, q.block]));
    const seq = questionOrder(questions, 5).map((id) => block.get(id));
    const changes = seq.filter((b, i) => i > 0 && b !== seq[i - 1]).length;
    expect(changes).toBe(new Set(seq).size - 1);
  });
});

describe('Réducteur', () => {
  it('avance, recule et termine', () => {
    let s = initialState(questions, 'rapide', false, 1);
    s = quizReducer(s, { type: 'answer', id: s.order[0]!, answer: { kind: 'scale', value: 1 } });
    s = quizReducer(s, { type: 'next' });
    expect(s.index).toBe(1);
    s = quizReducer(s, { type: 'back' });
    expect(s.index).toBe(0);
    s = quizReducer(s, { type: 'goto', index: 99 });
    s = quizReducer(s, { type: 'next' });
    expect(s.finished).toBe(true);
  });
  it('la persistance est désactivée par défaut', () => {
    expect(initialState(questions, 'rapide', false).persist).toBe(false);
  });
});

describe('Lien de partage', () => {
  it('encode les scores (pas les réponses) et refuse les valeurs invalides', () => {
    const s = encodeScores({ ECO: 42.4, ALT: -80, POP: 3 });
    expect(s).toMatch(/^1\./);
    expect(decodeScores(s)).toEqual({ ECO: 42, ALT: -80, POP: 3 });
    expect(decodeScores('1.999')).toBeNull();
    expect(decodeScores('2.' + Array(14).fill('0').join('.'))).toBeNull();
  });
});
