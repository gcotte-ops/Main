import { useEffect, useState } from 'react';

/** Routage par fragment (#/…) : fonctionne en déploiement statique, sans configuration serveur. */
export type Route =
  | { name: 'home' }
  | { name: 'quiz' }
  | { name: 'results' }
  | { name: 'methodology' }
  | { name: 'privacy' }
  | { name: 'shared'; code: string };

export function parseHash(hash: string): Route {
  const h = hash.replace(/^#\/?/, '');
  if (h.startsWith('partage/')) return { name: 'shared', code: decodeURIComponent(h.slice('partage/'.length)) };
  if (h === 'questionnaire') return { name: 'quiz' };
  if (h === 'resultats') return { name: 'results' };
  if (h === 'methodologie') return { name: 'methodology' };
  if (h === 'confidentialite') return { name: 'privacy' };
  return { name: 'home' };
}

export const href = {
  home: '#/',
  quiz: '#/questionnaire',
  results: '#/resultats',
  methodology: '#/methodologie',
  privacy: '#/confidentialite',
  shared: (code: string) => `#/partage/${encodeURIComponent(code)}`,
};

export function navigate(to: string) {
  window.location.hash = to;
}

export function useRoute(): Route {
  const [route, setRoute] = useState(() => parseHash(window.location.hash));
  useEffect(() => {
    const on = () => {
      setRoute(parseHash(window.location.hash));
      window.scrollTo(0, 0);
      document.getElementById('main')?.focus();
    };
    window.addEventListener('hashchange', on);
    return () => window.removeEventListener('hashchange', on);
  }, []);
  return route;
}
