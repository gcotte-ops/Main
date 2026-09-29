/**
 * Extrait les candidatures, leurs mesures et leur codage du fichier 01
 * vers src/data/candidates.json et src/data/measures.json.
 *
 * Règles (voir docs/METHODOLOGIE.md) :
 *  - panorama (§2) → liste des candidatures, parti, statut, bloc ;
 *  - fiches (§3.x) → mesures (une par proposition, découpage sur « ; » hors parenthèses),
 *    sources, notes, tableau de codage −2..+2 converti en −100..+100 (×50) ;
 *  - confiance absente d'une cellule → « Confiance globale » de la fiche ; « M à F » → F (prudence) ;
 *    aucune indication → F, signalé ;
 *  - « n.c. » ou cellule absente → null (« non renseigné ») ; aucune valeur n'est inventée ;
 *  - toute ligne ou cellule non analysable est listée dans scripts/reports/extract-candidates.md.
 *
 * Usage : npm run extract:candidates
 */
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import {
  CandidateSchema,
  MeasureSchema,
  PRIMARY_AXES,
  type Candidate,
  type CandidatePosition,
  type Confidence,
  type Measure,
  type PrimaryAxisId,
} from '../src/domain/schemas';

const ROOT = join(import.meta.dirname, '..');
const SOURCE = join(ROOT, 'docs/01_programmes_presidentielle_2027.md');
const REPORT = join(ROOT, 'scripts/reports/extract-candidates.md');
const DATA_DATE = '2026-09-25';
const SRC_FILE = 'Fichier 01';

const md = readFileSync(SOURCE, 'utf8').split('\n');
const report: string[] = [];

const slug = (s: string) =>
  s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const clean = (s: string) => s.replace(/\*\*/g, '').replace(/\s+/g, ' ').trim();

/** Découpe sur « ; » (et « . » suivi d'une majuscule) hors parenthèses et guillemets. */
function splitMeasures(text: string): string[] {
  const out: string[] = [];
  let depth = 0;
  let cur = '';
  for (let k = 0; k < text.length; k++) {
    const ch = text[k]!;
    if (ch === '(' || ch === '«') depth++;
    if (ch === ')' || ch === '»') depth = Math.max(0, depth - 1);
    const sentenceEnd = ch === '.' && text[k + 1] === ' ' && /[A-ZÉ]/.test(text[k + 2] ?? '');
    if ((ch === ';' || sentenceEnd) && depth === 0) { out.push(cur); cur = ''; continue; }
    cur += ch;
  }
  out.push(cur);
  return out.map((s) => s.trim().replace(/\.$/, '')).filter((s) => s.length > 2);
}

/* --------------------------------------------------------------- Panorama */

type Status = Candidate['status'];
interface Entry { id: string; name: string; party: string; bloc: string; status: Status; statusDetail: string }

function statusOf(detail: string, line: number): Status {
  if (detail.includes('⚠️')) { report.push(`- l.${line} : statut marqué ⚠️ (« ${detail} ») → Incertain`); return 'Incertain'; }
  if (/^Déclaré/.test(detail)) return 'Déclaré';
  if (/^Primaire/.test(detail)) return 'Primaire';
  if (/^Pressenti/.test(detail)) return 'Pressenti';
  report.push(`- l.${line} : statut non standard (« ${detail} ») → Incertain`);
  return 'Incertain';
}

const entries = new Map<string, Entry>();
const panoStart = md.findIndex((l) => l.startsWith('## 2. Panorama'));
for (let i = panoStart + 1; i < md.length && !md[i]!.startsWith('## '); i++) {
  const l = md[i]!;
  if (!l.startsWith('|') || l.includes('---') || l.includes('Candidat·e')) continue;
  const [rawNames, rawParty, rawStatus, rawBloc] = l.split('|').slice(1, 5).map((c) => c.trim());
  if (!rawNames || !rawParty || !rawStatus || !rawBloc) { report.push(`- l.${i + 1} : ligne de panorama non analysable`); continue; }

  // « Marine Le Pen (ou Jordan Bardella) » : un seul candidat, remplaçant en alternate.
  const alt = /\(ou ([^)]+)\)/.exec(rawNames);
  const names = rawNames.replace(/\(ou [^)]+\)/, '').split(',').map((n) => n.trim());
  const parties = rawParty.split('/').map((p) => p.trim());
  names.forEach((n, k) => {
    const pressenti = /\(pressenti\)/.test(n);
    const sub = /\(([^)]+)\)/.exec(n.replace(/\(pressenti\)/, ''));
    const name = n.replace(/\([^)]*\)/g, '').trim();
    const party = sub?.[1] ?? (parties.length === names.length ? parties[k]! : rawParty);
    const detail = pressenti ? 'Pressenti' : rawStatus.replace(/^Candidats?/, 'Candidat·e');
    const status = pressenti
      ? 'Pressenti'
      : /^Candidats à une primaire désormais caduque/.test(rawStatus)
        ? 'Incertain'
        : /^Déclarés \/ pressentis/.test(rawStatus)
          ? 'Incertain'
          : statusOf(rawStatus, i + 1);
    entries.set(slug(name), { id: slug(name), name, party, bloc: rawBloc, status, statusDetail: detail });
  });
  if (alt) entries.get(slug(names[0]!.replace(/\([^)]*\)/g, '').trim()))!.statusDetail += ` — remplaçant désigné : ${alt[1]}`;
}

