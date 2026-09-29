import type { Answer, Answers, Question } from '../domain/schemas';
import { mulberry32, shuffle } from '../engine/rng';

export type Mode = 'rapide' | 'apprendre';

export interface QuizState {
  mode: Mode;
  seed: number;
  order: string[];
  index: number;
  answers: Answers;
  /** Sauvegarde locale acceptée explicitement (désactivée par défaut). */
  persist: boolean;
  finished: boolean;
}

/** Blocs thématiques mélangés (graine), items mélangés dans chaque bloc ; les allocations (priorités) en dernier. */
export function questionOrder(questions: Question[], seed: number): string[] {
  const rng = mulberry32(seed);
  const blocks = [...new Set(questions.map((q) => q.block))].filter((b) => b !== 'priorites');
  const order: string[] = [];
  for (const b of shuffle(blocks, rng)) order.push(...shuffle(questions.filter((q) => q.block === b), rng).map((q) => q.id));
  order.push(...questions.filter((q) => q.block === 'priorites').map((q) => q.id));
  return order;
}

export function initialState(questions: Question[], mode: Mode, persist: boolean, seed = Math.floor(Math.random() * 2 ** 31)): QuizState {
  return { mode, seed, order: questionOrder(questions, seed), index: 0, answers: {}, persist, finished: false };
}

export type QuizAction =
  | { type: 'answer'; id: string; answer: Answer }
  | { type: 'next' }
  | { type: 'back' }
  | { type: 'goto'; index: number }
  | { type: 'finish' }
  | { type: 'setMode'; mode: Mode }
  | { type: 'setPersist'; persist: boolean };

export function quizReducer(s: QuizState, a: QuizAction): QuizState {
  switch (a.type) {
    case 'answer':
      return { ...s, answers: { ...s.answers, [a.id]: a.answer } };
    case 'next':
      return s.index + 1 >= s.order.length ? { ...s, finished: true } : { ...s, index: s.index + 1 };
    case 'back':
      return { ...s, index: Math.max(0, s.index - 1), finished: false };
    case 'goto':
      return { ...s, index: Math.max(0, Math.min(s.order.length - 1, a.index)), finished: false };
    case 'finish':
      return { ...s, finished: true };
    case 'setMode':
      return { ...s, mode: a.mode };
    case 'setPersist':
      return { ...s, persist: a.persist };
  }
}
