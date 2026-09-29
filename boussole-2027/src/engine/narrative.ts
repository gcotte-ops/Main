import type { Answers, Archetype, Axis, AxisId, AxisLevelText, Tension, Thinker } from '../domain/schemas';
import { PRIMARY_AXES, SECONDARY_AXES } from '../domain/schemas';
import type { Dataset } from '../domain/load';
import { detectBias, findInconsistencies, type Inconsistency, type ResponseBias } from './diagnostics';
import { computeIndices, detectTensions, type IdeologicalIndex } from './indices';
import {
  computeSalience,
  pickContradictor,
  rankArchetypes,
  rankCandidates,
  userVector,
  type ArchetypeMatch,
  type CandidateMatch,
} from './matching';
import { computeScores, levelOf, type AxisScore, type Scores } from './scoring';

/**
 * Moteur de règles de restitution (fonctionne hors ligne, sans LLM) : assemble scores, textes par
 * niveau, archétypes, indices, tensions, correspondances et synthèse à partir des données validées.
 */
export const ACTIVE_AXES: AxisId[] = [...PRIMARY_AXES, ...SECONDARY_AXES];

export interface AxisReading {
  axis: Axis;
  score: AxisScore;
  level: 0 | 1 | 2 | 3 | 4 | null;
  text: AxisLevelText | null;
  near: Thinker[];
  opposed: Thinker[];
}

export interface Reading { role: 'confirme' | 'nuance' | 'contredit'; thinker: Thinker; why: string }

export interface Results {
  scores: Scores;
  axes: AxisReading[];
  archetypes: ArchetypeMatch[];
  top: { match: ArchetypeMatch; lineage: Thinker[] }[];
  contradictor: Thinker | undefined;
  indices: IdeologicalIndex[];
  tensions: Tension[];
  inconsistencies: Inconsistency[];
  bias: ResponseBias;
  salience: Partial<Record<AxisId, number>>;
  candidates: { ranked: CandidateMatch[]; unranked: CandidateMatch[] };
  synthesis: string[];
  readings: Reading[];
  answeredCount: number;
}

const safe = (ids: string[], byId: Map<string, Thinker>) =>
  ids.map((id) => byId.get(id)).filter((t): t is Thinker => !!t && !t.restricted);

const wordCount = (paras: string[]) => paras.join(' ').split(/\s+/).filter((w) => /[\p{L}\d]/u.test(w)).length;
const firstSentences = (s: string, n: number) => (s.match(/[^.!?]+[.!?]+(\s|$)/g) ?? [s]).slice(0, n).join('').trim();
const lc = (s: string) => s.charAt(0).toLowerCase() + s.slice(1);

export function buildResults(d: Dataset, answers: Answers, opts: { draws?: number } = {}): Results {
  const byId = new Map(d.thinkers.map((t) => [t.id, t]));
  const scores = computeScores(d.questions, answers, opts);
  const axisById = new Map(d.axes.map((a) => [a.id, a]));

  const axes: AxisReading[] = ACTIVE_AXES.map((id) => {
    const axis = axisById.get(id)!;
    const score = scores[id] ?? { score: null, ci: null, nItems: 0, nEff: 0, established: false };
    const level = score.score === null ? null : levelOf(score.score);
    const text = level === null ? null : (d.axisLevels.find((t) => t.axis === id && t.level === level) ?? null);
    return { axis, score, level, text, near: text ? safe(text.near, byId) : [], opposed: text ? safe(text.opposed, byId) : [] };
  });

  const user = userVector(scores, ACTIVE_AXES);
  const archetypes = rankArchetypes(user, d.archetypes);
  const top = archetypes.slice(0, 3).map((match) => ({ match, lineage: safe(match.archetype.lineage, byId).slice(0, 3) }));
  const contradictor = pickContradictor(archetypes, d.thinkers);
  const indices = computeIndices(scores);
  const tensions = detectTensions(scores, d.tensions, 3);
  const salience = computeSalience(d.questions, answers);
  const candidates = rankCandidates(userVector(scores, [...PRIMARY_AXES]), d.candidates, salience);

  const readings = pickReadings(axes, top[0]?.match.archetype, contradictor, byId);
  const synthesis = writeSynthesis(axes, top.map((t) => t.match), tensions, indices, readings);

  return {
    scores, axes, archetypes, top, contradictor, indices, tensions,
    inconsistencies: findInconsistencies(d.questions, answers),
    bias: detectBias(d.questions, answers),
    salience, candidates, synthesis, readings,
    answeredCount: Object.values(answers).filter((a) => (a.kind === 'scale' ? a.value !== null : true)).length,
  };
}

/** Trois lectures : une qui confirme (filiation), une qui nuance (centre de l'axe le plus marqué), une qui contredit. */
function pickReadings(axes: AxisReading[], a: Archetype | undefined, contradictor: Thinker | undefined, byId: Map<string, Thinker>): Reading[] {
  const out: Reading[] = [];
  const used = new Set<string>();
  const confirm = a ? safe(a.lineage, byId)[0] : undefined;
  if (confirm) { out.push({ role: 'confirme', thinker: confirm, why: `Une référence du courant « ${a!.name} », dont votre profil est le plus proche.` }); used.add(confirm.id); }
  const marked = axes.filter((x) => x.score.score !== null && x.score.established).sort((x, y) => Math.abs(y.score.score!) - Math.abs(x.score.score!))[0];
  if (marked) {
    const pool = [...marked.axis.thinkers.center, ...(marked.text?.opposed ?? [])];
    const nuance = safe(pool, byId).find((t) => !used.has(t.id));
    if (nuance) { out.push({ role: 'nuance', thinker: nuance, why: `Pour mettre à l'épreuve votre position la plus marquée (${marked.axis.label}).` }); used.add(nuance.id); }
  }
  if (contradictor && !used.has(contradictor.id)) out.push({ role: 'contredit', thinker: contradictor, why: 'Une référence du courant le plus éloigné de vos réponses, pour en comprendre les meilleurs arguments.' });
  return out;
}