/* ------------------------------------------------------- Fiches §3.x */

const measures: Measure[] = [];
interface Sheet {
  section: string;
  candidateIds: string[];
  sources: string[];
  note?: string;
  globalConf?: Confidence;
  table?: { header: string[]; cells: string[]; line: number };
  measureIds: Map<string, string[]>;
}
const sheets: Sheet[] = [];

function addMeasure(sheet: Sheet, ids: string[], theme: string, text: string, prefix = ids[0]!) {
  for (const t of splitMeasures(text)) {
    const owner = prefix;
    const n = measures.filter((m) => m.id.startsWith(`${owner}-`)).length + 1;
    const id = `${owner}-${String(n).padStart(2, '0')}`;
    measures.push({ id, candidateIds: ids, section: sheet.section, theme: theme || 'Programme', text: t });
    for (const c of ids) sheet.measureIds.set(c, [...(sheet.measureIds.get(c) ?? []), id]);
  }
}

const HEADING_TO_IDS: Record<string, string[]> = {
  '3.13': ['nathalie-arthaud', 'anasse-kazib', 'selma-labib'],
};

function findId(name: string): string | undefined {
  const s = slug(name);
  if (entries.has(s)) return s;
  return [...entries.keys()].find((k) => k.endsWith(s) || s.endsWith(k));
}

let i = md.findIndex((l) => l.startsWith('## 3.'));
const end = md.findIndex((l) => l.startsWith('## 4.'));
let sheet: Sheet | null = null;
let theme = '';

const parseConf = (s: string): Confidence | undefined => {
  if (/M à F|F à M/.test(s)) return 'F';
  const m = /\b([HMF])\b/.exec(s);
  return m ? (m[1] as Confidence) : undefined;
};

