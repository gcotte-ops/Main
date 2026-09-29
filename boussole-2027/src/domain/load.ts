import { z } from 'zod';
import {
  ArchetypeSchema,
  AxisLevelTextSchema,
  AxisSchema,
  CandidateSchema,
  MeasureSchema,
  MetaSchema,
  QuestionSchema,
  TensionSchema,
  ThinkerSchema,
} from './schemas';
import axesJson from '../data/axes.json';
import questionsJson from '../data/questions.json';
import candidatesJson from '../data/candidates.json';
import measuresJson from '../data/measures.json';
import thinkersJson from '../data/thinkers.json';
import archetypesJson from '../data/archetypes.json';
import axisLevelsJson from '../data/texts/axis-levels.json';
import tensionsJson from '../data/texts/tensions.json';
import metaJson from '../data/meta.json';

export const DatasetSchema = z.object({
  axes: z.array(AxisSchema),
  questions: z.array(QuestionSchema),
  candidates: z.array(CandidateSchema),
  measures: z.array(MeasureSchema),
  thinkers: z.array(ThinkerSchema),
  archetypes: z.array(ArchetypeSchema),
  axisLevels: z.array(AxisLevelTextSchema),
  tensions: z.array(TensionSchema),
  meta: MetaSchema,
});
export type Dataset = z.infer<typeof DatasetSchema>;

/** Vérifications croisées que Zod ne peut exprimer (références entre fichiers). */
export function crossCheck(d: Dataset): string[] {
  const errors: string[] = [];
  const thinkerIds = new Set(d.thinkers.map((t) => t.id));
  const measureIds = new Set(d.measures.map((m) => m.id));
  const questionIds = new Set(d.questions.map((q) => q.id));
  const refThinker = (where: string, id: string) => {
    if (!thinkerIds.has(id)) errors.push(`${where} : auteur inconnu « ${id} »`);
  };
  for (const a of d.axes) [...a.thinkers.minus, ...a.thinkers.center, ...a.thinkers.plus].forEach((t) => refThinker(`axe ${a.id}`, t));
  for (const q of d.questions) {
    q.literature.forEach((t) => refThinker(q.id, t));
    q.sourceMeasure?.forEach((m) => { if (!measureIds.has(m)) errors.push(`${q.id} : mesure inconnue « ${m} »`); });
    q.contradicts?.forEach((c) => { if (!questionIds.has(c)) errors.push(`${q.id} : item contradictoire inconnu « ${c} »`); });
  }
  for (const a of d.archetypes) [...a.lineage, ...a.counterpoints].forEach((t) => refThinker(`archétype ${a.id}`, t));
  for (const t of d.axisLevels) [...t.near, ...t.opposed].forEach((x) => refThinker(`texte ${t.axis}/${t.level}`, x));
  for (const t of d.tensions) t.thinkers.forEach((x) => refThinker(`tension ${t.id}`, x));
  for (const c of d.candidates) c.measureIds.forEach((m) => { if (!measureIds.has(m)) errors.push(`${c.id} : mesure inconnue « ${m} »`); });
  if (new Set(d.questions.map((q) => q.id)).size !== d.questions.length) errors.push('identifiants de questions dupliqués');
  return errors;
}

export function parseDataset(raw: unknown): Dataset {
  const d = DatasetSchema.parse(raw);
  const errors = crossCheck(d);
  if (errors.length) throw new Error(`Données incohérentes :\n- ${errors.join('\n- ')}`);
  return d;
}

let cached: Dataset | null = null;

/** Charge et valide toutes les données embarquées (appelé une fois au démarrage). */
export function loadDataset(): Dataset {
  cached ??= parseDataset({
    axes: axesJson,
    questions: questionsJson,
    candidates: candidatesJson,
    measures: measuresJson,
    thinkers: thinkersJson,
    archetypes: archetypesJson,
    axisLevels: axisLevelsJson,
    tensions: tensionsJson,
    meta: metaJson,
  });
  return cached;
}
