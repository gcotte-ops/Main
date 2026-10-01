import { useEffect, useRef } from 'react';
import type { Dataset } from '../domain/load';
import type { Answer, Question } from '../domain/schemas';
import { BLOCK_LABELS, screens, type QuizAction, type QuizState } from '../state/quiz';
import { QuestionView, isAnswered } from '../ui/questions/QuestionView';

/** Réponses à partir desquelles des résultats partiels peuvent être affichés. */
export const PARTIAL_RESULTS_MIN = 40;

export function QuizPage({ data, state, dispatch, onErase }: { data: Dataset; state: QuizState; dispatch: (a: QuizAction) => void; onErase: () => void }) {
  const byScreen = screens(data.questions);
  const thinkers = new Map(data.thinkers.map((t) => [t.id, t]));
  const screenId = state.order[state.index]!;
  const qs = byScreen.get(screenId)!;
  const q = qs[0]!;
  const group = q.group ? data.groups.find((g) => g.id === q.group) : undefined;
  const shownAt = useRef(performance.now());
  const headingRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    shownAt.current = performance.now();
    headingRef.current?.focus();
  }, [screenId]);

  const onAnswer = (item: Question) => (a: Answer) => {
    dispatch({ type: 'answer', id: item.id, answer: { ...a, ms: Math.round(performance.now() - shownAt.current) } });
  };

  const done = Object.keys(state.answers).length;
  const pct = Math.round(((state.index + 1) / state.order.length) * 100);
  const canNext = qs.every((x) => isAnswered(x, state.answers[x.id]));
  // Mode Apprendre : l'explication apparaît une fois l'écran entièrement répondu.
  const revealed = state.mode === 'apprendre' && canNext;
  const firstPriority = state.order.findIndex((id) => byScreen.get(id)![0]!.block === 'priorites');

  return (
    <div className="quiz">
      <div className="progress">
        <div className="progress-label small">
          <span>Étape {state.index + 1} sur {state.order.length} · {BLOCK_LABELS[q.block] ?? q.block}</span>
          <span>{done} réponse{done > 1 ? 's' : ''}</span>
        </div>
        <div className="progress-track" role="progressbar" aria-label="Progression du questionnaire" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct} aria-valuetext={`${pct} %`}>
          <div className="progress-bar" style={{ width: `${pct}%` }} />
        </div>
      </div>

      <div ref={headingRef} tabIndex={-1} className="question-wrap" aria-live="polite">
        {state.index === firstPriority && (
          <p className="section small">Dernière étape : vous répartissez des points entre des priorités. Ces répartitions indiquent l'importance que vous accordez aux enjeux ; elles pondèrent la comparaison avec les candidat·es.</p>
        )}
        {group ? (
          <section aria-labelledby={`${screenId}-title`}>
            <h2 id={`${screenId}-title`} className="question-text">{group.title}</h2>
            <p className="group-context">{group.context}</p>
            <div className="affirmations">
              {qs.map((x) => <QuestionView key={x.id} q={x} inGroup answer={state.answers[x.id]} onAnswer={onAnswer(x)} />)}
            </div>
          </section>
        ) : (
          <QuestionView q={q} answer={state.answers[q.id]} onAnswer={onAnswer(q)} />
        )}
      </div>

      {revealed && (
        <aside className="section learn" aria-label="Enjeux et arguments">
          <h3>Enjeux et arguments</h3>
          <p>{q.explanation}</p>
          <p className="small"><strong>Pour aller plus loin :</strong> {q.literature.map((id) => thinkers.get(id)?.name).filter(Boolean).join(' ; ')}</p>
          {qs.some((x) => x.factual) && (
            <p className="small muted">{group ? `L'affirmation « ${qs.find((x) => x.factual)!.text} » comporte une dimension factuelle.` : 'Cet énoncé comporte une dimension factuelle.'}</p>
          )}
        </aside>
      )}

      <div className="actions quiz-nav">
        <button type="button" className="btn" disabled={state.index === 0} onClick={() => dispatch({ type: 'back' })}>Étape précédente</button>
        {q.type === 'allocation' && !canNext && <button type="button" className="btn" onClick={() => dispatch({ type: 'next' })}>Passer</button>}
        <button type="button" className="btn btn-primary" disabled={!canNext} onClick={() => dispatch({ type: 'next' })}>
          {state.index + 1 === state.order.length ? 'Voir mes résultats' : 'Étape suivante'}
        </button>
      </div>
      {group && !canNext && <p className="small muted">Répondez aux quatre affirmations (« Je ne sais pas » compte comme une réponse) pour passer à l'étape suivante.</p>}
      <div className="actions small">
        {done >= PARTIAL_RESULTS_MIN && <button type="button" className="btn btn-small" onClick={() => dispatch({ type: 'finish' })}>Arrêter et voir des résultats partiels</button>}
        <button type="button" className="btn btn-small" onClick={onErase}>Tout effacer et recommencer</button>
      </div>
    </div>
  );
}
