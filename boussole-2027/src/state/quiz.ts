import type { Answer, Answers, Group, Question } from '../domain/schemas';
import { mulberry32, shuffle } from '../engine/rng';

export type Mode = 'rapide' | 'apprendre';

/** Libellés des rubriques thématiques (champ `block` des questions). */
export const BLOCK_LABELS: Record<string, string> = {
  economie: 'Économie et travail', ecologie: 'Écologie et énergie', religion: 'Religion, laïcité et école', nation: 'Nation, monde et mémoire',
  societe: 'Mœurs, famille et identité', immigration: 'Immigration et altérité', international: 'Europe et relations internationales',
  institutions: 'Démocratie, pouvoir et changement', securite: 'Sécurité et justice', territoires: 'Territoires', priorites: 'Vos priorités',
};


/** Version du format de progression : une sauvegarde d'une autre version est ignorée. */
export const QUIZ_VERSION = 2;

export interface QuizState {
  version: number;
  mode: Mode;
  seed: number;
  /** Ordre des écrans (identifiant de bloc B01, ou de question C01 / A01). */
  order: string[];
  index: number;
  answers: Answers;
  /** Sauvegarde locale acceptée explicitement (désactivée par défaut). */
  persist: boolean;
  finished: boolean;
}

/** Identifiant de l'écran d'une question : son bloc d'affirmations, sinon elle-même. */
export const screenOf = (q: Question) => q.group ?? q.id;

/** Questions de chaque écran, dans l'ordre du fichier (a, b, c, d pour un bloc). */
export function screens(questions: Question[]): Map<string, Question[]> {
  const m = new Map<string, Question[]>();
  for (const q of questions) m.set(screenOf(q), [...(m.get(screenOf(q)) ?? []), q]);
  return m;
}

/**
 * Rubriques thématiques mélangées (graine), écrans mélangés dans chaque rubrique ; les répartitions de
 * la rubrique « priorités » en dernier. Un bloc qui en suit un autre (`follows`, ou item apparié `pair`)
 * reste juste après lui.
 */
export function questionOrder(questions: Question[], seed: number, groups: Group[] = []): string[] {
  const rng = mulberry32(seed);
  const byId = new Map(questions.map((q) => [q.id, q]));
  const unitOf = new Map<string, string>();
  for (const q of questions) if (q.pair && byId.has(q.pair)) unitOf.set(screenOf(q), screenOf(byId.get(q.pair)!));
  for (const g of groups) if (g.follows) unitOf.set(g.id, g.follows);
  const units = new Map<string, string[]>();
  const blockOfUnit = new Map<string, string>();
  for (const sc of screens(questions).keys()) {
    const u = unitOf.get(sc) ?? sc;
    units.set(u, [...(units.get(u) ?? []), sc]);
    blockOfUnit.set(u, questions.find((q) => screenOf(q) === sc)!.block);
  }
  const blocks = [...new Set(questions.map((q) => q.block))].filter((b) => b !== 'priorites');
  const order: string[] = [];
  const unitsOf = (b: string) => [...units.keys()].filter((u) => blockOfUnit.get(u) === b);
  for (const b of shuffle(blocks, rng)) for (const u of shuffle(unitsOf(b), rng)) order.push(...units.get(u)!);
  for (const u of unitsOf('priorites')) order.push(...units.get(u)!);
  return order;
}

export function initialState(questions: Question[], mode: Mode, persist: boolean, seed = Math.floor(Math.random() * 2 ** 31), groups: Group[] = []): QuizState {
  return { version: QUIZ_VERSION, mode, seed, order: questionOrder(questions, seed, groups), index: 0, answers: {}, persist, finished: false };
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
