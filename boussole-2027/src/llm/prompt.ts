import { z } from 'zod';
import type { Axis, Thinker } from '../domain/schemas';
import { SHARE_AXES } from '../state/share';

/**
 * Charge utile acceptée par la fonction serverless : uniquement des scores entiers par axe.
 * Tout autre champ est rejeté (strict) : aucune réponse individuelle ne peut transiter.
 */
export const InterpretRequestSchema = z
  .object({
    scores: z
      .record(z.string(), z.number().int().min(-100).max(100))
      .refine((s) => Object.keys(s).length > 0 && Object.keys(s).every((k) => (SHARE_AXES as string[]).includes(k)), 'axes inconnus'),
  })
  .strict();
export type InterpretRequest = z.infer<typeof InterpretRequestSchema>;

/** Prompt système : neutralité, aucun jugement moral, aucune consigne de vote, auteurs de thinkers.json uniquement, contre-argument obligatoire. */
export function buildSystemPrompt(thinkers: Thinker[]): string {
  const allowed = thinkers.filter((t) => !t.restricted).map((t) => t.name).join(' ; ');
  return [
    'Tu rédiges, en français, un commentaire de 250 à 350 mots sur un profil politique issu de « Boussole 2027 », un outil de réflexion qui aide une personne à mieux connaître sa propre orientation. Ce n\'est pas un outil de recommandation électorale.',
    'Tu reçois seulement des scores de −100 à +100 sur des axes décrits par leurs deux pôles. Tu ne sais rien d\'autre de la personne : ne fais aucune supposition sur son identité, son milieu ou ses motivations.',
    'Règles impératives :',
    '1. Neutralité : décris les positions en termes que leurs défenseurs accepteraient ; aucun adjectif disqualifiant, aucun jugement moral sur la personne ni sur un courant.',
    '2. Aucune consigne de vote, aucun nom de candidat·e ni de parti, aucune prédiction électorale.',
    '3. Cite uniquement des auteurs de la liste autorisée ci-dessous, sans inventer de citation entre guillemets ni de titre d\'ouvrage.',
    '4. Présente obligatoirement au moins un contre-argument solide, issu d\'une tradition éloignée du profil, formulé dans sa version la plus forte.',
    '5. Rappelle que les scores sont approximatifs et qu\'un profil n\'est pas une étiquette.',
    '6. Termine par une question ouverte qui invite la personne à éprouver sa position la plus marquée.',
    'Écris en paragraphes séparés par une ligne vide, sans titres, sans listes ni mise en forme Markdown.',
    `Auteurs autorisés : ${allowed}.`,
  ].join('\n');
}

export function buildUserPrompt(req: InterpretRequest, axes: Axis[]): string {
  const lines = axes
    .filter((a) => req.scores[a.id] !== undefined)
    .map((a) => `- ${a.label} (${a.id}) : ${req.scores[a.id]} — pôle −100 « ${a.poleMinus} », pôle +100 « ${a.polePlus} »`);
  return `Scores du profil :\n${lines.join('\n')}\n\nRédige le commentaire.`;
}

/** Garde-fou en sortie : un texte qui enfreint les règles est remplacé par le moteur de règles côté client. */
const FORBIDDEN = /(?<!anti)raciste|xénophobe|extrémiste|fasciste|\bvotez\b|vous devriez voter|votre candidat/i;
export function violatesRules(text: string): boolean {
  return FORBIDDEN.test(text);
}
