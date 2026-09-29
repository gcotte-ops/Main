import { useState } from 'react';
import type { Dataset } from '../domain/load';
import { href } from '../router';
import type { Mode, QuizState } from '../state/quiz';

export function HomePage(props: {
  data: Dataset;
  saved: QuizState | null;
  onStart: (mode: Mode, persist: boolean) => void;
  onResume: () => void;
  onErase: () => void;
}) {
  const [mode, setMode] = useState<Mode>('rapide');
  const [persist, setPersist] = useState(false);
  const answered = props.saved ? Object.keys(props.saved.answers).length : 0;
  return (
    <>
      <section className="hero on-dark">
        <h1>Boussole 2027</h1>
        <p className="hero-lead">
          Cent questions pour affiner la connaissance de votre propre orientation politique : où vous vous situez sur quatorze axes,
          quelles traditions intellectuelles vous sont proches, quelles objections méritent votre attention.
        </p>
        <p>
          Une comparaison indicative avec les candidat·es à l'élection présidentielle de 2027 est proposée à la fin.
          Ce n'est pas l'objet principal de l'outil, et ce n'est pas une consigne de vote.
        </p>
      </section>

      <div className="grid-3">
        <section className="section">
          <h2>Durée</h2>
          <p>Environ 35 minutes : 44 blocs de 4 affirmations, 15 questions à choix et 10 répartitions de points. Vous pouvez revenir en arrière à tout moment et répondre « Je ne sais pas ».</p>
        </section>
        <section className="section">
          <h2>Confidentialité</h2>
          <p>Vos opinions politiques sont des données sensibles. Tout est calculé dans votre navigateur : aucune réponse n'est envoyée, aucun cookie, aucun traceur. <a href={href.privacy}>En savoir plus</a>.</p>
        </section>
        <section className="section">
          <h2>Méthode</h2>
          <p>Axes, formules, pondérations, sources et limites sont publiés. Chaque score est accompagné d'une marge d'incertitude. <a href={href.methodology}>Lire la méthodologie</a>.</p>
        </section>
      </div>

      {props.saved && (
        <section className="section" aria-labelledby="resume-title">
          <h2 id="resume-title">Reprendre votre questionnaire</h2>
          <p>Une progression est enregistrée sur cet appareil ({answered} réponse{answered > 1 ? 's' : ''}).</p>
          <div className="actions">
            <button type="button" className="btn btn-dark" onClick={props.onResume}>Reprendre</button>
            <button type="button" className="btn" onClick={props.onErase}>Effacer mes réponses de cet appareil</button>
          </div>
        </section>
      )}

      <section className="section" aria-labelledby="start-title">
        <h2 id="start-title">Commencer</h2>
        <fieldset className="mode-choice">
          <legend>Choisissez un mode</legend>
          <label className="choice">
            <input type="radio" name="mode" checked={mode === 'rapide'} onChange={() => setMode('rapide')} />
            <span><strong>Rapide</strong> : les questions s'enchaînent, les explications sont gardées pour la fin.</span>
          </label>
          <label className="choice">
            <input type="radio" name="mode" checked={mode === 'apprendre'} onChange={() => setMode('apprendre')} />
            <span><strong>Apprendre</strong> : après chaque réponse, les enjeux, les arguments des deux côtés et les auteurs qui les éclairent.</span>
          </label>
        </fieldset>
        <label className="check">
          <input type="checkbox" checked={persist} onChange={(e) => setPersist(e.target.checked)} />
          <span>Conserver ma progression sur cet appareil pour reprendre plus tard (stockage local, effaçable d'un clic ; déconseillé sur un ordinateur partagé).</span>
        </label>
        <div className="actions">
          <button type="button" className="btn btn-primary" onClick={() => props.onStart(mode, persist)}>Commencer le questionnaire</button>
        </div>
      </section>
    </>
  );
}
