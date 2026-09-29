import type { Axis, AxisId, Candidate, Measure, Question, Thinker } from './schemas';
import { PRIMARY_AXES, SECONDARY_AXES } from './schemas';

/**
 * Règles rédactionnelles et psychométriques des items (spécification §6).
 * Utilisé par scripts/lint-questions.ts et par les tests unitaires.
 */
export interface LintReport { errors: string[]; warnings: string[]; stats: Record<string, unknown> }

export const MAX_WORDS = 30;

/** Mots chargés : jamais employés par l'outil en son nom propre (textes de restitution, synthèse). */
export const BLACKLIST = [
  'assisté', 'assistés', 'assistanat', 'wokisme', 'woke', 'fascisme', 'fasciste', 'facho', 'ultralibéral', 'ultralibéralisme',
  'islamo-gauchiste', 'islamogauchiste', 'islamo-gauchisme', 'invasion', 'submersion', 'grand remplacement', 'remigration',
  'bien-pensance', 'bien-pensant', 'gauchiste', 'racaille', 'ensauvagement', 'parasite', 'profiteur', 'théorie du genre',
  'idéologie du genre', 'communautarisme', 'ultra-riches', 'casseurs', 'extrême', 'dictature',
];

/**
 * Vocabulaire marqué (questionnaire v2) : un énoncé peut reprendre un terme en usage dans le débat
 * (« grand remplacement », « lutte des classes »…) s'il figure dans une affirmation que le camp qui
 * l'emploie pourrait signer — contrôle humain, voir AUDIT_QUESTIONS.md — et s'il est expliqué dans le
 * texte du mode Apprendre (contrôle automatique : le terme doit y apparaître).
 */
export const MARKED_TERMS = [
  ...BLACKLIST, 'lutte des classes', 'préférence nationale', 'écologie punitive', 'mondialisme', 'mondialiste', 'patriarcat',
  'racisme systémique', 'islamophobie', 'violences policières', 'oligarchie', 'bourgeoisie', 'bien-pensants', 'impérialisme',
];

const hasTerm = (text: string, term: string) => new RegExp(`(^|[^\\p{L}])${term}([^\\p{L}]|$)`, 'u').test(text.toLowerCase());

/** Thèmes de campagne 2027 à couvrir (spécification §6.1). */
export const REQUIRED_THEMES = [
  'retraites', 'fiscalite-patrimoine', 'dette', 'services-publics', 'immigration', 'nationalite', 'laicite', 'energie-nucleaire',
  'logement-zan', 'ue', 'otan-ukraine', 'dissuasion', 'referendum-conseil-constitutionnel', 'police-libertes', 'narcotrafic',
  'fin-de-vie', 'gpa-pma', 'cannabis', 'ecole', 'decentralisation', 'ia-numerique', 'memoire-coloniale',
];

