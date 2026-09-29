import type { QuizState } from './quiz';

/**
 * Sauvegarde locale (localStorage) : uniquement si la personne l'a demandé. Rien n'est jamais envoyé
 * à un serveur. Toute lecture ou écriture est protégée : l'application fonctionne sans stockage.
 */
const KEY = 'boussole-2027:progression';

export function loadSaved(): QuizState | null {
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return null;
    const s = JSON.parse(raw) as QuizState;
    return s && Array.isArray(s.order) && typeof s.answers === 'object' ? { ...s, persist: true } : null;
  } catch {
    return null;
  }
}

export function save(s: QuizState): void {
  try {
    if (s.persist) window.localStorage.setItem(KEY, JSON.stringify(s));
    else window.localStorage.removeItem(KEY);
  } catch {
    /* stockage indisponible : on continue sans sauvegarde */
  }
}

export function clearSaved(): void {
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    /* rien à effacer */
  }
}
