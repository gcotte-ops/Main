import { useEffect, useMemo, useReducer, useState } from 'react';
import { loadDataset, type Dataset } from './domain/load';
import { href, navigate, useRoute } from './router';
import { clearSaved, loadSaved, save } from './state/persistence';
import { initialState, quizReducer, type Mode, type QuizState } from './state/quiz';
import { HomePage } from './pages/Home';
import { QuizPage } from './pages/Quiz';
import { ResultsPage } from './pages/Results';
import { MethodologyPage } from './pages/Methodology';
import { PrivacyPage } from './pages/Privacy';
import { SharedPage } from './pages/Shared';
import { DataBanner } from './ui/DataBanner';

function useDataset(): { data: Dataset | null; error: string | null } {
  return useMemo(() => {
    try {
      return { data: loadDataset(), error: null };
    } catch (e) {
      return { data: null, error: e instanceof Error ? e.message : String(e) };
    }
  }, []);
}

export function App() {
  const { data, error } = useDataset();
  if (!data) return <main className="container"><h1>Boussole 2027</h1><p role="alert">Les données embarquées sont invalides : {error}</p></main>;
  return <Shell data={data} />;
}

function Shell({ data }: { data: Dataset }) {
  const route = useRoute();
  const [saved, setSaved] = useState(() => loadSaved());
  const [state, dispatch] = useReducer(
    (s: QuizState | null, a: Parameters<typeof quizReducer>[1] | { type: 'start'; state: QuizState } | { type: 'reset' }) =>
      a.type === 'start' ? a.state : a.type === 'reset' ? null : s ? quizReducer(s, a) : s,
    null,
  );

  useEffect(() => { if (state) save(state); }, [state]);
  useEffect(() => { if (state?.finished && route.name === 'quiz') navigate(href.results); }, [state?.finished, route.name]);

  const start = (mode: Mode, persist: boolean) => {
    dispatch({ type: 'start', state: initialState(data.questions, mode, persist, undefined, data.groups) });
    navigate(href.quiz);
  };
  const resume = () => { if (saved) { dispatch({ type: 'start', state: { ...saved, finished: false } }); navigate(href.quiz); } };
  const erase = () => { clearSaved(); setSaved(null); dispatch({ type: 'reset' }); navigate(href.home); };

  return (
    <>
      <a className="skip-link" href="#main">Aller au contenu</a>
      <header className="site-header on-dark">
        <div className="container header-inner">
          <a href={href.home} className="brand">Boussole 2027</a>
          <nav aria-label="Navigation principale">
            <ul>
              <li><a href={href.methodology} aria-current={route.name === 'methodology' ? 'page' : undefined}>Méthodologie</a></li>
              <li><a href={href.privacy} aria-current={route.name === 'privacy' ? 'page' : undefined}>Confidentialité</a></li>
              {state && Object.keys(state.answers).length > 0 && <li><a href={href.results} aria-current={route.name === 'results' ? 'page' : undefined}>Résultats</a></li>}
            </ul>
          </nav>
        </div>
      </header>
      <main id="main" tabIndex={-1} className="container">
        {route.name === 'home' && <HomePage data={data} onStart={start} saved={saved} onResume={resume} onErase={erase} />}
        {route.name === 'quiz' && (state ? <QuizPage data={data} state={state} dispatch={dispatch} onErase={erase} /> : <NoSession />)}
        {route.name === 'results' && (state && Object.keys(state.answers).length ? <ResultsPage data={data} state={state} onErase={erase} /> : <NoSession />)}
        {route.name === 'methodology' && <MethodologyPage data={data} />}
        {route.name === 'privacy' && <PrivacyPage />}
        {route.name === 'shared' && <SharedPage data={data} code={route.code} />}
      </main>
      <footer className="site-footer">
        <div className="container">
          <DataBanner meta={data.meta} />
          <p className="small muted">
            Outil de réflexion, pas une consigne de vote. Tous les calculs sont effectués dans votre navigateur ; aucune réponse n'est envoyée.{' '}
            <a href={href.methodology}>Méthodologie</a> · <a href={href.privacy}>Confidentialité</a>
          </p>
        </div>
      </footer>
    </>
  );
}

function NoSession() {
  return (
    <section className="section">
      <h1>Aucun questionnaire en cours</h1>
      <p>Commencez le questionnaire depuis l'accueil. Vos réponses restent dans cet onglet et disparaissent à sa fermeture, sauf si vous avez demandé à les conserver sur cet appareil.</p>
      <a className="btn btn-primary" href={href.home}>Revenir à l'accueil</a>
    </section>
  );
}