const words = (s: string) => s.replace(/[«»"()]/g, ' ').split(/\s+/).filter((w) => /[\p{L}\d]/u.test(w));

/** Constructions négatives : « ne/n' » (ne… pas/plus/jamais/ni/que compte pour une), « sans », « non », « aucun » isolé. */
export function negationCount(s: string): number {
  const t = ` ${s.toLowerCase()} `;
  // « ne » suivi d'un espace, ou « n' » élidé (« neutre », « nette »… ne comptent pas).
  const ne = (t.match(/[\s(](ne(?=\s)|n'(?=\p{L}))/gu) ?? []).length;
  const sans = (t.match(/\ssans\s/g) ?? []).length;
  const non = (t.match(/\snon\s/g) ?? []).length;
  const aucun = ne ? 0 : (t.match(/\saucun(e)?\s/g) ?? []).length;
  return ne + sans + non + aucun;
}

const OPINION_VERBS = /\b(devrait|devraient|doit|doivent|faut|faudrait|mérite|méritent)\b/g;

/** Axe de plus fort chargement (sur toutes les options pour un dilemme ou une allocation). */
export function dominantAxis(q: Question): AxisId | null {
  const acc = new Map<AxisId, number>();
  const loads = q.type === 'likert' ? [q.loadings ?? {}] : (q.options ?? []).map((o) => o.loadings);
  for (const l of loads) for (const [a, w] of Object.entries(l) as [AxisId, number][]) acc.set(a, Math.max(acc.get(a) ?? 0, Math.abs(w)));
  let best: AxisId | null = null;
  let bw = 0;
  for (const [a, w] of acc) if (w > bw) { best = a; bw = w; }
  return best;
}

/** Sens « inversé » attendu : l'accord (ou l'option B) tire vers le pôle moins de l'axe principal. */
export function expectedReversed(q: Question): boolean | null {
  if (q.type === 'likert') return (q.loadings?.[q.primaryAxis] ?? 0) < 0;
  if (q.type === 'dilemma') return (q.options?.[1]?.loadings[q.primaryAxis] ?? 0) < 0;
  return null;
}

/** Biais d'un répondant « tout d'accord » (Likert = +2) par axe, en points (−100..+100). */
export function allAgreeBias(questions: Question[]): Partial<Record<AxisId, number>> {
  const num = new Map<AxisId, number>();
  const den = new Map<AxisId, number>();
  for (const q of questions) {
    if (q.type !== 'likert') continue;
    for (const [a, w] of Object.entries(q.loadings ?? {}) as [AxisId, number][]) {
      num.set(a, (num.get(a) ?? 0) + w);
      den.set(a, (den.get(a) ?? 0) + Math.abs(w));
    }
  }
  return Object.fromEntries([...num].map(([a, n]) => [a, Math.round((100 * n) / den.get(a)!)])) as Partial<Record<AxisId, number>>;
}

export function lintQuestions(
  questions: Question[],
  ctx: { thinkers: Thinker[]; measures: Measure[]; candidates: Candidate[]; axes: Axis[] },
): LintReport {
  const errors: string[] = [];
  const warnings: string[] = [];
  const thinkers = new Map(ctx.thinkers.map((t) => [t.id, t]));
  const measures = new Set(ctx.measures.map((m) => m.id));
  const ids = new Set<string>();
  const facets = new Set(ctx.axes.flatMap((a) => a.facets?.map((f) => f.id) ?? []));
  const enabled = new Set(ctx.axes.filter((a) => a.enabled).map((a) => a.id));
  const marked: string[] = [];

  // Noms de candidat·es (nom de famille capitalisé) et de partis : interdits dans les énoncés.
  const names = new Set<string>();
  for (const c of ctx.candidates) {
    names.add(c.name);
    const last = c.name.split(' ').slice(1).join(' ');
    if (last.length >= 4) names.add(last);
  }
  for (const p of ['Rassemblement national', 'RN', 'LFI', 'France insoumise', 'Reconquête', 'Renaissance', 'Horizons', 'Républicains', 'PCF', 'Écologistes']) names.add(p);

  for (const q of questions) {
    const where = q.id;
    if (ids.has(q.id)) errors.push(`${where} : identifiant dupliqué`);
    ids.add(q.id);
    const texts = [q.text, ...(q.options?.map((o) => o.label) ?? [])];
    for (const t of texts) {
      const n = words(t).length;
      if (n > MAX_WORDS) errors.push(`${where} : ${n} mots (> ${MAX_WORDS}) « ${t.slice(0, 50)}… »`);
      if (negationCount(t) >= 2) errors.push(`${where} : double négation probable « ${t} »`);
      if (t.includes(';')) errors.push(`${where} : « ; » suggère deux idées dans un même énoncé`);
      for (const m of MARKED_TERMS) {
        if (!hasTerm(t, m)) continue;
        marked.push(`${where} : « ${m} »`);
        if (!hasTerm(q.explanation, m)) errors.push(`${where} : terme marqué « ${m} » non expliqué dans le mode Apprendre`);
      }
      for (const nm of names) if (new RegExp(`(^|[^\\p{L}])${nm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}([^\\p{L}]|$)`, 'u').test(t)) errors.push(`${where} : nom de candidat·e ou de parti « ${nm} »`);
      if ((t.match(OPINION_VERBS) ?? []).length > 1) warnings.push(`${where} : plusieurs verbes d'opinion, vérifier qu'il n'y a qu'une idée`);
    }
    // Chargements.
    const dom = dominantAxis(q);
    if (dom !== q.primaryAxis && !(q.type === 'likert' && Object.keys(q.loadings ?? {}).length === 0))
      errors.push(`${where} : primaryAxis ${q.primaryAxis} ≠ axe de plus fort chargement ${dom}`);
    const loadSets = q.type === 'likert' ? [q.loadings ?? {}] : (q.options ?? []).map((o) => o.loadings);
    for (const l of loadSets) {
      const entries = Object.entries(l) as [AxisId, number][];
      if (q.type === 'likert' && entries.length > 3) errors.push(`${where} : plus de 3 axes chargés`);
      for (const [a, w] of entries) {
        if (!enabled.has(a)) errors.push(`${where} : charge l'axe désactivé ${a}`);
        // Une option de question à choix peut combiner plusieurs axes (ex. « démocratie des conseils ») ;
        // la règle ne vise que les affirmations et les dilemmes.
        if ((q.type === 'likert' || q.type === 'dilemma') && a !== q.primaryAxis && Math.abs(w) > 0.5) errors.push(`${where} : poids secondaire ${a} = ${w} (> 0,5)`);
      }
    }
    const exp = expectedReversed(q);
    if (exp !== null && exp !== q.reversed) errors.push(`${where} : reversed=${q.reversed} incohérent avec le signe du chargement principal`);
    if (q.facet && !facets.has(q.facet)) errors.push(`${where} : facette inconnue ${q.facet}`);
    // Références.
    for (const t of q.literature) {
      if (!thinkers.has(t)) errors.push(`${where} : auteur inconnu « ${t} »`);
      else if (thinkers.get(t)!.restricted) errors.push(`${where} : auteur restreint « ${t} » cité comme éclairage`);
    }
    for (const m of q.sourceMeasure ?? []) if (!measures.has(m)) errors.push(`${where} : mesure inconnue « ${m} »`);
    for (const c of q.contradicts ?? []) if (!questions.some((x) => x.id === c)) errors.push(`${where} : item contradictoire inconnu ${c}`);
    if (q.pair) {
      const p = questions.find((x) => x.id === q.pair);
      if (!p) errors.push(`${where} : item apparié inconnu ${q.pair}`);
      else if (p.text !== q.text || p.group === q.group) errors.push(`${where} : un item apparié reprend le même énoncé dans un autre bloc`);
    }
    const sentences = q.explanation.split(/[.!?](\s|$)/).filter((s) => s.trim().length > 10).length;
    if (sentences < 2) errors.push(`${where} : explication trop courte (${sentences} phrase)`);
  }

  // Répartition.
  const per = (axis: AxisId) => questions.filter((q) => q.primaryAxis === axis);
  const quotas: Record<string, { n: number; reversed: number }> = {};
  for (const axis of [...PRIMARY_AXES, ...SECONDARY_AXES]) {
    const qs = per(axis);
    const rev = qs.filter((q) => q.type !== 'allocation' && q.reversed).length;
    quotas[axis] = { n: qs.length, reversed: rev };
    const primary = (PRIMARY_AXES as readonly string[]).includes(axis);
    const min = primary ? 8 : 5;
    const minRev = primary ? 3 : 2;
    if (qs.length < min) errors.push(`axe ${axis} : ${qs.length} items (< ${min})`);
    if (rev < minRev) errors.push(`axe ${axis} : ${rev} items inversés (< ${minRev})`);
  }
  // Formats (v2) : blocs de 4 affirmations, questions à choix, 10 répartitions.
  const byType = { likert: 0, dilemma: 0, choice: 0, allocation: 0 };
  for (const q of questions) byType[q.type]++;
  const groups = new Map<string, Question[]>();
  for (const q of questions) if (q.group) groups.set(q.group, [...(groups.get(q.group) ?? []), q]);
  for (const [g, qs] of groups) {
    if (qs.length !== 4) errors.push(`bloc ${g} : ${qs.length} affirmations (4 attendues)`);
    if (qs.some((q) => q.type !== 'likert')) errors.push(`bloc ${g} : un bloc ne contient que des affirmations`);
    if (new Set(qs.map((q) => q.block)).size > 1) errors.push(`bloc ${g} : affirmations dans des rubriques différentes`);
  }
  const ungrouped = questions.filter((q) => q.type === 'likert' && !q.group).length;
  if (ungrouped) errors.push(`${ungrouped} affirmations hors bloc`);
  if (byType.dilemma) warnings.push(`${byType.dilemma} dilemmes à deux options (remplacés par des questions à choix en v2)`);
  if (byType.likert < 150 || byType.choice < 10 || byType.allocation !== 10)
    warnings.push(`formats : ${JSON.stringify(byType)} (cible v2 ≈ 176 affirmations / 15 choix / 10 répartitions)`);
  const cross = questions.filter((q) => {
    const l = q.type === 'likert' ? [q.loadings ?? {}] : (q.options ?? []).map((o) => o.loadings);
    return new Set(l.flatMap((x) => Object.keys(x))).size >= 2;
  }).length;
  if (cross < 40) errors.push(`${cross} items à chargements croisés (< 40 %)`);
  const anchored = questions.filter((q) => q.sourceMeasure?.length).length;
  if (anchored < 50) errors.push(`${anchored} items ancrés dans une mesure du fichier 01 (< 50)`);
  const themes = new Set(questions.map((q) => q.theme));
  for (const t of REQUIRED_THEMES) if (!themes.has(t)) errors.push(`thème de campagne non couvert : ${t}`);
  if (!questions.some((q) => q.factual)) warnings.push('aucun item factuel');
  const bias = allAgreeBias(questions);
  for (const [a, b] of Object.entries(bias)) if (Math.abs(b!) > 25) errors.push(`axe ${a} : un répondant « tout d'accord » obtiendrait ${b} (> ±25)`);

  return { errors, warnings, stats: { byType, groups: groups.size, cross, anchored, quotas, allAgreeBias: bias, themes: [...themes].sort(), marked } };
}
