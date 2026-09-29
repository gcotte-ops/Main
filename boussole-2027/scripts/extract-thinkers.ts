/**
 * Extrait les fiches d'auteur·ices du fichier 02 vers src/data/thinkers.json.
 *
 * Règles :
 *  - une fiche = une ligne commençant par « **Nom** (dates) — résumé [AXES] » ;
 *  - une fiche groupée (« A et B ») donne une seule entrée, avec `members` ;
 *  - un renvoi « **Nom** (voir §N) » est fusionné dans la fiche principale (axes + `notes`) ;
 *  - les fiches collectives (« **Réfutations** — … ») reçoivent un identifiant explicite ;
 *  - toute ligne non analysable est signalée dans scripts/reports/extract-thinkers.md.
 *
 * Usage : npm run extract:thinkers
 */
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { ALL_AXES, ThinkerSchema, type AxisId, type Thinker } from '../src/domain/schemas';

const ROOT = join(import.meta.dirname, '..');
const SOURCE = join(ROOT, 'docs/02_penseurs_courants_politiques.md');
const OUT = join(ROOT, 'src/data/thinkers.json');
const REPORT = join(ROOT, 'scripts/reports/extract-thinkers.md');

/** Identifiants imposés (fiches collectives, noms composés, groupes lisibles). Clé = premier nom en gras. */
const ID_OVERRIDES: Record<string, string> = {
  'Critiques du néolibéralisme': 'critiques-neoliberalisme',
  'Réfutations': 'refutations-racisme-scientifique',
  'Écomodernisme': 'ecomodernisme',
  'Le déni climatique et sa sociologie': 'oreskes-conway',
  'Écologies conservatrices': 'ecologies-conservatrices',
  "Doctrine sociale de l'Église": 'doctrine-sociale-eglise',
  "Droit d'ingérence et responsabilité de protéger": 'droit-ingerence-r2p',
  'Racisme symbolique et moderne': 'racisme-symbolique',
  'Walter Lippmann': 'lippmann',
  'Derrick Bell': 'derrick-bell',
  'Theodor Adorno et al.': 'adorno',
  'Juan Linz': 'linz-levitsky-ziblatt',
  'Philippe Aghion': 'aghion-tirole-duflo',
  'Nick Land': 'accelerationnismes',
  'Hans Morgenthau': 'realistes-morgenthau-waltz-mearsheimer',
  'Stuart Hall': 'hall-spivak-bhabha',
  'Patricia Hill Collins': 'hill-collins-hooks-davis',
  'Donella et Dennis Meadows': 'meadows',
  'Charles de Gaulle': 'de-gaulle',
  'Pierre Mendès France': 'mendes-france',
  'W. E. B. Du Bois': 'du-bois',
  'Georges Vacher de Lapouge': 'vacher-de-lapouge',
  'Mao Zedong': 'mao',
  'Simone de Beauvoir': 'beauvoir',
  'Olympe de Gouges': 'olympe-de-gouges',
  'Henri de Saint-Simon': 'saint-simon-fourier',
  'Marc Andreessen': 'andreessen',
  'Hervé Le Bras': 'le-bras-heran',
};

/** Fiches jamais proposées comme auteurs « proches » d'un profil (doctrines réfutées, provocation à la haine). */
const RESTRICTED = new Set([
  'gobineau', 'vacher-de-lapouge', 'chamberlain', 'grant', 'carrel', 'camus', 'faye', 'qutb',
]);

/** Groupes dont un élément en gras n'est pas une personne. */
const NOT_A_PERSON = new Set(['colloque Lippmann', 'théorie critique de la race', 'GIEC', 'R2P']);
/** Couples dont le « et » n'est pas un séparateur de personnes. */
const KEEP_TOGETHER = new Set(['Donella et Dennis Meadows']);
const splitNames = (names: string[]) =>
  names.flatMap((n) => (KEEP_TOGETHER.has(n) ? [n] : n.split(/\s+et\s+/).map((x) => x.trim())));

const slug = (s: string) =>
  s
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/ø/g, 'o')
    .replace(/æ/g, 'ae')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');

const PARTICLES = new Set(['de', 'von', 'du', 'd', 'la', 'le']);

/** Nom de famille approximatif : dernier mot, sans particule. « Esther Duflo et Abhijit Banerjee » → duflo-banerjee. */
function surname(name: string): string {
  return name
    .split(/\s+et\s+/)
    .map((n) => {
      const words = n.replace(/\./g, ' ').split(/\s+/).filter(Boolean);
      const last = words.filter((w) => !PARTICLES.has(w.toLowerCase())).pop() ?? n;
      return slug(last);
    })
    .join('-');
}

interface Raw { line: number; section: string; sectionNum: string; head: string; body: string; axes: AxisId[] }

const md = readFileSync(SOURCE, 'utf8').split('\n');
const report: string[] = [];
const raws: Raw[] = [];
let section = '';
let sectionNum = '';

