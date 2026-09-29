import type { AxisId } from '../domain/schemas';

/**
 * Lien de partage facultatif : seuls les scores arrondis (jamais les réponses) sont encodés,
 * dans le fragment d'URL (#…), qui n'est pas transmis au serveur par le navigateur.
 */
export const SHARE_AXES: AxisId[] = ['ECO', 'IDE', 'ENV', 'REL', 'ETA', 'CUL', 'ALT', 'UE', 'GMO', 'GOV', 'SEC', 'INS', 'TER', 'POP'];
const VERSION = '1';

export function encodeScores(v: Partial<Record<AxisId, number>>): string {
  const parts = SHARE_AXES.map((a) => (v[a] === undefined ? '_' : String(Math.round(v[a]!))));
  return `${VERSION}.${parts.join('.')}`;
}

export function decodeScores(s: string): Partial<Record<AxisId, number>> | null {
  const [ver, ...parts] = s.split('.');
  if (ver !== VERSION || parts.length !== SHARE_AXES.length) return null;
  const out: Partial<Record<AxisId, number>> = {};
  for (let i = 0; i < parts.length; i++) {
    if (parts[i] === '_') continue;
    const n = Number(parts[i]);
    if (!Number.isFinite(n) || n < -100 || n > 100) return null;
    out[SHARE_AXES[i]!] = n;
  }
  return out;
}
