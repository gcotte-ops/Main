import { z } from 'zod';

/* ------------------------------------------------------------------ Axes */

export const PRIMARY_AXES = ['ECO', 'IDE', 'ENV', 'REL', 'ETA', 'CUL', 'ALT', 'UE', 'GMO', 'GOV'] as const;
/** CHG (mode de changement) : axe optionnel de la v1, mesuré depuis le questionnaire v2. */
export const SECONDARY_AXES = ['SEC', 'INS', 'TER', 'POP', 'CHG'] as const;
export const OPTIONAL_AXES = ['GEN', 'TEC', 'MEM'] as const;
export const ALL_AXES = [...PRIMARY_AXES, ...SECONDARY_AXES, ...OPTIONAL_AXES] as const;

export const AxisIdSchema = z.enum(ALL_AXES);
export type AxisId = z.infer<typeof AxisIdSchema>;
export type PrimaryAxisId = (typeof PRIMARY_AXES)[number];

/** Vecteur partiel de valeurs par axe. */
const axisRecord = <T extends z.ZodTypeAny>(value: T) => z.partialRecord(AxisIdSchema, value);

const Weight = z.number().min(-1).max(1);
export const LoadingsSchema = axisRecord(Weight);
export type Loadings = z.infer<typeof LoadingsSchema>;

const kebab = z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/, 'id en kebab-case attendu');

export const AxisSchema = z.object({
  id: AxisIdSchema,
  code: z.string(), // intitulé court du fichier 01 (« Économie »)
  label: z.string(),
  poleMinus: z.string(),
  polePlus: z.string(),
  description: z.string().min(40),
  levels: z.tuple([z.string(), z.string(), z.string(), z.string(), z.string()]),
  thinkers: z.object({ minus: z.array(kebab).min(1), center: z.array(kebab), plus: z.array(kebab).min(1) }),
  primary: z.boolean(),
  enabled: z.boolean(),
  facets: z.array(z.object({ id: z.string(), label: z.string(), poleMinus: z.string(), polePlus: z.string() })).optional(),
});
export type Axis = z.infer<typeof AxisSchema>;

/* ------------------------------------------------------------- Questions */

export const QuestionOptionSchema = z.object({
  label: z.string().min(2),
  loadings: LoadingsSchema,
  /** Chargements sur des facettes (« REL.laicite ») : questions à choix uniquement. */
  facets: z.record(z.string(), Weight).optional(),
});

export const QuestionSchema = z
  .object({
    /** B01a : affirmation d'un bloc ; C01 : question à choix ; A01 : répartition (Q001 / D01 : format v1). */
    id: z.string().regex(/^(Q\d{3}|D\d{2}|A\d{2}|B\d{2}[a-d]|C\d{2})$/),
    text: z.string().min(10),
    /** likert : affirmation ; dilemma : deux options et échelle bipolaire ; choice : une option parmi N ; allocation : 10 points. */
    type: z.enum(['likert', 'dilemma', 'choice', 'allocation']),
    primaryAxis: AxisIdSchema,
    /** Facette (sous-indice d'un axe, ex. « laicite » pour REL) et poids de l'accord sur cette facette. */
    facet: z.string().optional(),
    facetLoading: Weight.optional(),
    options: z.array(QuestionOptionSchema).optional(),
    loadings: LoadingsSchema.optional(),
    theme: z.string(),
    /** Rubrique thématique (ordre et libellé de progression ; « priorites » = répartitions finales). */
    block: z.string(),
    /** Bloc d'affichage (B01) : les affirmations d'un même groupe partagent un écran et un contexte. */
    group: z.string().optional(),
    /** Même énoncé posé dans un autre contexte (bloc apparié) : sert au signalement de cohérence. */
    pair: z.string().optional(),
    reversed: z.boolean(),
    sourceMeasure: z.array(z.string()).optional(),
    literature: z.array(kebab).min(1).max(3),
    explanation: z.string().min(60),
    factual: z.boolean().optional(),
    contradicts: z.array(z.string()).optional(),
    /** Pourquoi des réponses opposées à cet item et à ceux de `contradicts` peuvent néanmoins coexister. */
    coexistence: z.string().optional(),
  })
  .superRefine((q, ctx) => {
    if (q.contradicts?.length && !q.coexistence) ctx.addIssue({ code: 'custom', message: `${q.id} : contradicts sans coexistence` });
    if (q.facet && q.facetLoading === undefined) ctx.addIssue({ code: 'custom', message: `${q.id} : facette sans facetLoading` });
    if (q.type === 'likert' && !q.loadings) ctx.addIssue({ code: 'custom', message: `${q.id} : likert sans loadings` });
    if (q.type === 'dilemma' && q.options?.length !== 2)
      ctx.addIssue({ code: 'custom', message: `${q.id} : un dilemme a exactement 2 options` });
    if (q.type === 'choice' && (!q.options || q.options.length < 4))
      ctx.addIssue({ code: 'custom', message: `${q.id} : une question à choix a au moins 4 options` });
    if (q.type === 'allocation' && (!q.options || q.options.length < 3))
      ctx.addIssue({ code: 'custom', message: `${q.id} : une allocation a au moins 3 options` });
  });