function writeSynthesis(axes: AxisReading[], top: ArchetypeMatch[], tensions: Tension[], indices: IdeologicalIndex[], readings: Reading[]): string[] {
  const measured = axes.filter((x) => x.score.score !== null);
  if (!measured.length || !top.length) return ['Vous n\'avez pas encore répondu à suffisamment de questions pour établir une synthèse.'];
  const [a1, a2, a3] = top;
  const p: string[] = [];

  p.push(
    `Parmi les dix-huit courants de référence, votre profil se rapproche d'abord de « ${a1!.archetype.name} » (${a1!.affinity} % d'affinité)` +
      (a2 && a3 ? `, puis de « ${a2.archetype.name} » (${a2.affinity} %) et de « ${a3.archetype.name} » (${a3.affinity} %). ` : '. ') +
      firstSentences(a1!.archetype.description, 2) +
      ' Ce rapprochement est indicatif : un courant regroupe des positions typiques, et personne n\'y correspond exactement.',
  );

  const strong = [...measured].filter((x) => x.score.established).sort((x, y) => Math.abs(y.score.score!) - Math.abs(x.score.score!)).slice(0, 3);
  const central = measured.filter((x) => x.level === 2).map((x) => x.axis.label.toLowerCase());
  const fmt = (x: AxisReading) => `${x.axis.label.toLowerCase()} (${lc(x.axis.levels[x.level!])}, ${x.score.score! > 0 ? '+' : ''}${Math.round(x.score.score!)})`;
  if (strong.length)
    p.push(
      `Vos positions les plus affirmées concernent ${strong.map(fmt).join(', ').replace(/, ([^,]*)$/, ' et $1')}. ` +
        (central.length
          ? `Vous vous situez en revanche près du centre sur ${central.slice(0, 4).join(', ').replace(/, ([^,]*)$/, ' et $1')}, ce qui peut traduire une position de synthèse, une hésitation ou des convictions qui ne se laissent pas ranger sur cet axe.`
          : 'Vous ne vous situez au centre sur aucun axe : vos réponses dessinent des convictions nettes, que les objections présentées plus bas permettent de mettre à l\'épreuve.'),
    );

  if (tensions.length) {
    p.push(
      `Certaines combinaisons de vos réponses ouvrent des débats connus au sein des courants eux-mêmes. ` +
        tensions.slice(0, 3).map((t) => `${t.title} : ${lc(firstSentences(t.text, 2))}`).join(' '),
    );
  } else {
    p.push(
      'Aucune des tensions répertoriées par l\'outil ne ressort de vos réponses : vos positions forment un ensemble cohérent au regard des courants décrits. ' +
        (a1!.archetype.internalTensions[0] ? `Le courant dont vous êtes le plus proche connaît néanmoins ses propres débats, par exemple : ${lc(a1!.archetype.internalTensions[0])}` : ''),
    );
  }

  const marked = indices.filter((i) => i.marked);
  const INDEX_LABEL: Record<IdeologicalIndex['id'], string> = {
    intersectionnalite: 'une convergence de vos positions vers les pôles égalitaires sur l\'altérité, l\'économie et les mœurs, caractéristique de la lecture intersectionnelle (Crenshaw, Hill Collins, Fraser)',
    fusionnisme: 'une combinaison de libéralisme économique, de conservatisme des mœurs et d\'attachement religieux caractéristique du « fusionnisme »',
    'souverainisme-social': 'une combinaison de protection sociale et de souveraineté nationale caractéristique du « souverainisme social » (Polanyi, List)',
  };
  if (marked.length) p.push(`Vos réponses présentent ${marked.map((i) => INDEX_LABEL[i.id]).join(' ; ')}. Ces indices décrivent une cohérence idéologique ; ils ne vous notent pas.`);

  const r = readings.map((x) => x.thinker.name);
  p.push(
    'Ces résultats décrivent des positions et leurs arguments, pas une personne, et chaque score est entouré d\'une marge d\'incertitude. ' +
      (r.length === 3 ? `Pour prolonger la réflexion, trois lectures : ${r[0]} pour approfondir, ${r[1]} pour nuancer, ${r[2]} pour vous confronter au point de vue opposé.` : ''),
  );

  // Ajustement de longueur (cible 250–400 mots).
  if (wordCount(p) < 250 && a1!.archetype.internalTensions.length > 1)
    p.splice(p.length - 1, 0, `Débats internes du courant « ${a1!.archetype.name} » : ${a1!.archetype.internalTensions.map(lc).join(' ; ').replace(/\.(?= ;)/g, '')}`);
  if (wordCount(p) < 250 && a2) p.splice(p.length - 1, 0, `Le deuxième courant qui vous ressemble, « ${a2.archetype.name} », se caractérise ainsi : ${lc(firstSentences(a2.archetype.description, 2))}`);
  while (wordCount(p) > 400 && tensions.length > 1) {
    const idx = p.findIndex((x) => x.startsWith('Certaines combinaisons'));
    if (idx < 0) break;
    tensions = tensions.slice(0, -1);
    p[idx] = `Certaines combinaisons de vos réponses ouvrent des débats connus au sein des courants eux-mêmes. ${tensions.map((t) => `${t.title} : ${lc(firstSentences(t.text, 1))}`).join(' ')}`;
  }
  return p;
}
