import { useState } from 'react';
import type { Results } from '../engine/narrative';

/**
 * Option de commentaire par LLM (désactivée par défaut : VITE_ENABLE_LLM=true au build).
 * N'envoie que le vecteur de scores arrondis (jamais les réponses), après accord explicite.
 * En cas d'erreur, la synthèse du moteur de règles reste la référence.
 */
export const LLM_ENABLED = import.meta.env.VITE_ENABLE_LLM === 'true';

export function scorePayload(r: Results) {
  return { scores: Object.fromEntries(r.axes.flatMap((a) => (a.score.score === null ? [] : [[a.axis.id, Math.round(a.score.score)]]))) };
}

export function LlmPanel({ r }: { r: Results }) {
  const [consent, setConsent] = useState(false);
  const [state, setState] = useState<{ status: 'idle' | 'loading' | 'done' | 'error'; text?: string }>({ status: 'idle' });
  if (!LLM_ENABLED) return null;
  const payload = scorePayload(r);
  return (
    <div className="card llm">
      <h3>Commentaire rédigé par une IA (facultatif)</h3>
      <p className="small">
        Si vous l'acceptez, vos <strong>scores arrondis par axe</strong> (et seulement eux : {Object.keys(payload.scores).length} nombres, aucune réponse) seront envoyés
        à notre serveur, qui les transmet à un modèle d'IA d'Anthropic pour rédiger un commentaire neutre. Rien n'est conservé par l'application.
      </p>
      <details className="small"><summary>Voir exactement ce qui serait envoyé</summary><pre>{JSON.stringify(payload)}</pre></details>
      <label className="check small"><input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} /> J'accepte l'envoi de ces scores anonymes.</label>
      <div className="actions">
        <button
          type="button"
          className="btn btn-dark"
          disabled={!consent || state.status === 'loading'}
          onClick={async () => {
            setState({ status: 'loading' });
            try {
              const res = await fetch('/api/interpret', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(payload) });
              if (!res.ok) throw new Error(String(res.status));
              const json = (await res.json()) as { text?: string };
              if (!json.text) throw new Error('vide');
              setState({ status: 'done', text: json.text });
            } catch {
              setState({ status: 'error' });
            }
          }}
        >
          {state.status === 'loading' ? 'Rédaction en cours…' : 'Obtenir un commentaire'}
        </button>
      </div>
      {state.status === 'error' && <p className="small" role="status">Le commentaire n'a pas pu être obtenu. La synthèse ci-dessus, produite dans votre navigateur, reste disponible.</p>}
      {state.status === 'done' && <div className="section small" aria-live="polite">{state.text!.split(/\n{2,}/).map((p) => <p key={p.slice(0, 30)}>{p}</p>)}</div>}
    </div>
  );
}
