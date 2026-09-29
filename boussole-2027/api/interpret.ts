/**
 * Fonction serverless facultative (désactivée par défaut) : commentaire d'un profil par un modèle Claude.
 *
 * - Activée seulement si ENABLE_LLM=true côté serveur (et VITE_ENABLE_LLM=true au build du client).
 * - La clé ANTHROPIC_API_KEY reste côté serveur ; elle n'est jamais exposée au navigateur.
 * - Modèle configurable par ANTHROPIC_MODEL (défaut : claude-opus-5-5).
 * - Reçoit uniquement des scores entiers par axe (schéma strict) ; ne journalise rien.
 * - En cas de refus, d'erreur ou de texte non conforme : réponse d'erreur, le client garde la synthèse locale.
 *
 * Signature Web standard (Request → Response), compatible avec les fonctions Vercel, Netlify et Cloudflare.
 */
import Anthropic from '@anthropic-ai/sdk';
import axesJson from '../src/data/axes.json';
import thinkersJson from '../src/data/thinkers.json';
import { AxisSchema, ThinkerSchema } from '../src/domain/schemas';
import { InterpretRequestSchema, buildSystemPrompt, buildUserPrompt, violatesRules } from '../src/llm/prompt';

const axes = axesJson.map((a) => AxisSchema.parse(a));
const thinkers = thinkersJson.map((t) => ThinkerSchema.parse(t));
const SYSTEM = buildSystemPrompt(thinkers);

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' } });

export default async function handler(req: Request): Promise<Response> {
  if (process.env.ENABLE_LLM !== 'true') return json(404, { error: 'désactivé' });
  if (req.method !== 'POST') return json(405, { error: 'méthode non autorisée' });
  const raw = await req.text();
  if (raw.length > 2_000) return json(413, { error: 'requête trop volumineuse' });
  let parsed;
  try {
    parsed = InterpretRequestSchema.safeParse(JSON.parse(raw));
  } catch {
    return json(400, { error: 'JSON invalide' });
  }
  if (!parsed.success) return json(400, { error: 'seuls des scores par axe sont acceptés' });

  const client = new Anthropic();
  try {
    const response = await client.beta.messages.create({
      model: process.env.ANTHROPIC_MODEL ?? 'claude-opus-5-5',
      max_tokens: 16000,
      // Tâche de rédaction courte : effort explicite (le défaut dépend du modèle).
      output_config: { effort: 'medium' },
      // En cas de refus des garde-fous du modèle, le serveur Anthropic relance sur le modèle de repli recommandé.
      betas: ['server-side-fallback-2026-07-01'],
      fallbacks: 'default',
      system: SYSTEM,
      messages: [{ role: 'user', content: buildUserPrompt(parsed.data, axes) }],
    });
    if (response.stop_reason === 'refusal') return json(502, { error: 'refus du modèle' });
    const text = response.content.flatMap((b) => (b.type === 'text' ? [b.text] : [])).join('\n').trim();
    if (!text || violatesRules(text)) return json(502, { error: 'texte non conforme' });
    return json(200, { text, model: response.model });
  } catch (error) {
    if (error instanceof Anthropic.RateLimitError) return json(503, { error: 'service saturé, réessayez plus tard' });
    if (error instanceof Anthropic.APIError) return json(502, { error: `erreur du fournisseur (${error.status ?? 'réseau'})` });
    return json(500, { error: 'erreur interne' });
  }
}
