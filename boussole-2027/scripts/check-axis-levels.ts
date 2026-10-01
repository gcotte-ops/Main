/**
 * Vérifie un fichier de textes par axe et par niveau (src/data/texts/axis-levels*.json) :
 * schéma, 5 niveaux par axe, 80–120 mots, auteurs existants et non restreints, proche ≠ contradicteur,
 * question de réflexion terminée par « ? », mots chargés interdits.
 * Usage : npx tsx scripts/check-axis-levels.ts [fichier]
 */
import { readFileSync } from 'node:fs';
import { z } from 'zod';
import thinkers from '../src/data/thinkers.json';
import { BLACKLIST } from '../src/domain/lint';
import { AxisLevelTextSchema } from '../src/domain/schemas';

export function checkAxisLevels(raw: unknown, axesExpected?: string[]): string[] {
  const errors: string[] = [];
  const r = z.array(AxisLevelTextSchema).safeParse(raw);
  if (!r.success) return r.error.issues.map((i) => `${i.path.join('.')} : ${i.message}`);
  const map = new Map(thinkers.map((t) => [t.id, t as { restricted?: boolean }]));
  const byAxis = new Map<string, number[]>();
  for (const t of r.data) {
    const where = `${t.axis}/${t.level}`;
    byAxis.set(t.axis, [...(byAxis.get(t.axis) ?? []), t.level]);
    const n = t.text.split(/\s+/).filter((w) => /[\p{L}\d]/u.test(w)).length;
    if (n < 80 || n > 120) errors.push(`${where} : ${n} mots (80–120 attendus)`);
    for (const id of [...t.near, ...t.opposed]) {
      if (!map.has(id)) errors.push(`${where} : auteur inconnu « ${id} »`);
      else if (map.get(id)!.restricted) errors.push(`${where} : auteur restreint « ${id} »`);
    }
    if (t.near.some((x) => t.opposed.includes(x))) errors.push(`${where} : même auteur proche et contradicteur`);
    if (!t.question.trim().endsWith('?')) errors.push(`${where} : la question de réflexion doit finir par « ? »`);
    const low = `${t.text} ${t.question}`.toLowerCase();
    for (const b of BLACKLIST) if (new RegExp(`(^|[^\\p{L}])${b}([^\\p{L}]|$)`, 'u').test(low)) errors.push(`${where} : mot chargé « ${b} »`);
    if (/\braciste|xénophobe|extrémiste|fanatique|réactionnaire|naïf|naïve|dangereu/i.test(low)) errors.push(`${where} : qualificatif disqualifiant`);
  }
  for (const [axis, levels] of byAxis) if ([...levels].sort().join() !== '0,1,2,3,4') errors.push(`${axis} : niveaux ${levels.join(',')} (0 à 4 attendus, une fois chacun)`);
  for (const a of axesExpected ?? []) if (!byAxis.has(a)) errors.push(`axe ${a} manquant`);
  return errors;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const file = process.argv[2] ?? 'src/data/texts/axis-levels.json';
  const errs = checkAxisLevels(JSON.parse(readFileSync(file, 'utf8')));
  console.log(errs.length ? `${errs.length} erreur(s) :\n- ${errs.join('\n- ')}` : `${file} : OK`);
  process.exit(errs.length ? 1 : 0);
}
