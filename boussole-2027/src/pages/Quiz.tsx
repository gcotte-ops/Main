import { useEffect, useRef, useState } from 'react';
import type { Dataset } from '../domain/load';
import type { Answer } from '../domain/schemas';
import type { QuizAction, QuizState } from '../state/quiz';
import { QuestionView, isAnswered } from '../ui/questions/QuestionView';

export function QuizPage({ data, state, dispatch, onErase }: { data: Dataset; state: QuizState; dispatch: (a: QuizAction) => void; onErase: () => void }) {
  const byId = new Map(data.questions.map((q) => [q.id, q]));
  const thinkers = new Map(data.thinkers.map((t) => [t.id, t]));
  const q = byId.get(state.order[state.index]!)!;
  const answer = state.answers[q.id];
  const shownAt = useRef(performance.now());
  const [revealed, setRevealed] = useState(false);
  const headingRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    shownAt.current = performance.now();
    setRevealed(false);
    headingRef.current?.focus();
  }, [q.id]);

  const onAnswer = (a: Answer) => {
    dispatch({ type: 'answer', id: q.id, answer: { ...a, ms: Math.round(performance.now() - shownAt.current) } });
    if (state.mode === 'apprendre' && q.type !== 'allocation') setRevealed(true);
  };

  const done = Object.keys(state.answers).length;
  const pct = Math.round(((state.index + 1) / state.order.length) * 100);
  const canNext = isAnswered(q, answer);
  const blockLabel: Record<string, string> = {
    economie: 'Économie', societe: 'Société et mœurs', ecologie: 'Écologie et énergie', religion: 'Religion et laïcité', immigration: 'Immigration et altérité',
    international: 'Europe et monde', institutions: 'Institutions et démocratie', securite: 'Sécurité et libertés', territoires: 'Territoires', priorites: 'Vos priorités',
  };

  return (
    <div className="quiz">
      <div className="progress" aria-label="Progression">
        <div className="progress-label small">
          <span>Question {state.index + 1} sur {state.order.length} · {blockLabel[q.block] ?? q.block}</span>
          <span>{done} réponse{done > 1 ? 's' : ''}</span>
        </div>
        <div className="progress-track" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct} aria-valuetext={`${pct} %`}>
          <div className="progress-bar" style={{ width: `${pct}%` }} />
        </div>
      </div>

      <div ref={headingRef} tabIndex={-1} className="question-wrap" aria-live="polite">
        {q.block === 'priorites' && state.order.indexOf(q.id) === state.order.findIndex((id) => byId.get(id)!.block === 'priorites') && (
          <p className="section small">Dernière étape : vous répartissez des points entre des priorités. Ces répartitions indiquent l'importance que vous accordez aux enjeux ; elles pondèrent la comparaison avec les candidat·es.</p>
        )}
        <QuestionView q={q} answer={answer} onAnswer={onAnswer} />
      </div>

      {(revealed || (state.mode === 'apprendre' && q.type === 'allocation' && canNext)) && (
        <aside className="section learn" aria-label="Enjeux et arguments">
          <h3>Enjeux et arguments</h3>
          <p>{q.explanation}</p>
          <p className="small"><strong>Pour aller plus loin :</strong> {q.literature.map((id) => thinkers.get(id)?.name).filter(Boolean).join(' ; ')}</p>
          {q.factual && <p className="small muted">Cet énoncé comporte une dimension factuelle.</p>}
        </aside>
      )}

      <div className="actions quiz-nav">
        <button type="button" className="btn" disabled={state.index === 0} onClick={() => dispatch({ type: 'back' })}>Question précédente</button>
        {q.type === 'allocation' && !canNext && <button type="button" className="btn" onClick={() => dispatch({ type: 'next' })}>Passer</button>}
        <button type="button" className="btn btn-primary" disabled={!canNext} onClick={() => dispatch({ type: 'next' })}>
          {state.index + 1 === state.order.length ? 'Voir mes résultats' : 'Question suivante'}
        </button>
      </div>
      <div className="actions small">
        {done >= 20 && <button type="button" className="btn btn-small" onClick={() => dispatch({ type: 'finish' })}>Arrêter et voir des résultats partiels</button>}
        <button type="button" className="btn btn-small" onClick={onErase}>Tout effacer et recommencer</button>
      </div>
    </div>
  );
}
