/**
 * Linter du questionnaire (spécification §6.2, formats v2) : longueur, double négation, vocabulaire marqué expliqué, noms de
 * candidat·es, un seul verbe d'opinion (avertissement), équilibre des items inversés, quotas par axe,
 * chargements croisés, ancrage dans le fichier 01, auteurs existants, couverture des thèmes,
 * biais d'un répondant « tout d'accord ».
 *
 * Usage : npm run lint:questions   (code de sortie 1 en cas d'erreur)
 */
import { z } from 'zod';
import axes from '../src/data/axes.json';
import candidates from '../src/data/candidates.json';
import measures from '../src/data/measures.json';
import questions from '../src/data/questions.json';
import thinkers from '../src/data/thinkers.json';
import { lintQuestions } from '../src/domain/lint';
import { AxisSchema, CandidateSchema, MeasureSchema, QuestionSchema, ThinkerSchema } from '../src/domain/schemas';

const parsed = z.array(QuestionSchema).safeParse(questions);
if (!parsed.success) {
  console.error('Schéma invalide :\n' + parsed.error.issues.map((i) => `- ${i.path.join('.')} : ${i.message}`).join('\n'));
  process.exit(1);
}
const report = lintQuestions(parsed.data, {
  axes: z.array(AxisSchema).parse(axes),
  candidates: z.array(CandidateSchema).parse(candidates),
  measures: z.array(MeasureSchema).parse(measures),
  thinkers: z.array(ThinkerSchema).parse(thinkers),
});
console.log(JSON.stringify(report.stats, null, 1));
if (report.warnings.length) console.log(`\n${report.warnings.length} avertissement(s) :\n- ${report.warnings.join('\n- ')}`);
if (report.errors.length) {
  console.error(`\n${report.errors.length} erreur(s) :\n- ${report.errors.join('\n- ')}`);
  process.exit(1);
}
console.log('\nLint des questions : OK');
