/**
 * ACP à deux composantes par itération de puissance avec déflation (pas de dépendance externe).
 * Les lignes sont des profils (archétypes, candidat·es), les colonnes des axes. Les données sont centrées.
 */
export interface PcaModel { mean: number[]; components: [number[], number[]]; explained: [number, number] }

function powerIteration(cov: number[][], iters = 200): { vec: number[]; val: number } {
  const n = cov.length;
  let v = Array.from({ length: n }, (_, i) => 1 / Math.sqrt(n) + i * 1e-3);
  let val = 0;
  for (let it = 0; it < iters; it++) {
    const w = cov.map((row) => row.reduce((s, x, j) => s + x * v[j]!, 0));
    const norm = Math.sqrt(w.reduce((s, x) => s + x * x, 0)) || 1;
    v = w.map((x) => x / norm);
    val = norm;
  }
  // Orientation stable : première coordonnée non nulle positive.
  const k = v.findIndex((x) => Math.abs(x) > 1e-9);
  if (k >= 0 && v[k]! < 0) v = v.map((x) => -x);
  return { vec: v, val };
}

export function fitPca(rows: number[][]): PcaModel {
  const p = rows[0]?.length ?? 0;
  const mean = Array.from({ length: p }, (_, j) => rows.reduce((s, r) => s + r[j]!, 0) / rows.length);
  const X = rows.map((r) => r.map((x, j) => x - mean[j]!));
  const cov = Array.from({ length: p }, (_, i) =>
    Array.from({ length: p }, (_, j) => X.reduce((s, r) => s + r[i]! * r[j]!, 0) / Math.max(1, rows.length - 1)),
  );
  const total = cov.reduce((s, r, i) => s + r[i]!, 0) || 1;
  const c1 = powerIteration(cov);
  const deflated = cov.map((r, i) => r.map((x, j) => x - c1.val * c1.vec[i]! * c1.vec[j]!));
  const c2 = powerIteration(deflated);
  return { mean, components: [c1.vec, c2.vec], explained: [c1.val / total, c2.val / total] };
}

export function project(model: PcaModel, row: number[]): [number, number] {
  const x = row.map((v, j) => v - model.mean[j]!);
  const dot = (c: number[]) => x.reduce((s, v, j) => s + v * c[j]!, 0);
  return [dot(model.components[0]), dot(model.components[1])];
}
