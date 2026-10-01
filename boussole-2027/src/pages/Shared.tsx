import type { Dataset } from '../domain/load';
import { rankArchetypes } from '../engine/matching';
import { levelOf, type AxisScore } from '../engine/scoring';
import { href } from '../router';
import { decodeScores } from '../state/share';
import { Radar } from '../ui/charts/Radar';

/** Profil partagé : scores seulement (pas de réponses, donc ni intervalles de confiance ni diagnostic). */
export function SharedPage({ data, code }: { data: Dataset; code: string }) {
  const v = decodeScores(code);
  if (!v) return <section className="section"><h1>Lien invalide</h1><p>Ce lien de partage n'a pas pu être lu.</p><a href={href.home}>Accueil</a></section>;
  const axes = data.axes.filter((a) => a.enabled);
  const scores: Record<string, AxisScore> = Object.fromEntries(Object.entries(v).map(([k, s]) => [k, { score: s!, ci: null, nItems: 0, nEff: 0, established: true }]));
  const top = rankArchetypes(v, data.archetypes).slice(0, 3);
  return (
    <article>
      <h1>Profil partagé</h1>
      <p>Ce profil a été partagé par une personne ayant répondu à Boussole 2027. Il contient uniquement ses scores arrondis, sans ses réponses. Outil de réflexion, pas une consigne de vote.</p>
      <div className="grid-2">
        <figure className="chart"><h2>Radar des 15 axes</h2><Radar axes={axes} scores={scores} /></figure>
        <div>
          <h2>Courants les plus proches</h2>
          <ol>{top.map((m) => <li key={m.archetype.id}>{m.archetype.name} ({m.affinity} %)</li>)}</ol>
          <table>
            <thead><tr><th scope="col">Axe</th><th scope="col">Score</th><th scope="col">Niveau</th></tr></thead>
            <tbody>{axes.map((a) => { const s = v[a.id]; return <tr key={a.id}><th scope="row">{a.label}</th><td>{s ?? '—'}</td><td>{s === undefined ? '—' : a.levels[levelOf(s)]}</td></tr>; })}</tbody>
          </table>
        </div>
      </div>
      <a className="btn btn-primary" href={href.home}>Faire le questionnaire</a>
    </article>
  );
}