md.forEach((text, i) => {
  const h = /^## (\d+)\. (.+)$/.exec(text);
  if (h) { sectionNum = h[1]!; section = h[2]!.trim(); return; }
  if (!text.startsWith('**') || !sectionNum) return;
  const dash = text.indexOf(' — ');
  if (dash < 0) { report.push(`- l.${i + 1} : pas de séparateur « — », ignorée : \`${text.slice(0, 80)}\``); return; }
  const head = text.slice(0, dash);
  let body = text.slice(dash + 3).trim();
  const axM = /\[([A-Z, ]+)\]\s*$/.exec(body);
  const axes: AxisId[] = [];
  if (axM) {
    for (const a of axM[1]!.split(',').map((s) => s.trim())) {
      if ((ALL_AXES as readonly string[]).includes(a)) axes.push(a as AxisId);
      else report.push(`- l.${i + 1} : axe inconnu « ${a} »`);
    }
    body = body.slice(0, axM.index).trim();
  }
  raws.push({ line: i + 1, section, sectionNum, head, body, axes });
});

const byId = new Map<string, Thinker>();
const nameIndex = new Map<string, string>(); // nom affiché → id
const pendingRefs: Raw[] = [];

for (const r of raws) {
  const bolds = [...r.head.matchAll(/\*\*([^*]+)\*\*/g)].map((m) => m[1]!.trim());
  const first = bolds[0]!;
  if (/\(voir §\d+\)/.test(r.head)) { pendingRefs.push(r); continue; }

  const collective = !/\(/.test(r.head) || /^(Critiques|Réfutations|Écomodernisme|Le déni|Écologies|Doctrine|Droit d'ingérence|Racisme symbolique)/.test(first);
  const heads = bolds.filter((b) => !NOT_A_PERSON.has(b));
  const persons = splitNames(heads);
  const members = collective && ID_OVERRIDES[first] && !/\(/.test(r.head.replace(/\*\*[^*]+\*\*/g, ''))
    ? splitNames([...r.body.matchAll(/\*\*([^*]+)\*\*/g)].map((m) => m[1]!.trim())).filter((b) => !NOT_A_PERSON.has(b))
    : persons;
  const id = ID_OVERRIDES[first] ?? heads.map(surname).join('-');
  const dates = [...r.head.matchAll(/\(([^)]*)\)/g)].map((m) => m[1]!.trim()).filter((d) => /\d|s\./.test(d)).join(' ; ');
  const name = persons.join(', ').replace(/, ([^,]+)$/, persons.length > 1 ? ' et $1' : ', $1');

  if (byId.has(id)) { report.push(`- l.${r.line} : identifiant dupliqué « ${id} »`); continue; }
  if (!r.axes.length) report.push(`- l.${r.line} : aucune indication d'axes pour « ${first} »`);

  const t: Thinker = {
    id,
    name: collective && ID_OVERRIDES[first] ? first : name,
    dates: dates || 'n. c.',
    current: r.section,
    section: `§${r.sectionNum}`,
    summary: r.body,
    axes: r.axes,
    ...(members.length > 1 || (collective && members.length) ? { members } : {}),
    ...(RESTRICTED.has(id) ? { restricted: true } : {}),
  };
  byId.set(id, t);
  nameIndex.set(slug(first), id);
  for (const p of [...persons, ...members]) nameIndex.set(slug(p), id);
}

// Renvois « (voir §N) » : fusion dans la fiche principale.
for (const r of pendingRefs) {
  const first = /\*\*([^*]+)\*\*/.exec(r.head)![1]!.trim();
  const target = nameIndex.get(slug(first));
  if (!target) { report.push(`- l.${r.line} : renvoi « ${first} » sans fiche principale`); continue; }
  const t = byId.get(target)!;
  t.axes = [...new Set([...t.axes, ...r.axes])];
  t.aliases = [...new Set([...(t.aliases ?? []), `${first} (${r.section})`])];
  if (r.body) t.notes = [...(t.notes ?? []), { section: `§${r.sectionNum}`, text: r.body }];
  report.push(`- l.${r.line} : renvoi « ${first} » fusionné dans \`${target}\``);
}

const thinkers = [...byId.values()];
const invalid = thinkers.flatMap((t) => {
  const r = ThinkerSchema.safeParse(t);
  return r.success ? [] : [`- \`${t.id}\` invalide : ${r.error.issues.map((x) => x.message).join('; ')}`];
});
report.push(...invalid);

mkdirSync(join(ROOT, 'scripts/reports'), { recursive: true });
writeFileSync(OUT, JSON.stringify(thinkers, null, 2) + '\n');
writeFileSync(
  REPORT,
  `# Rapport d'extraction — penseurs (fichier 02)\n\n${thinkers.length} fiches extraites, ${pendingRefs.length} renvois, ` +
    `${thinkers.filter((t) => t.restricted).length} fiches « restreintes ».\n\n## Signalements\n\n${report.join('\n') || '_aucun_'}\n`,
);
console.log(`${thinkers.length} fiches → ${OUT}`);
console.log(report.join('\n'));
if (invalid.length) process.exit(1);
