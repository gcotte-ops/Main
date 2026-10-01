import { useId } from 'react';
import type { Answer, Question } from '../../domain/schemas';

export const LIKERT_LABELS: [number, string][] = [
  [-2, 'Pas du tout d\'accord'],
  [-1, 'Plutôt pas d\'accord'],
  [0, 'Neutre'],
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
/** « Neutre » compte comme une position centrale (0) ; « Je ne sais pas » exclut l'item du calcul. */
export const NO_OPINION = 'Je ne sais pas';
export const NO_CHOICE = 'Aucune de ces réponses / je ne sais pas';

/** `inGroup` : affirmation affichée dans un bloc (le titre et le contexte sont portés par l'écran). */
type Props = { q: Question; answer: Answer | undefined; onAnswer: (a: Answer) => void; inGroup?: boolean };

function ScaleChoices({ name, labels, value, onPick, compact }: { name: string; labels: [number, string][]; value: number | null | undefined; onPick: (v: -2 | -1 | 0 | 1 | 2 | null) => void; compact?: boolean }) {
  return (
    <div className={compact ? 'choices choices-row' : 'choices'}>
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

export function QuestionView({ q, answer, onAnswer, inGroup }: Props) {
  const id = useId();
  const current = answer?.kind === 'scale' ? answer.value : undefined;

  if (q.type === 'likert' && inGroup)
    return (
      <fieldset className="question affirmation card">
        <legend className="affirmation-text">{q.text}</legend>
        <ScaleChoices name={id} labels={LIKERT_LABELS} value={current} compact onPick={(v) => onAnswer({ kind: 'scale', value: v })} />
      </fieldset>
    );

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

  if (q.type === 'choice') {
    const picked = answer?.kind === 'choice' ? answer.index : undefined;
    return (
      <fieldset className="question">
        <legend><h2 className="question-text">{q.text}</h2></legend>
        <p className="small muted">Une seule réponse : celle qui se rapproche le plus de votre avis.</p>
        <div className="choices">
          {q.options!.map((o, i) => (
            <label key={o.label} className={`choice${picked === i ? ' is-selected' : ''}`}>
              <input type="radio" name={id} checked={picked === i} onChange={() => onAnswer({ kind: 'choice', index: i })} />
              <span>{o.label}</span>
            </label>
          ))}
          <label className={`choice choice-none${picked === null ? ' is-selected' : ''}`}>
            <input type="radio" name={id} checked={picked === null} onChange={() => onAnswer({ kind: 'choice', index: null })} />
            <span>{NO_CHOICE}</span>
          </label>
        </div>
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
  if (q.type === 'choice') return a.kind === 'choice';
  return a.kind === 'scale';
}
