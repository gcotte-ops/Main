import { useMemo, useRef, useState } from 'react';
import type { Dataset } from '../domain/load';
import { PRIMARY_AXES, type AxisId, type Candidate, type Confidence } from '../domain/schemas';
import { buildResults, type AxisReading, type Results } from '../engine/narrative';
import { OPENNESS_WEIGHTS, opennessIndex } from '../engine/indices';
import { CONFIDENCE_WEIGHT, type CandidateMatch } from '../engine/matching';
import { fitPca, project } from '../engine/pca';
import { href } from '../router';
import { encodeScores } from '../state/share';
import type { QuizState } from '../state/quiz';
import { ChartFrame, LegendItem } from '../ui/charts/ChartFrame';
import { DivergingBars } from '../ui/charts/DivergingBars';
import { Heatmap, intersectionCells } from '../ui/charts/Heatmap';
import { Map2D, type MapPoint } from '../ui/charts/Map2D';
import { Radar } from '../ui/charts/Radar';
import { DataBanner, frDate } from '../ui/DataBanner';
import { exportNodePdf } from '../ui/exporting';
import { LlmPanel } from '../ui/LlmPanel';

const fmt = (v: number | null | undefined) => (v === null || v === undefined ? 'non mesuré' : `${v > 0 ? '+' : ''}${Math.round(v)}`);
const CONF_LABEL: Record<Confidence, string> = { H: 'élevée', M: 'moyenne', F: 'faible' };
const CONF_SPREAD: Record<Confidence, number> = { H: 10, M: 20, F: 35 };

