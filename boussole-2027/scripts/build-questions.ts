/**
 * Convertit le questionnaire rédigé (docs/questionnaire-v2/*.json, source de travail) vers les données
 * de l'application : src/data/questions.json (une entrée par affirmation, choix ou répartition) et
 * src/data/groups.json (titre et contexte des blocs affichés ensemble).
 *  - Affirmation d'un bloc → item Likert ; une clé « AXE.facette » devient facet / facetLoading.
 *  - Question à choix → type « choice » ; les clés de facette vont dans options[].facets.
 *  - Répartition → type « allocation ».
 * Usage : npm run build:questions   (--check : échoue si les fichiers générés ne sont pas à jour)
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { dominantAxis } from '../src/domain/lint';
import { GroupSchema, QuestionSchema, type AxisId, type Group, type Question } from '../src/domain/schemas';

const ROOT = join(import.meta.dirname, '..');
const SRC = join(ROOT, 'docs/questionnaire-v2');
type W = Record<string, number>;
interface Aff { id: string; texte: string; theme?: string; poids: W; mesures?: string[]; factuel?: boolean; paire?: string }
interface Bloc { id: string; titre: string; theme: string; contexte: string; suite_de?: string; affirmations: Aff[]; auteurs: string[]; explication: string }
interface Choix { id: string; theme: string; question: string; options: { texte: string; poids: W }[]; auteurs: string[]; explication: string }
const load = <T>(f: string) => JSON.parse(readFileSync(join(SRC, f), 'utf8')) as T;

/** Rubriques (ordre de passage et libellé de progression). « priorites » passe toujours en dernier. */
export const RUBRIQUES: Record<string, string[]> = {
  economie: ['B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B43', 'C02', 'C09', 'C11', 'A02', 'A10'],
  ecologie: ['B08', 'B09', 'B10', 'B11', 'C04', 'A08'],
  religion: ['B12', 'B13', 'B14', 'B15', 'C07', 'A07'],
  nation: ['B16', 'B17', 'B18', 'B19'],
  societe: ['B20', 'B21', 'B22', 'B23', 'B24', 'C13', 'C15'],
  immigration: ['B25', 'B26', 'B27', 'B28', 'C03', 'C10'],
  international: ['B29', 'B30', 'B31', 'B32', 'C05', 'C06', 'A03', 'A04'],
  institutions: ['B33', 'B34', 'B35', 'B36', 'B39', 'B40', 'B42', 'B44', 'C01', 'C12', 'C14'],
  securite: ['B37', 'B38', 'C08'],
  territoires: ['B41', 'A05', 'A06'],
  priorites: ['A01', 'A09'],
};

const splitWeights = (w: W) => {
  const loadings: W = {};
  const facets: W = {};
  for (const [k, v] of Object.entries(w)) (k.includes('.') ? facets : loadings)[k] = v;
  return { loadings, facets };
};

export function buildQuestions(): { questions: Question[]; groups: Group[] } {
  const blocs = [...load<Bloc[]>('blocs-1.json'), ...load<Bloc[]>('blocs-2.json')];
  const choix = load<Choix[]>('choix.json');
  const reps = load<Choix[]>('repartitions.json');
  const rubrique = new Map(Object.entries(RUBRIQUES).flatMap(([r, ids]) => ids.map((id) => [id, r] as const)));
  const blockOf = (id: string) => {
    const r = rubrique.get(id);
    if (!r) throw new Error(`${id} n'est classé dans aucune rubrique (RUBRIQUES)`);
    return r;
  };

  const questions: Question[] = [];
  for (const b of blocs) {
    for (const a of b.affirmations) {
      const { loadings, facets } = splitWeights(a.poids);
      const facet = Object.entries(facets);
      if (facet.length > 1) throw new Error(`${a.id} : une seule facette par affirmation`);
      const primary = (Object.entries(loadings).sort((x, y) => Math.abs(y[1]) - Math.abs(x[1]))[0]?.[0] ?? facet[0]![0].split('.')[0]) as AxisId;
      questions.push({
        id: a.id,
        text: a.texte,
        type: 'likert',
        primaryAxis: primary,
        ...(facet.length ? { facet: facet[0]![0], facetLoading: facet[0]![1] } : {}),
        loadings,
        theme: a.theme ?? b.theme,
        block: blockOf(b.id),
        group: b.id,
        ...(a.paire ? { pair: a.paire } : {}),
        reversed: (loadings[primary] ?? 0) < 0,
        ...(a.mesures?.length ? { sourceMeasure: a.mesures } : {}),
        literature: b.auteurs,
        explanation: b.explication,
        ...(a.factuel ? { factual: true } : {}),
      } as Question);
    }
  }
  for (const [type, list] of [['choice', choix], ['allocation', reps]] as const) {
    for (const c of list) {
      const options = c.options.map((o) => {
        const { loadings, facets } = splitWeights(o.poids);
        return { label: o.texte, loadings, ...(Object.keys(facets).length ? { facets } : {}) };
      });
      const q = { id: c.id, text: c.question, type, primaryAxis: 'ECO', options, theme: c.theme, block: blockOf(c.id), reversed: false, literature: c.auteurs, explanation: c.explication } as Question;
      q.primaryAxis = dominantAxis(q) ?? 'ECO';
      questions.push(q);
    }
  }
  const groups = blocs.map((b) => ({ id: b.id, title: b.titre, context: b.contexte, ...(b.suite_de ? { follows: b.suite_de } : {}) }));
  return { questions: questions.map((q) => QuestionSchema.parse(q)), groups: groups.map((g) => GroupSchema.parse(g)) };
}

/** Une clé par ligne, valeurs compactes (options : une par ligne) : lisible et diff ligne à ligne. */
export function formatJson(items: object[]): string {
  const val = (v: unknown) => JSON.stringify(v).replace(/":/g, '": ').replace(/,"/g, ', "');
  const obj = (o: object) => {
    const lines = Object.entries(o).map(([k, v]) =>
      k === 'options' && Array.isArray(v) ? `    "options": [\n${v.map((x) => `      ${val(x)}`).join(',\n')}\n    ]` : `    ${JSON.stringify(k)}: ${val(v)}`);
    return `  {\n${lines.join(',\n')}\n  }`;
  };
  return `[\n${items.map(obj).join(',\n')}\n]\n`;
}

if (process.argv[1]?.endsWith('build-questions.ts')) {
  const { questions, groups } = buildQuestions();
  const out: [string, object[]][] = [['src/data/questions.json', questions], ['src/data/groups.json', groups]];
  let stale = false;
  for (const [f, data] of out) {
    const text = formatJson(data);
    const path = join(ROOT, f);
    if (process.argv.includes('--check')) {
      if (readFileSync(path, 'utf8') !== text) { console.error(`${f} n'est pas à jour : lancez npm run build:questions`); stale = true; }
    } else writeFileSync(path, text);
  }
  if (stale) process.exit(1);
  const n = (t: string) => questions.filter((q) => q.type === t).length;
  console.log(`${groups.length} blocs · ${n('likert')} affirmations · ${n('choice')} choix · ${n('allocation')} répartitions`);
}
