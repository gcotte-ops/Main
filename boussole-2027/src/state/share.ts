import type { AxisId } from '../domain/schemas';

/**
 * Lien de partage facultatif : seuls les scores arrondis (jamais les réponses) sont encodés,
 * dans le fragment d'URL (#…), qui n'est pas transmis au serveur par le navigateur.
 */
const SHARE_AXES_V1: AxisId[] = ['ECO', 'IDE', 'ENV', 'REL', 'ETA', 'CUL', 'ALT', 'UE', 'GMO', 'GOV', 'SEC', 'INS', 'TER', 'POP'];
/** Version 2 : ajoute CHG. Les liens de la version 1 restent lisibles. */
export const SHARE_AXES: AxisId[] = [...SHARE_AXES_V1, 'CHG'];
const VERSION = '2';
const AXES_BY_VERSION: Record<string, AxisId[]> = { '1': SHARE_AXES_V1, '2': SHARE_AXES };

export function encodeScores(v: Partial<Record<AxisId, number>>): string {
  const parts = SHARE_AXES.map((a) => (v[a] === undefined ? '_' : String(Math.round(v[a]!))));
  return `${VERSION}.${parts.join('.')}`;
}

export function decodeScores(s: string): Partial<Record<AxisId, number>> | null {
  const [ver, ...parts] = s.split('.');
  const axes = AXES_BY_VERSION[ver ?? ''];
  if (!axes || parts.length !== axes.length) return null;
  const out: Partial<Record<AxisId, number>> = {};
  for (let i = 0; i < parts.length; i++) {
    if (parts[i] === '_') continue;
    const n = Number(parts[i]);
    if (!Number.isFinite(n) || n < -100 || n > 100) return null;
    out[axes[i]!] = n;
  }
  return out;
}
