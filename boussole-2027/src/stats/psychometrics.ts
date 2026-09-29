/**
 * Outils de validité interne pour un pilote (spécification §10) : alpha de Cronbach, oméga de McDonald
 * (modèle à un facteur), analyse factorielle exploratoire (composantes principales + rotation varimax).
 * Les données sont importées manuellement (CSV) ; rien n'est jamais collecté par l'application.
 */
export type Matrix = number[][];

export function mean(xs: number[]): number { return xs.reduce((s, x) => s + x, 0) / xs.length; }
export function variance(xs: number[]): number { const m = mean(xs); return xs.reduce((s, x) => s + (x - m) ** 2, 0) / (xs.length - 1); }

/** Alpha de Cronbach sur des lignes complètes (répondants × items). */
export function cronbachAlpha(rows: Matrix): number {
  const k = rows[0]?.length ?? 0;
  if (k < 2 || rows.length < 3) return NaN;
  const itemVar = Array.from({ length: k }, (_, j) => variance(rows.map((r) => r[j]!)));
  const totalVar = variance(rows.map((r) => r.reduce((s, x) => s + x, 0)));
  return (k / (k - 1)) * (1 - itemVar.reduce((s, v) => s + v, 0) / totalVar);
}

/** Corrélations de Pearson par paires complètes (NaN = valeur manquante). */
export function correlationMatrix(data: Matrix): Matrix {
  const p = data[0]?.length ?? 0;
  const R: Matrix = Array.from({ length: p }, () => Array(p).fill(0));
  for (let i = 0; i < p; i++) {
    R[i]![i] = 1;
    for (let j = i + 1; j < p; j++) {
      const pairs = data.filter((r) => Number.isFinite(r[i]!) && Number.isFinite(r[j]!));
      const xi = pairs.map((r) => r[i]!), xj = pairs.map((r) => r[j]!);
      const mi = mean(xi), mj = mean(xj);
      let num = 0, di = 0, dj = 0;
      for (let k = 0; k < pairs.length; k++) { num += (xi[k]! - mi) * (xj[k]! - mj); di += (xi[k]! - mi) ** 2; dj += (xj[k]! - mj) ** 2; }
      const r = di && dj ? num / Math.sqrt(di * dj) : 0;
      R[i]![j] = r; R[j]![i] = r;
    }
  }
  return R;
}

/** Décomposition propre d'une matrice symétrique (méthode de Jacobi) ; valeurs décroissantes. */
export function eigenSymmetric(A: Matrix): { values: number[]; vectors: Matrix } {
  const n = A.length;
  const a = A.map((r) => [...r]);
  const v: Matrix = Array.from({ length: n }, (_, i) => Array.from({ length: n }, (_, j) => (i === j ? 1 : 0)));
  for (let sweep = 0; sweep < 100; sweep++) {
    let off = 0;
    for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) off += a[i]![j]! ** 2;
    if (off < 1e-12) break;
    for (let p = 0; p < n; p++)
      for (let q = p + 1; q < n; q++) {
        if (Math.abs(a[p]![q]!) < 1e-15) continue;
        const theta = (a[q]![q]! - a[p]![p]!) / (2 * a[p]![q]!);
        const t = Math.sign(theta || 1) / (Math.abs(theta) + Math.sqrt(theta * theta + 1));
        const c = 1 / Math.sqrt(t * t + 1), s = t * c;
        for (let k = 0; k < n; k++) {
          const akp = a[k]![p]!, akq = a[k]![q]!;
          a[k]![p] = c * akp - s * akq; a[k]![q] = s * akp + c * akq;
        }
        for (let k = 0; k < n; k++) {
          const apk = a[p]![k]!, aqk = a[q]![k]!;
          a[p]![k] = c * apk - s * aqk; a[q]![k] = s * apk + c * aqk;
        }
        for (let k = 0; k < n; k++) {
          const vkp = v[k]![p]!, vkq = v[k]![q]!;
          v[k]![p] = c * vkp - s * vkq; v[k]![q] = s * vkp + c * vkq;
        }
      }
  }
  const order = Array.from({ length: n }, (_, i) => i).sort((x, y) => a[y]![y]! - a[x]![x]!);
  return { values: order.map((i) => a[i]![i]!), vectors: Array.from({ length: n }, (_, r) => order.map((i) => v[r]![i]!)) };
}

/** Oméga de McDonald (un facteur) : ω = (Σλ)² / ((Σλ)² + Σ(1 − λ²)), λ = premier facteur de la matrice de corrélation. */
export function mcdonaldOmega(rows: Matrix): number {
  if ((rows[0]?.length ?? 0) < 3) return NaN;
  const { values, vectors } = eigenSymmetric(correlationMatrix(rows));
  let lambda = vectors.map((r) => r[0]! * Math.sqrt(Math.max(0, values[0]!)));
  if (lambda.reduce((s, x) => s + x, 0) < 0) lambda = lambda.map((x) => -x);
  const sl = lambda.reduce((s, x) => s + x, 0);
  const psi = lambda.reduce((s, x) => s + (1 - Math.min(1, x * x)), 0);
  return (sl * sl) / (sl * sl + psi);
}

/** Rotation varimax (Kaiser) d'une matrice de saturations p × k. */
export function varimax(L: Matrix, iters = 100): Matrix {
  const p = L.length, k = L[0]?.length ?? 0;
  const out = L.map((r) => [...r]);
  for (let it = 0; it < iters; it++) {
    let changed = false;
    for (let i = 0; i < k; i++)
      for (let j = i + 1; j < k; j++) {
        let A = 0, B = 0, C = 0, D = 0;
        for (let r = 0; r < p; r++) {
          const x = out[r]![i]!, y = out[r]![j]!;
          const u = x * x - y * y, v = 2 * x * y;
          A += u; B += v; C += u * u - v * v; D += 2 * u * v;
        }
        const phi = 0.25 * Math.atan2(D - (2 * A * B) / p, C - (A * A - B * B) / p);
        if (Math.abs(phi) < 1e-8) continue;
        changed = true;
        const c = Math.cos(phi), s = Math.sin(phi);
        for (let r = 0; r < p; r++) {
          const x = out[r]![i]!, y = out[r]![j]!;
          out[r]![i] = c * x + s * y; out[r]![j] = -s * x + c * y;
        }
      }
    if (!changed) break;
  }
  return out;
}

/** Analyse factorielle exploratoire : k facteurs (Kaiser si non précisé), saturations après varimax. */
export function exploratoryFactorAnalysis(data: Matrix, k?: number) {
  const R = correlationMatrix(data);
  const { values, vectors } = eigenSymmetric(R);
  const nf = k ?? Math.max(1, values.filter((v) => v > 1).length);
  const L = vectors.map((row) => row.slice(0, nf).map((x, j) => x * Math.sqrt(Math.max(0, values[j]!))));
  return { eigenvalues: values, factors: nf, loadings: varimax(L) };
}

export function parseCsv(text: string): { header: string[]; rows: string[][] } {
  const lines = text.split(/\r?\n/).filter((l) => l.trim());
  const sep = lines[0]!.includes(';') ? ';' : ',';
  const split = (l: string) => l.split(sep).map((c) => c.trim().replace(/^"|"$/g, ''));
  return { header: split(lines[0]!), rows: lines.slice(1).map(split) };
}
