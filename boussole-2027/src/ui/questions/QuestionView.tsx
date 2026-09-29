import { useId } from 'react';
import type { Answer, Question } from '../../domain/schemas';

export const LIKERT_LABELS: [number, string][] = [
  [-2, 'Pas du tout d\'accord'],
  [-1, 'Plutôt pas d\'accord'],
  [0, 'Ni d\'accord ni pas d\'accord'],
  [1, 'Plutôt d\'accord'],
  [2, 'Tout à fait d\'accord'],
];
const DILEMMA_LABELS: [number, string][] = [
  [-2, 'A, nettement'],
  [-1, 'Plutôt A'],
  [0, 'Les deux se valent'],
  [1, 'Plutôt B'],
  [2, 'B, nettement'],
];
export const NO_OPINION = 'Je ne sais pas / sans avis';

type Props = { q: Question; answer: Answer | undefined; onAnswer: (a: Answer) => void };

function ScaleChoices({ name, labels, value, onPick }: { name: string; labels: [number, string][]; value: number | null | undefined; onPick: (v: -2 | -1 | 0 | 1 | 2 | null) => void }) {
  return (
    <div className="choices">
      {labels.map(([v, label]) => (
        <label key={v} className={`choice${value === v ? ' is-selected' : ''}`}>
          <input type="radio" name={name} checked={value === v} onChange={() => onPick(v as -2 | -1 | 0 | 1 | 2)} />
          <span>{label}</span>
        </label>
      ))}
      <label className={`choice choice-none${value === null ? ' is-selected' : ''}`}>
        <input type="radio" name={name} checked={value === null} onChange={() => onPick(null)} />
        <span>{NO_OPINION}</span>
      </label>
    </div>
  );
}

export function QuestionView({ q, answer, onAnswer }: Props) {
  const id = useId();
  const current = answer?.kind === 'scale' ? answer.value : undefined;

  if (q.type === 'likert')
    return (
      <fieldset className="question">
        <legend><h2 className="question-text">{q.text}</h2></legend>
        <ScaleChoices name={id} labels={LIKERT_LABELS} value={current} onPick={(v) => onAnswer({ kind: 'scale', value: v })} />
      </fieldset>
    );

  if (q.type === 'dilemma') {
    const [A, B] = q.options!;
    return (
      <fieldset className="question">
        <legend><h2 className="question-text">{q.text}</h2></legend>
        <div className="dilemma">
          <p className="card"><strong>A.</strong> {A!.label}</p>
          <p className="card"><strong>B.</strong> {B!.label}</p>
        </div>
        <ScaleChoices name={id} labels={DILEMMA_LABELS} value={current} onPick={(v) => onAnswer({ kind: 'scale', value: v })} />
      </fieldset>
    );
  }

  const points = answer?.kind === 'allocation' ? answer.points : q.options!.map(() => 0);
  const used = points.reduce((s, p) => s + p, 0);
  const set = (i: number, delta: number) => {
    const next = [...points];
    next[i] = Math.max(0, Math.min(10, (next[i] ?? 0) + delta));
    if (next.reduce((s, p) => s + p, 0) <= 10) onAnswer({ kind: 'allocation', points: next });
  };
  return (
    <fieldset className="question">
      <legend><h2 className="question-text">{q.text}</h2></legend>
      <p className="small" aria-live="polite">Points utilisés : <strong>{used}</strong> / 10{used < 10 ? ` — il reste ${10 - used} point${10 - used > 1 ? 's' : ''}` : ''}</p>
      <ul className="allocation">
        {q.options!.map((o, i) => (
          <li key={o.label} className="card allocation-row">
            <span id={`${id}-${i}`}>{o.label}</span>
            <span className="stepper">
              <button type="button" className="btn btn-small" aria-label={`Retirer un point : ${o.label}`} disabled={(points[i] ?? 0) === 0} onClick={() => set(i, -1)}>−</button>
              <output aria-labelledby={`${id}-${i}`} className="stepper-value">{points[i] ?? 0}</output>
              <button type="button" className="btn btn-small" aria-label={`Ajouter un point : ${o.label}`} disabled={used >= 10} onClick={() => set(i, 1)}>+</button>
            </span>
          </li>
        ))}
      </ul>
    </fieldset>
  );
}

export function isAnswered(q: Question, a: Answer | undefined): boolean {
  if (!a) return false;
  if (q.type === 'allocation') return a.kind === 'allocation' && a.points.reduce((s, p) => s + p, 0) === 10;
  return a.kind === 'scale';
}