export function ResultsPage({ data, state, onErase }: { data: Dataset; state: QuizState; onErase: () => void }) {
  const r = useMemo(() => buildResults(data, state.answers), [data, state.answers]);
  const pageRef = useRef<HTMLDivElement>(null);
  const [pdfBusy, setPdfBusy] = useState(false);
  const partial = r.answeredCount < data.questions.length;

  return (
    <div ref={pageRef} className="results">
      <header className="results-head">
        <h1>Vos résultats</h1>
        <DataBanner meta={data.meta} />
        <p><strong>Outil de réflexion, pas une consigne de vote.</strong> Données candidat·es à jour au {frDate(data.meta.dataDate)} (fichier 01) ; premier tour le {frDate(data.meta.electionRound1)}.</p>
        {partial && <p className="section small" role="status">Résultats calculés sur {r.answeredCount} réponses sur {data.questions.length} : les positions sur certains axes sont moins établies.</p>}
        {(r.bias.acquiescence || r.bias.tooFast) && (
          <div className="section small" role="status">
            {r.bias.acquiescence === 'high' && <p>Vous avez approuvé plus de 80 % des énoncés. Comme la moitié d'entre eux sont formulés dans un sens et l'autre moitié dans le sens opposé, cela peut traduire une tendance à acquiescer ; vos scores s'en trouvent rapprochés du centre.</p>}
            {r.bias.acquiescence === 'low' && <p>Vous avez rejeté plus de 80 % des énoncés, qui sont pourtant formulés pour moitié dans chaque sens ; vos scores s'en trouvent rapprochés du centre.</p>}
            {r.bias.tooFast && <p>Vous avez répondu en moins d'une seconde et demie par question en moyenne. Vous pouvez revenir sur certaines réponses pour vérifier qu'elles reflètent bien votre avis.</p>}
          </div>
        )}
        <nav aria-label="Sections des résultats" className="toc small">
          <a href="#r-radar">Radar</a> · <a href="#r-carte">Carte</a> · <a href="#r-archetypes">Courants</a> · <a href="#r-intersections">Intersections</a> ·{' '}
          <a href="#r-axes">Axe par axe</a> · <a href="#r-critique">Retour critique</a> · <a href="#r-candidats">Candidat·es</a> · <a href="#r-lectures">Lectures</a> · <a href="#r-export">Export</a>
        </nav>
      </header>

      <RadarSection r={r} />
      <MapSection data={data} r={r} />
      <ArchetypeSection r={r} />
      <IntersectionSection data={data} r={r} />
      <AxesSection r={r} />
      <CritiqueSection r={r} />
      <CandidatesSection data={data} r={r} />
      <ReadingsSection r={r} />

      <section id="r-export" className="section" aria-labelledby="export-title">
        <h2 id="export-title">Exporter et partager</h2>
        <p className="small">Les exports sont produits dans votre navigateur. Le lien de partage ne contient que vos scores arrondis par axe, jamais vos réponses, et il est placé après le « # » de l'adresse, qui n'est pas transmis au serveur.</p>
        <div className="actions">
          <button type="button" className="btn btn-dark" disabled={pdfBusy} onClick={async () => { if (!pageRef.current) return; setPdfBusy(true); try { await exportNodePdf(pageRef.current, 'boussole-2027-resultats'); } finally { setPdfBusy(false); } }}>
            Télécharger en PDF
          </button>
          <ShareButton r={r} />
          <button type="button" className="btn" onClick={onErase}>Effacer mes réponses</button>
        </div>
        <LlmPanel r={r} />
      </section>
    </div>
  );
}

/* ---------------------------------------------------------------- Radar */

function RadarSection({ r }: { r: Results }) {
  const [all, setAll] = useState(false);
  const rows = r.axes.filter((a) => all || a.axis.primary);
  const scores = Object.fromEntries(r.axes.map((a) => [a.axis.id, a.score]));
  return (
    <section id="r-radar" aria-labelledby="radar-h">
      <h2 id="radar-h">Vos positions</h2>
      <div className="grid-2">
        <ChartFrame
          title={`Radar des ${rows.length} axes`}
          description="Centre du graphique : pôle « moins » de chaque axe (−100) ; cercle médian : position centrale (0) ; bord : pôle « plus » (+100). Le halo indique l'intervalle de confiance à 95 %."
          fileName="boussole-radar"
          controls={<label className="check small"><input type="checkbox" checked={all} onChange={(e) => setAll(e.target.checked)} /> Afficher les 14 axes (dont 4 secondaires)</label>}
          legend={<><LegendItem shape="user" label="Votre position" /> <LegendItem shape="ci" label="Intervalle de confiance" /></>}
          table={<ScoreTable rows={rows} />}
        >
          <Radar axes={rows.map((a) => a.axis)} scores={scores} />
        </ChartFrame>
        <ChartFrame
          title="Position sur chaque axe"
          description="Barre : votre score (−100 à +100) ; trait : intervalle de confiance ; zone grisée : centre (−20 à +20). Barre hachurée en clair : position peu établie."
          fileName="boussole-barres"
          legend={<><LegendItem shape="user" label="Votre score" /></>}
          table={<ScoreTable rows={r.axes} />}
        >
          <DivergingBars rows={r.axes} />
        </ChartFrame>
      </div>
    </section>
  );
}

function ScoreTable({ rows }: { rows: AxisReading[] }) {
  return (
    <table>
      <caption className="visually-hidden">Scores par axe</caption>
      <thead><tr><th scope="col">Axe</th><th scope="col">Pôle −</th><th scope="col">Pôle +</th><th scope="col">Score</th><th scope="col">IC 95 %</th><th scope="col">Items</th><th scope="col">Niveau</th></tr></thead>
      <tbody>
        {rows.map((a) => (
          <tr key={a.axis.id}>
            <th scope="row">{a.axis.label}</th><td>{a.axis.poleMinus}</td><td>{a.axis.polePlus}</td>
            <td>{fmt(a.score.score)}</td><td>{a.score.ci ? `${fmt(a.score.ci[0])} à ${fmt(a.score.ci[1])}` : '—'}</td>
            <td>{a.score.nItems} (effectif {a.score.nEff})</td>
            <td>{a.level === null ? '—' : a.axis.levels[a.level]}{a.score.score !== null && !a.score.established ? ' (peu établie)' : ''}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/* ------------------------------------------------------------- Carte 2D */

function candidateVector(c: Candidate): Partial<Record<AxisId, number | null>> {
  return Object.fromEntries(PRIMARY_AXES.map((a) => [a, c.positions[a]?.value ?? null]));
}

function MapSection({ data, r }: { data: Dataset; r: Results }) {
  const [view, setView] = useState<'eco' | 'pca'>('eco');
  const user = Object.fromEntries(r.axes.map((a) => [a.axis.id, a.score.score]));
  const coded = data.candidates.filter((c) => PRIMARY_AXES.filter((a) => c.positions[a]?.value != null).length >= 5);

  const points: MapPoint[] = useMemo(() => {
    if (view === 'eco') {
      const pts: MapPoint[] = data.archetypes.map((a) => ({ id: a.id, label: a.name, kind: 'archetype', x: a.centroid.ECO ?? 0, y: opennessIndex(a.centroid) ?? 0 }));
      for (const c of coded) {
        const v = candidateVector(c);
        const y = opennessIndex(v);
        const eco = c.positions.ECO;
        if (eco?.value == null || y === null) continue;
        const confs = (Object.keys(OPENNESS_WEIGHTS) as AxisId[]).map((a) => c.positions[a]).filter((p) => p?.value != null).map((p) => CONF_SPREAD[p!.confidence]);
        pts.push({ id: c.id, label: c.name, kind: 'candidate', x: eco.value, y, ex: CONF_SPREAD[eco.confidence], ey: confs.reduce((s, x) => s + x, 0) / confs.length });
      }
      const uy = opennessIndex(user);
      if (user.ECO != null && uy !== null) {
        const eco = r.scores.ECO!;
        const cis = (Object.keys(OPENNESS_WEIGHTS) as AxisId[]).map((a) => r.scores[a]?.ci).filter(Boolean).map((ci) => (ci![1] - ci![0]) / 2);
        pts.push({ id: 'user', label: 'Vous', kind: 'user', x: user.ECO, y: uy, ex: eco.ci ? (eco.ci[1] - eco.ci[0]) / 2 : undefined, ey: cis.length ? cis.reduce((s, x) => s + x, 0) / cis.length : undefined });
      }
      return pts;
    }
    // ACP ajustée sur les archétypes et les candidat·es codé·es sur ≥ 8 axes (valeurs manquantes : moyenne).
    const pool = coded.filter((c) => PRIMARY_AXES.filter((a) => c.positions[a]?.value != null).length >= 8);
    const rawRows = [...data.archetypes.map((a) => PRIMARY_AXES.map((ax) => a.centroid[ax] ?? null)), ...pool.map((c) => PRIMARY_AXES.map((ax) => c.positions[ax]?.value ?? null))];
    const means = PRIMARY_AXES.map((_, j) => { const v = rawRows.map((row) => row[j]).filter((x): x is number => x !== null); return v.reduce((s, x) => s + x, 0) / v.length; });
    const fill = (row: (number | null)[]) => row.map((x, j) => x ?? means[j]!);
    const model = fitPca(rawRows.map(fill));
    const pts: MapPoint[] = data.archetypes.map((a, i) => { const [x, y] = project(model, fill(rawRows[i]!)); return { id: a.id, label: a.name, kind: 'archetype', x, y }; });
    pool.forEach((c, i) => { const row = rawRows[data.archetypes.length + i]!; const [x, y] = project(model, fill(row)); pts.push({ id: c.id, label: c.name, kind: 'candidate', x, y, imputed: row.some((v) => v === null) }); });
    const [ux, uy] = project(model, fill(PRIMARY_AXES.map((a) => user[a] ?? null)));
    pts.push({ id: 'user', label: 'Vous', kind: 'user', x: ux, y: uy });
    return pts;
  }, [view, data, r]);

  const domain = view === 'pca' ? Math.max(100, ...points.map((p) => Math.max(Math.abs(p.x), Math.abs(p.y)))) * 1.05 : 100;
  return (
    <section id="r-carte" aria-labelledby="carte-h">
      <h2 id="carte-h">Carte politique</h2>
      <ChartFrame
        title={view === 'eco' ? 'Économie × Ouverture–Fermeture' : 'Analyse en composantes principales'}
        description={
          view === 'eco'
            ? `Abscisse : axe ECO. Ordonnée : indice composite « Ouverture–Fermeture » = ${Object.entries(OPENNESS_WEIGHTS).map(([a, w]) => `${a} × ${w}`).join(' + ')}. Barres : incertitude (IC pour vous, confiance du codage pour les candidat·es).`
            : 'Les deux premières composantes résument les dix axes principaux à partir des archétypes et des candidat·es les plus complètement codé·es. Les axes non codés sont remplacés par la moyenne (losange clair).'
        }
        fileName="boussole-carte"
        controls={
          <div role="group" aria-label="Vue de la carte" className="segmented">
            <button type="button" className={view === 'eco' ? 'btn btn-small btn-dark' : 'btn btn-small'} aria-pressed={view === 'eco'} onClick={() => setView('eco')}>Économie × Ouverture</button>
            <button type="button" className={view === 'pca' ? 'btn btn-small btn-dark' : 'btn btn-small'} aria-pressed={view === 'pca'} onClick={() => setView('pca')}>Vue ACP</button>
          </div>
        }
        legend={<><LegendItem shape="user" label="Vous" /> <LegendItem shape="archetype" label="Archétypes (courants)" /> <LegendItem shape="candidate" label="Candidat·es (codage du fichier 01)" /></>}
        table={
          <table>
            <thead><tr><th scope="col">Point</th><th scope="col">Type</th><th scope="col">x</th><th scope="col">y</th></tr></thead>
            <tbody>{points.map((p) => <tr key={`${p.kind}-${p.id}`}><th scope="row">{p.label}</th><td>{p.kind === 'user' ? 'vous' : p.kind === 'archetype' ? 'archétype' : 'candidat·e'}</td><td>{Math.round(p.x)}</td><td>{Math.round(p.y)}</td></tr>)}</tbody>
          </table>
        }
      >
        <Map2D
          points={points}
          domain={domain}
          xLabel={view === 'eco' ? ['Néolibéral', 'Socialiste', 'ECO'] : ['', '', 'Composante 1']}
          yLabel={view === 'eco' ? ['Fermeture', 'Ouverture', 'CUL, ALT, GOV, ETA'] : ['', '', 'Composante 2']}
          showLabels="user-and-candidates"
        />
      </ChartFrame>
    </section>
  );
}

/* ----------------------------------------------------------- Archétypes */

function ArchetypeSection({ r }: { r: Results }) {
  return (
    <section id="r-archetypes" aria-labelledby="arch-h">
      <h2 id="arch-h">Les courants dont vous êtes le plus proche</h2>
      <p className="small muted">Affinité : moyenne d'une similarité de direction (cosinus) et d'une proximité de position (distance), sur les 14 axes. Un courant est un repère, pas une étiquette.</p>
      <ol className="cards">
        {r.top.map(({ match, lineage }) => (
          <li key={match.archetype.id} className="card">
            <h3>{match.archetype.name} <span className="badge">{match.affinity} %</span></h3>
            <p>{match.archetype.description}</p>
            <p className="small"><strong>Filiation intellectuelle :</strong> {lineage.map((t) => t.name).join(' ; ')}</p>
            <details className="small"><summary>Pourquoi ce centroïde ? Débats internes</summary>
              <p>{match.archetype.justification}</p>
              <ul>{match.archetype.internalTensions.map((t) => <li key={t}>{t}</li>)}</ul>
            </details>
          </li>
        ))}
      </ol>
      {r.contradictor && (
        <p className="section small"><strong>Un contradicteur :</strong> {r.contradictor.name}, référence du courant le plus éloigné de vos réponses (« {r.archetypes.at(-1)!.archetype.name} »). {r.contradictor.summary}</p>
      )}
    </section>
  );
}

/* --------------------------------------------------------- Intersections */

const INDEX_TEXT: Record<string, { title: string; body: string }> = {
  intersectionnalite: { title: 'Convergence intersectionnelle', body: 'Moyenne de ALT, ECO, CUL (et GEN quand l\'axe sera mesuré) orientés vers leurs pôles égalitaires. Kimberlé Crenshaw a montré que les discriminations se combinent plutôt qu\'elles ne s\'additionnent ; Patricia Hill Collins parle de « matrice de domination » ; Nancy Fraser lie redistribution et reconnaissance. Un indice élevé signifie que vos positions convergent comme le suppose cette lecture.' },
  fusionnisme: { title: 'Fusionnisme', body: 'Moyenne de ECO (pôle néolibéral), CUL (pôle conservateur) et REL (pôle traditionnaliste). Cette alliance du marché et de la tradition caractérise une partie de la droite ; Michéa et Deneen en soulignent la tension interne.' },
  'souverainisme-social': { title: 'Souverainisme social', body: 'Moyenne de ECO (pôle socialiste), ETA et UE (pôles nationaux). Polanyi et List éclairent cette protection de la société par la nation ; Rodrik et Stiglitz en discutent les limites.' },
};

function IntersectionSection({ data, r }: { data: Dataset; r: Results }) {
  const axes = data.axes.filter((a) => a.primary);
  const cells = intersectionCells(axes, r.scores).filter((c) => c.combo);
  return (
    <section id="r-intersections" aria-labelledby="inter-h">
      <h2 id="inter-h">Lecture intersectionnelle et combinaisons d'axes</h2>
      <p className="small muted">Ces indices décrivent des cohérences idéologiques documentées par la littérature ; ils ne notent personne.</p>
      <div className="cards grid-3">
        {r.indices.map((i) => (
          <div key={i.id} className="card">
            <h3>{INDEX_TEXT[i.id]!.title} <span className="badge">{i.value === null ? 'n. d.' : fmt(i.value)}</span></h3>
            <p className="small">{INDEX_TEXT[i.id]!.body}</p>
            <p className="small">{i.marked ? 'Toutes les composantes dépassent +30 : combinaison marquée.' : 'Combinaison non marquée dans vos réponses.'}</p>
          </div>
        ))}
      </div>
      <ChartFrame
        title="Carte des intersections (10 × 10)"
        description="Intensité d'une case = la plus faible des deux positions en valeur absolue : une case foncée signale deux positions marquées à la fois. Un point jaune signale une combinaison nommée par la littérature."
        fileName="boussole-intersections"
        legend={<><span className="legend-item"><span className="swatch heat-0" /> faible</span> <span className="legend-item"><span className="swatch heat-4" /> forte</span> <LegendItem shape="user" label="Combinaison remarquable" /></>}
        table={
          <table>
            <thead><tr><th scope="col">Combinaison</th><th scope="col">Axes</th><th scope="col">Intensité</th><th scope="col">Références</th></tr></thead>
            <tbody>{cells.length ? cells.map((c) => <tr key={`${c.a.id}-${c.b.id}`}><th scope="row">{c.combo!.name}</th><td>{c.a.id} × {c.b.id}</td><td>{Math.round(c.value)}</td><td>{c.combo!.ref}</td></tr>) : <tr><td colSpan={4}>Aucune combinaison remarquable (intensité ≥ 30).</td></tr>}</tbody>
          </table>
        }
      >
        <Heatmap axes={axes} scores={r.scores} />
      </ChartFrame>
      {cells.length > 0 && <ul className="small">{cells.slice(0, 6).map((c) => <li key={`${c.a.id}-${c.b.id}`}><strong>{c.combo!.name}</strong> ({c.a.label} × {c.b.label}) — {c.combo!.ref}</li>)}</ul>}
    </section>
  );
}

/* --------------------------------------------------------- Axe par axe */

function AxesSection({ r }: { r: Results }) {
  return (
    <section id="r-axes" aria-labelledby="axes-h">
      <h2 id="axes-h">Évaluation axe par axe</h2>
      <div className="cards grid-2">
        {r.axes.map((a) => (
          <article key={a.axis.id} className="card axis-card">
            <h3>{a.axis.label} <span className="badge">{fmt(a.score.score)}</span></h3>
            <p className="small muted">{a.axis.poleMinus} ↔ {a.axis.polePlus} · {a.level === null ? 'non mesuré' : a.axis.levels[a.level]}{a.score.ci ? ` · IC 95 % : ${fmt(a.score.ci[0])} à ${fmt(a.score.ci[1])}` : ''}</p>
            {a.score.score !== null && !a.score.established && <p className="small"><strong>Position peu établie</strong> : moins de 4 items effectifs ont été répondus sur cet axe.</p>}
            {a.text && <p>{a.text.text}</p>}
            <p className="small"><strong>Auteurs proches :</strong> {a.near.map((t) => t.name).join(' ; ') || '—'}<br /><strong>Contradicteurs :</strong> {a.opposed.map((t) => t.name).join(' ; ') || '—'}</p>
            {a.text && <p className="small reflect"><strong>Question de réflexion :</strong> {a.text.question}</p>}
            {a.axis.facets?.map((f) => {
              const s = r.scores[f.id as keyof typeof r.scores];
              return s?.score != null ? <p key={f.id} className="small">{f.label} : {fmt(s.score)} ({f.poleMinus} ↔ {f.polePlus}){s.established ? '' : ', peu établie'}</p> : null;
            })}
          </article>
        ))}
      </div>
    </section>
  );
}

/* ------------------------------------------------------- Retour critique */

function CritiqueSection({ r }: { r: Results }) {
  return (
    <section id="r-critique" aria-labelledby="crit-h">
      <h2 id="crit-h">Synthèse et retour critique</h2>
      <div className="section">{r.synthesis.map((p) => <p key={p.slice(0, 40)}>{p}</p>)}</div>
      {r.tensions.length > 0 && (
        <>
          <h3>Tensions internes à explorer</h3>
          <ul className="cards">{r.tensions.map((t) => <li key={t.id} className="card"><h4>{t.title}</h4><p>{t.text}</p></li>)}</ul>
        </>
      )}
      {r.inconsistencies.length > 0 && (
        <>
          <h3>Des réponses qui semblent se contredire</h3>
          <ul className="cards">{r.inconsistencies.map((x) => <li key={`${x.a.id}-${x.b.id}`} className="card small">{x.text}</li>)}</ul>
        </>
      )}
    </section>
  );
}

/* ----------------------------------------------------------- Candidat·es */

const AXIS_LABEL: Record<string, string> = { ECO: 'économie', IDE: 'identité', ENV: 'environnement', REL: 'religion', ETA: 'État', CUL: 'mœurs', ALT: 'altérité', UE: 'Europe', GMO: 'gouvernance mondiale', GOV: 'gouvernance' };

function CandidateCard({ m, data }: { m: CandidateMatch; data: Dataset }) {
  const c = m.candidate;
  const measures = new Map(data.measures.map((x) => [x.id, x]));
  return (
    <li className="card">
      <h4>{c.name} <span className="small muted">— {c.party}</span> {m.affinity !== null && <span className="badge">{m.affinity} %</span>}</h4>
      <p className="small">Statut : {c.statusDetail.toLowerCase().startsWith(c.status.toLowerCase().slice(0, 6)) ? c.statusDetail : `${c.status} — ${c.statusDetail}`} · Complétude des données : {Math.round(m.completeness * 100)} % des axes principaux · Mise à jour : {frDate(c.lastUpdated)}</p>
      {c.alternates && <p className="small">Candidature de remplacement possible : {c.alternates.join(', ')} (le fichier 01 ne code pas de positions distinctes).</p>}
      {m.axesUsed > 0 && (
        <p className="small">
          <strong>Vous convergez sur :</strong> {m.converge.map((g) => AXIS_LABEL[g.axis]).join(', ')}. <strong>Vous divergez sur :</strong> {m.diverge.map((g) => AXIS_LABEL[g.axis]).join(', ')}.
        </p>
      )}
      <details className="small">
        <summary>Positions codées et sources</summary>
        <table>
          <thead><tr><th scope="col">Axe</th><th scope="col">Position</th><th scope="col">Vous</th><th scope="col">Confiance</th><th scope="col">Justification et source</th></tr></thead>
          <tbody>
            {PRIMARY_AXES.map((a) => {
              const p = c.positions[a];
              const gap = m.converge.concat(m.diverge).find((g) => g.axis === a);
              return (
                <tr key={a}>
                  <th scope="row">{a}</th>
                  <td>{p?.value == null ? 'non renseigné' : fmt(p.value)}</td>
                  <td>{gap ? fmt(gap.user) : '—'}</td>
                  <td>{p?.value == null ? '—' : `${CONF_LABEL[p.confidence]} (poids ${CONFIDENCE_WEIGHT[p.confidence]})`}</td>
                  <td>{p?.justification} <span className="muted">{p?.sources.join(' ; ')}</span></td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {c.measureIds.length > 0 && (
          <>
            <p><strong>Mesures citées dans le fichier 01 ({c.section}) :</strong></p>
            <ul>{c.measureIds.slice(0, 12).map((id) => <li key={id}>{measures.get(id)?.theme} : {measures.get(id)?.text}</li>)}</ul>
            {c.measureIds.length > 12 && <p className="muted">… et {c.measureIds.length - 12} autres mesures.</p>}
          </>
        )}
        <p><strong>Sources :</strong> {c.sources.join(' ; ')}</p>
      </details>
    </li>
  );
}

function CandidatesSection({ data, r }: { data: Dataset; r: Results }) {
  const { ranked, unranked } = r.candidates;
  const closest = ranked.slice(0, 5);
  const farthest = ranked.slice(-3).reverse().filter((m) => !closest.includes(m));
  const primary = [...ranked, ...unranked].filter((m) => m.candidate.status === 'Primaire');
  return (
    <section id="r-candidats" aria-labelledby="cand-h">
      <h2 id="cand-h">Comparaison indicative avec les candidat·es</h2>
      <DataBanner meta={data.meta} />
      <p className="small">
        Distance calculée sur les dix axes principaux, pondérée par la confiance du codage (élevée 1, moyenne 0,6, faible 0,3) et par vos priorités. Les axes non codés sont ignorés ;
        seules les candidatures codées sur au moins 5 axes sont classées. Les positions proviennent exclusivement du fichier 01 ; elles sont une hypothèse de calibrage à faire auditer.
      </p>
      <h3>Les plus proches de vos réponses</h3>
      <ol className="cards">{closest.map((m) => <CandidateCard key={m.candidate.id} m={m} data={data} />)}</ol>
      <h3>Les plus éloigné·es</h3>
      <ol className="cards">{farthest.map((m) => <CandidateCard key={m.candidate.id} m={m} data={data} />)}</ol>
      <h3>Primaire « Choisir 2027 » (PS et Place publique, 9-10 et 16-17 octobre 2026)</h3>
      <p className="small">Les cinq candidat·es sont affiché·es jusqu'au résultat. Seul Raphaël Glucksmann est codé dans le fichier 01 ; les autres sont « non renseignés ».</p>
      <ul className="cards">{primary.map((m) => <CandidateCard key={m.candidate.id} m={m} data={data} />)}</ul>
      <details>
        <summary>Autres candidatures non classées (données insuffisantes) : {unranked.filter((m) => m.candidate.status !== 'Primaire').length}</summary>
        <ul className="cards">{unranked.filter((m) => m.candidate.status !== 'Primaire').map((m) => <CandidateCard key={m.candidate.id} m={m} data={data} />)}</ul>
      </details>
      <details>
        <summary>Toutes les candidatures classées ({ranked.length})</summary>
        <table>
          <thead><tr><th scope="col">Rang</th><th scope="col">Candidat·e</th><th scope="col">Affinité</th><th scope="col">Axes comparés</th><th scope="col">Statut</th></tr></thead>
          <tbody>{ranked.map((m, i) => <tr key={m.candidate.id}><td>{i + 1}</td><th scope="row">{m.candidate.name}</th><td>{m.affinity} %</td><td>{m.axesUsed}</td><td>{m.candidate.status}</td></tr>)}</tbody>
        </table>
      </details>
    </section>
  );
}

/* --------------------------------------------------------------- Lectures */

function ReadingsSection({ r }: { r: Results }) {
  const role = { confirme: 'Pour approfondir', nuance: 'Pour nuancer', contredit: 'Pour se confronter' };
  return (
    <section id="r-lectures" aria-labelledby="lect-h">
      <h2 id="lect-h">Trois lectures</h2>
      <ul className="cards grid-3">
        {r.readings.map((x) => (
          <li key={x.role} className="card">
            <h3>{role[x.role]}</h3>
            <p><strong>{x.thinker.name}</strong> <span className="muted small">({x.thinker.dates})</span></p>
            <p className="small">{x.thinker.summary}</p>
            <p className="small muted">{x.why}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}

function ShareButton({ r }: { r: Results }) {
  const [copied, setCopied] = useState(false);
  const code = encodeScores(Object.fromEntries(r.axes.flatMap((a) => (a.score.score === null ? [] : [[a.axis.id, a.score.score]]))));
  const url = `${window.location.origin}${window.location.pathname}${href.shared(code)}`;
  return (
    <button
      type="button"
      className="btn"
      onClick={async () => {
        try { await navigator.clipboard.writeText(url); setCopied(true); } catch { window.prompt('Copiez ce lien :', url); }
      }}
    >
      {copied ? 'Lien copié' : 'Copier un lien de partage (scores seulement)'}
    </button>
  );
}
