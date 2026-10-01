import { describe, expect, it } from 'vitest';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

const ROOT = join(__dirname, '../..');
const SRC = join(ROOT, 'src');
const TOKENS = join(SRC, 'styles/tokens.css');

const PALETTE = ['#07072d', '#000f2e', '#eaf0f9', '#ffc40b', '#ffffff'];
const NAVY = [7, 7, 45];
const SKY = [234, 240, 249];

function hexToRgb(hex: string): [number, number, number] {
  let h = hex.slice(1).toLowerCase();
  if (h.length === 3) h = [...h].map((c) => c + c).join('');
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)) as [number, number, number];
}

/** Couleur autorisée : palette, gris neutre (R = G = B) ou interpolation bleu foncé → bleu clair. */
function isAllowed(hex: string): boolean {
  const h = hex.toLowerCase();
  if (PALETTE.includes(h)) return true;
  const [r, g, b] = hexToRgb(h);
  if (r === g && g === b) return true;
  for (let t = 0; t <= 1.0001; t += 0.005) {
    const mix = NAVY.map((c, i) => c + t * (SKY[i]! - c));
    if (Math.abs(mix[0]! - r) <= 2 && Math.abs(mix[1]! - g) <= 2 && Math.abs(mix[2]! - b) <= 2) return true;
  }
  return false;
}

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((f) => {
    const p = join(dir, f);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });
}

const COLOR_LITERAL = /#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b|\brgba?\(|\bhsla?\(/g;
const NAMED = /(?<![\w-])(?:color|fill|stroke|background(?:-color)?)\s*[:=]\s*['"]?(red|blue|green|yellow|orange|purple|pink|black|gray|grey|navy|gold)\b/gi;

describe('Charte graphique', () => {
  it('tokens.css ne contient que des couleurs de la palette, des gris neutres ou des nuances dérivées', () => {
    const css = readFileSync(TOKENS, 'utf8');
    const found = css.match(/#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b/g) ?? [];
    expect(found.length).toBeGreaterThan(0);
    const bad = found.filter((h) => !isAllowed(h));
    expect(bad).toEqual([]);
  });

  it('aucun autre fichier de src/ ne déclare de couleur littérale', () => {
    const offenders: string[] = [];
    for (const f of walk(SRC)) {
      if (f === TOKENS || !/\.(css|ts|tsx)$/.test(f)) continue;
      const txt = readFileSync(f, 'utf8');
      const m = [...(txt.match(COLOR_LITERAL) ?? []), ...(txt.match(NAMED) ?? [])];
      if (m.length) offenders.push(`${relative(ROOT, f)}: ${m.join(', ')}`);
    }
    expect(offenders).toEqual([]);
  });

  it('les tailles de titre et de texte respectent la charte', () => {
    const css = readFileSync(TOKENS, 'utf8');
    const rem = (name: string) => parseFloat(new RegExp(`--${name}:\\s*([\\d.]+)rem`).exec(css)![1]!);
    expect(rem('fs-h1') * 16).toBeCloseTo(35, 0);
    expect(rem('fs-body') * 16).toBeCloseTo(14.67, 1); // 11 pt
    expect(css).toMatch(/--font-title:\s*'Fraunces'/);
    expect(css).toMatch(/--font-body:\s*'Open Sans'/);
  });
});
