import { describe, expect, it } from 'vitest';
import groupsJson from '../../src/data/groups.json';
import questionsJson from '../../src/data/questions.json';
import { GroupSchema, QuestionSchema } from '../../src/domain/schemas';
import { initialState, questionOrder, quizReducer, screens } from '../../src/state/quiz';
import { decodeScores, encodeScores } from '../../src/state/share';

const questions = questionsJson.map((q) => QuestionSchema.parse(q));
const groups = groupsJson.map((g) => GroupSchema.parse(g));

describe('Ordre des questions', () => {
  it('est déterministe pour une graine, couvre les 69 écrans, priorités en dernier', () => {
    const a = questionOrder(questions, 123);
    expect(a).toEqual(questionOrder(questions, 123));
    expect(new Set(a).size).toBe(69);
    expect(a.length).toBe(69);
    expect(new Set([...screens(questions).values()].flat().map((q) => q.id)).size).toBe(201);
    expect(a.slice(-2).sort()).toEqual(['A01', 'A09']);
    expect(questionOrder(questions, 124)).not.toEqual(a);
  });
  it('affiche les affirmations d\'un bloc ensemble et garde les blocs appariés consécutifs', () => {
    const sc = screens(questions);
    expect(sc.get('B01')!.map((q) => q.id)).toEqual(['B01a', 'B01b', 'B01c', 'B01d']);
    for (const seed of [1, 2, 3, 4, 5]) {
      const o = questionOrder(questions, seed, groups);
      expect(o.indexOf('B30') - o.indexOf('B29')).toBe(1);
      expect(o.indexOf('B34') - o.indexOf('B33')).toBe(1);
    }
  });
  it('garde les rubriques thématiques groupées', () => {
    const block = new Map([...screens(questions)].map(([id, qs]) => [id, qs[0]!.block]));
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
    s = quizReducer(s, { type: 'goto', index: 999 });
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
    expect(s).toMatch(/^2\./);
    expect(decodeScores(s)).toEqual({ ECO: 42, ALT: -80, POP: 3 });
    expect(decodeScores(encodeScores({ CHG: 55 }))).toEqual({ CHG: 55 });
    expect(decodeScores('1.999')).toBeNull();
    expect(decodeScores('3.' + Array(15).fill('0').join('.'))).toBeNull();
    // Les liens de la version 1 (14 axes, sans CHG) restent lisibles.
    expect(decodeScores('1.10' + '._'.repeat(13))).toEqual({ ECO: 10 });
  });
});