for (; i < end; i++) {
  const l = md[i]!;
  const h = /^### (3\.\d+) (.+)$/.exec(l);
  if (h) {
    const sec = h[1]!;
    const title = h[2]!;
    let ids = HEADING_TO_IDS[sec];
    if (!ids) {
      const person = title.split(' — ')[0]!;
      const id = findId(person);
      ids = id ? [id] : [];
    }
    sheet = { section: `§${sec}`, candidateIds: ids, sources: [], measureIds: new Map() };
    sheets.push(sheet);
    theme = '';
    continue;
  }
  if (!sheet) continue;

  const src = /^\*Sources : (.+)\*$/.exec(l);
  if (src) { sheet.sources = src[1]!.split(/ ; /).map((s) => s.trim().replace(/\.$/, '')); continue; }
  if (/^> Note : /.test(l)) { sheet.note = clean(l.slice(9)); continue; }
  if (/^> GOV non codé/.test(l)) { sheet.note = clean(l.slice(2)); continue; }
  if (/^> Confiance globale/.test(l)) { sheet.globalConf = parseConf(l); continue; }
  if (l.startsWith('| ECO')) {
    const header = l.split('|').slice(1, -1).map((c) => c.trim());
    const cells = md[i + 2]!.split('|').slice(1, -1).map((c) => c.trim());
    const target = sheet;
    target.table = { header, cells, line: i + 3 };
    i += 2;
    continue;
  }

  // §3.7 : paragraphes par personne, socle PS rattaché aux candidat·es PS de la primaire.
  if (sheet.section === '§3.7') {
    const socle = /^\*\*Socle programmatique du PS\*\* \(([^)]+)\) : (.+)$/.exec(l);
    if (socle) {
      const psIds = ['olivier-faure', 'jerome-guedj', 'segolene-royal'];
      addMeasure(sheet, psIds, 'Socle programmatique du PS', socle[2]!, 'ps-socle');
      sheet.sources.push(`Socle PS : ${socle[1]}`);
      continue;
    }
    const person = /^\*\*([^*]+)\*\*(?: \(([^)]+)\))?(?: — (.+?))?(?: : (.+))?$/.exec(l);
    if (person) {
      const id = findId(person[1]!.trim());
      if (!id) { report.push(`- l.${i + 1} : personne inconnue « ${person[1]} »`); continue; }
      const sub: Sheet = { section: '§3.7', candidateIds: [id], sources: [], measureIds: new Map() };
      const stars = (person[3] ?? '') + ' ' + (person[4]?.match(/★+/)?.[0] ?? '');
      if (person[2]) sub.sources.push(person[2]);
      if (stars.trim()) sub.sources.push(`fiabilité ${stars.trim()}`);
      if (person[4]) addMeasure(sub, [id], 'Programme', person[4].replace(/\s*★+\.?\s*$/, ''));
      sheets.push(sub);
      sheet = sub;
      continue;
    }
    if (/^Codage Glucksmann/.test(l)) { sheet = sheets.find((s) => s.candidateIds[0] === 'raphael-glucksmann')!; continue; }
  }

  // §3.14 : puces « - **Nom** (précision) : texte ».
  if (sheet.section === '§3.14') {
    const b = /^- \*\*([^*]+)\*\*(?: \(([^)]+)\))? : (.+)$/.exec(l);
    if (!b) continue;
    const names = b[1]!.split(',').map((n) => n.trim());
    if (names.length > 1) {
      for (const n of names) {
        const id = findId(n) ?? slug(n);
        if (!entries.has(id)) {
          entries.set(id, { id, name: n, party: 'n. c.', bloc: 'n. c.', status: 'Incertain', statusDetail: `Cité au §3.14 : ${clean(b[3]!)}` });
          report.push(`- l.${i + 1} : « ${n} » absent du panorama, ajouté comme Incertain`);
        }
      }
      continue;
    }
    const id = findId(names[0]!);
    if (!id) { report.push(`- l.${i + 1} : personne inconnue « ${names[0]} »`); continue; }
    const sub: Sheet = { section: '§3.14', candidateIds: [id], sources: [], measureIds: new Map() };
    const stars = b[3]!.match(/\(([^)]*★[^)]*)\)/);
    if (stars) sub.sources.push(stars[1]!);
    if (b[2]) sub.sources.push(b[2]);
    addMeasure(sub, [id], 'Programme partiel ou positionnement', b[3]!.replace(/\s*\([^)]*★[^)]*\)/g, ''));
    sheets.push(sub);
    continue;
  }

  // Fiches standard.
  const themeOnly = /^\*\*([^*]+)\*\*\s*$/.exec(l);
  if (themeOnly) { theme = themeOnly[1]!.trim(); continue; }
  const themeInline = /^-? ?\*\*([^*]+)\*\* : (.+)$/.exec(l);
  if (themeInline) { addMeasure(sheet, sheet.candidateIds, themeInline[1]!.trim(), clean(themeInline[2]!)); continue; }
  const bullet = /^- (.+)$/.exec(l);
  if (bullet) {
    const b = clean(bullet[1]!);
    const lead = /^([A-ZÉ][\wéèêàç' /-]{2,30}) : (.+)$/.exec(b);
    if (lead) addMeasure(sheet, sheet.candidateIds, lead[1]!, lead[2]!);
    else if (theme) addMeasure(sheet, sheet.candidateIds, theme, b);
    else addMeasure(sheet, sheet.candidateIds, /^Promoteur|^Candidatures|^Internationalisme|^RP :/.test(b) ? 'Contexte' : 'Programme', b);
  }
}

/* ------------------------------------------------------------ Codage */

function parseCell(cell: string, candidateId: string, line: number, axis: string, globalConf?: Confidence) {
  const c = cell.trim();
  if (!c || /^n\.?\s?c\.?$/i.test(c)) return { value: null, confidence: 'F' as Confidence, explicit: false };
  // Cellule scindée « +1,5 (RP) / +1 (LO) ».
  if (c.includes('/')) {
    const tag: Record<string, string> = { 'anasse-kazib': 'RP', 'nathalie-arthaud': 'LO', 'selma-labib': 'NPA' };
    const part = c.split('/').map((p) => p.trim()).find((p) => p.includes(`(${tag[candidateId]})`));
    if (!part) {
      report.push(`- l.${line} : ${axis} « ${c} » ne mentionne pas ${candidateId} → null`);
      return { value: null, confidence: 'F' as Confidence, explicit: false };
    }
    return parseCell(part.replace(/\((RP|LO|NPA)\)/, ''), candidateId, line, axis, globalConf);
  }
  const m = /^([+−-]?\d+(?:,\d+)?)\s*(?:\(([HMF])\))?$/.exec(c);
  if (!m) {
    report.push(`- l.${line} : cellule ${axis} non analysable « ${c} » (${candidateId}) → null`);
    return { value: null, confidence: 'F' as Confidence, explicit: false };
  }
  const v = parseFloat(m[1]!.replace('−', '-').replace(',', '.'));
  const conf = (m[2] as Confidence | undefined) ?? globalConf;
  if (!conf) report.push(`- l.${line} : ${candidateId} ${axis} sans niveau de confiance → F`);
  return { value: Math.round(v * 50), confidence: conf ?? 'F', explicit: true };
}

const candidates: Candidate[] = [];
for (const e of entries.values()) {
  const own = sheets.filter((s) => s.candidateIds.includes(e.id));
  const coded = own.find((s) => s.table);
  const mIds = [...new Set(own.flatMap((s) => s.measureIds.get(e.id) ?? []))];
  const section = own[0]?.section ?? null;
  const sources = [
    `${SRC_FILE} ${section ?? '§2 (panorama)'} — état au 25/09/2026`,
    ...new Set(own.flatMap((s) => s.sources)),
  ];
  const note = own.map((s) => s.note).find(Boolean);
  const positions: Partial<Record<PrimaryAxisId, CandidatePosition>> = {};
  for (const axis of PRIMARY_AXES) {
    if (!coded?.table) {
      positions[axis] = { value: null, confidence: 'F', justification: 'Non codé dans le fichier 01.', sources: [sources[0]!] };
      continue;
    }
    const k = coded.table.header.indexOf(axis);
    const cell = k >= 0 ? (coded.table.cells[k] ?? '') : '';
    const p = parseCell(cell, e.id, coded.table.line, axis, coded.globalConf);
    const mentions = note && new RegExp(`\\b${axis}\\b`).test(note);
    positions[axis] = {
      value: p.value,
      confidence: p.confidence,
      justification:
        p.value === null
          ? `Non codé dans le fichier 01 (${coded.section}).`
          : `Codage indicatif du fichier 01 (${coded.section}, « ${cell} »), hypothèse de calibrage à auditer.${mentions ? ` Note de la fiche : ${note}` : ''}`,
      sources: [sources[0]!, ...coded.sources],
    };
  }
  const cand: Candidate = {
    id: e.id,
    name: e.name,
    party: e.party,
    bloc: e.bloc,
    status: e.status,
    statusDetail: e.statusDetail,
    section,
    ...(e.id === 'marine-le-pen' ? { alternates: ['Jordan Bardella'] } : {}),
    ...(note ? { note } : {}),
    positions,
    measureIds: mIds,
    sources,
    lastUpdated: DATA_DATE,
  };
  const r = CandidateSchema.safeParse(cand);
  if (!r.success) report.push(`- ${e.id} invalide : ${r.error.issues.map((x) => `${x.path.join('.')} ${x.message}`).join('; ')}`);
  candidates.push(cand);
}
for (const m of measures) if (!MeasureSchema.safeParse(m).success) report.push(`- mesure ${m.id} invalide`);
// Les fiches conteneurs §3.7 et §3.14 sont réparties par personne : elles n'ont pas de candidat propre.
for (const s of sheets) if (!s.candidateIds.length && !['§3.7', '§3.14'].includes(s.section)) report.push(`- fiche ${s.section} sans candidat reconnu`);

const codedCount = (c: Candidate) => Object.values(c.positions).filter((p) => p?.value !== null).length;
const summary = candidates
  .map((c) => `| ${c.name} | ${c.status} | ${c.section ?? '—'} | ${codedCount(c)}/10 | ${c.measureIds.length} |`)
  .join('\n');

mkdirSync(join(ROOT, 'scripts/reports'), { recursive: true });
writeFileSync(join(ROOT, 'src/data/candidates.json'), JSON.stringify(candidates, null, 2) + '\n');
writeFileSync(join(ROOT, 'src/data/measures.json'), JSON.stringify(measures, null, 2) + '\n');
writeFileSync(
  REPORT,
  `# Rapport d'extraction — candidat·es (fichier 01)\n\n${candidates.length} candidatures, ${measures.length} mesures, ` +
    `${candidates.filter((c) => codedCount(c) > 0).length} candidatures codées.\n\n` +
    `| Candidat·e | Statut | Fiche | Axes codés | Mesures |\n|---|---|---|---|---|\n${summary}\n\n## Signalements\n\n${report.join('\n') || '_aucun_'}\n`,
);
console.log(`${candidates.length} candidatures, ${measures.length} mesures`);
console.log(report.join('\n'));
