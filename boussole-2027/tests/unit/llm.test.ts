import { describe, expect, it } from 'vitest';
import axes from '../../src/data/axes.json';
import thinkers from '../../src/data/thinkers.json';
import { InterpretRequestSchema, buildSystemPrompt, buildUserPrompt, violatesRules } from '../../src/llm/prompt';
import type { Axis, Thinker } from '../../src/domain/schemas';

describe('Option LLM : charge utile et prompt', () => {
  it('n\'accepte que des scores entiers par axe connu, rien d\'autre', () => {
    expect(InterpretRequestSchema.safeParse({ scores: { ECO: 40, ALT: -12 } }).success).toBe(true);
    expect(InterpretRequestSchema.safeParse({ scores: { ECO: 40 }, answers: { Q001: 2 } }).success).toBe(false);
    expect(InterpretRequestSchema.safeParse({ scores: { Q001: 2 } }).success).toBe(false);
    expect(InterpretRequestSchema.safeParse({ scores: { ECO: 40.5 } }).success).toBe(false);
    expect(InterpretRequestSchema.safeParse({ scores: {} }).success).toBe(false);
  });
  it('le prompt système impose neutralité, absence de consigne de vote, auteurs autorisés et contre-argument', () => {
    const s = buildSystemPrompt(thinkers as Thinker[]);
    expect(s).toMatch(/Neutralité/);
    expect(s).toMatch(/Aucune consigne de vote/);
    expect(s).toMatch(/contre-argument/);
    expect(s).toMatch(/Hannah Arendt/);
    expect(s).not.toMatch(/Gobineau/); // fiches restreintes exclues
  });
  it('le message utilisateur ne contient que les scores et les pôles', () => {
    const u = buildUserPrompt({ scores: { ECO: 40 } }, axes as Axis[]);
    expect(u).toContain('Économie (ECO) : 40');
    expect(u).not.toContain('ALT');
  });
  it('garde-fou de sortie', () => {
    expect(violatesRules('Votez pour X.')).toBe(true);
    expect(violatesRules('Une tradition antiraciste, dans la lignée de Fanon…')).toBe(false);
  });
});