export type Question = z.infer<typeof QuestionSchema>;

/** Bloc d'affirmations affiché sur un même écran. */
export const GroupSchema = z.object({
  id: z.string().regex(/^B\d{2}$/),
  title: z.string().min(3),
  context: z.string().min(10),
  /** Bloc affiché juste après un autre (même question dans un second contexte, ex. B30 après B29). */
  follows: z.string().regex(/^B\d{2}$/).optional(),
});
export type Group = z.infer<typeof GroupSchema>;

/* ------------------------------------------------------------ Candidats */

export const ConfidenceSchema = z.enum(['H', 'M', 'F']);
export type Confidence = z.infer<typeof ConfidenceSchema>;

export const CandidatePositionSchema = z.object({
  value: z.number().min(-100).max(100).nullable(),
  confidence: ConfidenceSchema,
  justification: z.string(),
  sources: z.array(z.string()),
});
export type CandidatePosition = z.infer<typeof CandidatePositionSchema>;

export const CandidateStatusSchema = z.enum(['Déclaré', 'Primaire', 'Pressenti', 'Incertain']);

export const CandidateSchema = z.object({
  id: kebab,
  name: z.string(),
  party: z.string(),
  bloc: z.string(),
  status: CandidateStatusSchema,
  statusDetail: z.string(),
  section: z.string().nullable(), // « §3.1 » du fichier 01, null si seulement cité au panorama
  alternates: z.array(z.string()).optional(),
  note: z.string().optional(),
  positions: axisRecord(CandidatePositionSchema),
  measureIds: z.array(z.string()),
  sources: z.array(z.string()),
  lastUpdated: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
});
export type Candidate = z.infer<typeof CandidateSchema>;

export const MeasureSchema = z.object({
  id: z.string(),
  candidateIds: z.array(kebab).min(1),
  section: z.string(),
  theme: z.string(),
  text: z.string(),
});
export type Measure = z.infer<typeof MeasureSchema>;

/* -------------------------------------------------------------- Penseurs */

export const ThinkerSchema = z.object({
  id: kebab,
  name: z.string(),
  dates: z.string(),
  current: z.string(),
  section: z.string(),
  summary: z.string().min(20),
  axes: z.array(AxisIdSchema),
  members: z.array(z.string()).optional(),
  aliases: z.array(z.string()).optional(),
  /** Mentions complémentaires (renvois « voir §N » du fichier 02). */
  notes: z.array(z.object({ section: z.string(), text: z.string() })).optional(),
  /** Doctrines réfutées ou auteurs condamnés pour provocation à la haine : jamais proposés comme « proches ». */
  restricted: z.boolean().optional(),
});
export type Thinker = z.infer<typeof ThinkerSchema>;

/* ------------------------------------------------------------ Archétypes */

export const ArchetypeSchema = z.object({
  id: kebab,
  name: z.string(),
  centroid: axisRecord(z.number().min(-100).max(100)),
  justification: z.string().min(40),
  description: z.string().min(80),
  lineage: z.array(kebab).min(2),
  counterpoints: z.array(kebab).min(1),
  internalTensions: z.array(z.string()).min(1),
});
export type Archetype = z.infer<typeof ArchetypeSchema>;

/* ----------------------------------------------------------------- Textes */

export const AxisLevelTextSchema = z.object({
  axis: AxisIdSchema,
  level: z.number().int().min(0).max(4),
  text: z.string(),
  near: z.array(kebab).min(1),
  opposed: z.array(kebab).min(1),
  question: z.string(),
});
export type AxisLevelText = z.infer<typeof AxisLevelTextSchema>;

export const TensionSchema = z.object({
  id: kebab,
  title: z.string(),
  /** Conditions conjonctives : axe (ou facette « REL.laicite ») comparé à un seuil. */
  when: z.array(
    z.object({ axis: z.string(), op: z.enum(['<', '>']), value: z.number().min(-100).max(100) }),
  ).min(1),
  text: z.string(),
  thinkers: z.array(kebab).min(2),
});
export type Tension = z.infer<typeof TensionSchema>;

export const MetaSchema = z.object({
  dataDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  electionRound1: z.string(),
  electionRound2: z.string(),
  version: z.string(),
});
export type Meta = z.infer<typeof MetaSchema>;

/* --------------------------------------------------------------- Réponses */

/** Likert : −2..+2 (0 = « neutre ») ; dilemme : −2 (A nettement) .. +2 (B nettement) ; null = « je ne sais pas ». */
export type LikertAnswer = { kind: 'scale'; value: -2 | -1 | 0 | 1 | 2 | null; ms?: number };
/** Question à choix : index de l'option retenue ; null = « Aucune de ces réponses / je ne sais pas ». */
export type ChoiceAnswer = { kind: 'choice'; index: number | null; ms?: number };
/** Allocation : points par option (total 10). */
export type AllocationAnswer = { kind: 'allocation'; points: number[]; ms?: number };
export type Answer = LikertAnswer | ChoiceAnswer | AllocationAnswer;
export type Answers = Record<string, Answer>;
