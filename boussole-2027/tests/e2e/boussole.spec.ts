import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page, type Request } from '@playwright/test';

const ORIGIN = 'http://localhost:4173';
/** 44 blocs + 15 questions à choix + 10 répartitions. */
const SCREENS = 69;

// Ordre de passage déterministe : avec cette graine, le premier écran est un bloc (B19).
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => { Math.random = () => 0.42; });
});

/** Répond à l'écran affiché (réponses variées selon i) : bloc de 4 affirmations, question à choix ou répartition. */
async function answerScreen(page: Page, i: number) {
  if (await page.locator('.allocation').count()) {
    const plus = page.getByRole('button', { name: /Ajouter un point/ });
    const n = await plus.count();
    for (let k = 0; k < 10; k++) await plus.nth((k * 3 + i) % n).click();
  } else if (await page.locator('.affirmation').count()) {
    const rows = page.locator('.affirmation');
    const n = await rows.count();
    for (let k = 0; k < n; k++) await rows.nth(k).locator('.choice').nth((i * 7 + k * 3 + 3) % 6).click();
  } else {
    const opts = page.locator('.choices .choice');
    await opts.nth((i * 5 + 1) % (await opts.count())).click();
  }
}

/** Répond à tous les écrans puis attend la page de résultats. */
async function completeQuiz(page: Page, mode: 'Rapide' | 'Apprendre' = 'Rapide') {
  // Environ 250 clics : délai du test triplé.
  test.slow();
  await page.goto('/');
  if (mode === 'Apprendre') await page.getByLabel(/Apprendre/).check();
  await page.getByRole('button', { name: 'Commencer le questionnaire' }).click();
  for (let i = 0; i < SCREENS; i++) {
    await answerScreen(page, i);
    await page.getByRole('button', { name: /Étape suivante|Voir mes résultats/ }).click();
  }
  await expect(page.getByRole('heading', { level: 1, name: 'Vos résultats' })).toBeVisible();
}

test.describe('Parcours complet', () => {
  test('69 écrans (201 réponses) puis restitution complète', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (e) => errors.push(e.message));
    await completeQuiz(page);
    for (const h of ['Vos positions', 'Carte politique', 'Les courants dont vous êtes le plus proche', 'Lecture intersectionnelle et combinaisons d\'axes',
      'Évaluation axe par axe', 'Synthèse et retour critique', 'Comparaison indicative avec les candidat·es', 'Trois lectures'])
      await expect(page.getByRole('heading', { level: 2, name: h })).toBeVisible();
    // Mentions obligatoires et date des données.
    await expect(page.getByText('Outil de réflexion, pas une consigne de vote.').first()).toBeVisible();
    await expect(page.getByText(/Programmes 2027 encore incomplets au 25 septembre 2026/).first()).toBeVisible();
    // 15 cartes d'axe (dont CHG), chacune avec auteurs proches et contradicteurs.
    const cards = page.locator('.axis-card');
    await expect(cards).toHaveCount(15);
    for (let i = 0; i < 15; i++) {
      await expect(cards.nth(i)).toContainText('Auteurs proches :');
      await expect(cards.nth(i)).not.toContainText('Contradicteurs : —');
    }
    // Chaque position de candidat·e renvoie au fichier 01.
    await page.locator('#r-candidats details').first().locator('summary').click();
    await expect(page.locator('#r-candidats details').first()).toContainText('Fichier 01 §');
    expect(errors).toEqual([]);
  });

  test('bloc : 4 affirmations, 6 réponses chacune ; on ne passe qu\'une fois les 4 répondues', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Commencer le questionnaire' }).click();
    const rows = page.locator('.affirmation');
    await expect(rows).toHaveCount(4);
    for (let k = 0; k < 4; k++) await expect(rows.nth(k).locator('.choice')).toHaveText(['Pas du tout d\'accord', 'Plutôt pas d\'accord', 'Neutre', 'Plutôt d\'accord', 'Tout à fait d\'accord', 'Je ne sais pas']);
    const next = page.getByRole('button', { name: 'Étape suivante' });
    for (let k = 0; k < 3; k++) await rows.nth(k).getByText('Neutre').click();
    await expect(next).toBeDisabled();
    await rows.nth(3).getByText('Je ne sais pas').click();
    await expect(next).toBeEnabled();
  });

  test('question à choix : options et « Aucune de ces réponses »', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Commencer le questionnaire' }).click();
    for (let i = 0; i < SCREENS && !(await page.getByText('Aucune de ces réponses / je ne sais pas').count()); i++) {
      await answerScreen(page, i);
      await page.getByRole('button', { name: 'Étape suivante' }).click();
    }
    expect(await page.locator('.choices .choice').count()).toBeGreaterThanOrEqual(5);
    await page.getByText('Aucune de ces réponses / je ne sais pas').click();
    await expect(page.getByRole('button', { name: 'Étape suivante' })).toBeEnabled();
  });

  test('mode Apprendre : explication et auteurs une fois l\'écran répondu ; retour arrière', async ({ page }) => {
    await page.goto('/');
    await page.getByLabel(/Apprendre/).check();
    await page.getByRole('button', { name: 'Commencer le questionnaire' }).click();
    await page.locator('.affirmation').first().locator('.choice').first().click();
    await expect(page.getByRole('heading', { name: 'Enjeux et arguments' })).toHaveCount(0);
    await answerScreen(page, 0);
    await expect(page.getByRole('heading', { name: 'Enjeux et arguments' })).toBeVisible();
    await expect(page.getByText('Pour aller plus loin :')).toBeVisible();
    const first = await page.locator('.question-text').first().textContent();
    await page.getByRole('button', { name: 'Étape suivante' }).click();
    await page.getByRole('button', { name: 'Étape précédente' }).click();
    await expect(page.locator('.question-text').first()).toHaveText(first!);
  });

  test('navigation au clavier', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Commencer le questionnaire' }).focus();
    await page.keyboard.press('Enter');
    await expect(page.locator('.question-text')).toBeVisible();
    await page.locator('.choices input').first().focus();
    await page.keyboard.press('ArrowDown');
    await expect(page.locator('.choices input').nth(1)).toBeChecked();
    await answerScreen(page, 0);
    await page.getByRole('button', { name: 'Étape suivante' }).focus();
    await page.keyboard.press('Enter');
    await expect(page.getByText(`Étape 2 sur ${SCREENS}`)).toBeVisible();
  });
});

test.describe('Confidentialité', () => {
  test('aucune donnée ne quitte le navigateur ; rien n\'est stocké par défaut', async ({ page, context }) => {
    const requests: Request[] = [];
    page.on('request', (r) => requests.push(r));
    await completeQuiz(page);
    await page.goto(`${ORIGIN}/#/methodologie`);
    await page.goto(`${ORIGIN}/#/confidentialite`);
    const external = requests.filter((r) => !r.url().startsWith(ORIGIN));
    expect(external.map((r) => r.url())).toEqual([]);
    const nonGet = requests.filter((r) => r.method() !== 'GET');
    expect(nonGet.map((r) => `${r.method()} ${r.url()}`)).toEqual([]);
    for (const r of requests) expect(r.postData() ?? '').toBe('');
    expect(await context.cookies()).toEqual([]);
    const stored = await page.evaluate(() => Object.keys(window.localStorage));
    expect(stored).toEqual([]);
  });

  test('la sauvegarde locale n\'a lieu qu\'avec accord, et s\'efface d\'un clic', async ({ page }) => {
    await page.goto('/');
    await page.getByLabel(/Conserver ma progression/).check();
    await page.getByRole('button', { name: 'Commencer le questionnaire' }).click();
    await page.locator('.choices .choice').first().click();
    expect(await page.evaluate(() => Object.keys(window.localStorage))).toEqual(['boussole-2027:progression']);
    await page.getByRole('button', { name: 'Tout effacer et recommencer' }).click();
    expect(await page.evaluate(() => Object.keys(window.localStorage))).toEqual([]);
  });
});

test.describe('Accessibilité (WCAG 2.2 AA, axe-core)', () => {
  const scan = async (page: Page) => {
    const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
    return r.violations.map((v) => `${v.id} (${v.nodes.length}) : ${v.help} — ${v.nodes[0]?.target.join(' ')}`);
  };
  for (const [name, path] of [['accueil', '/'], ['méthodologie', '/#/methodologie'], ['confidentialité', '/#/confidentialite']] as const) {
    test(`page ${name}`, async ({ page }) => {
      await page.goto(path);
      expect(await scan(page)).toEqual([]);
    });
  }
  test('questionnaire et résultats', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Commencer le questionnaire' }).click();
    expect(await scan(page)).toEqual([]);
    await completeQuiz(page);
    expect(await scan(page)).toEqual([]);
  });
});

test.describe('Charte graphique', () => {
  test('h1 en Fraunces 35 px, texte en Open Sans 11 pt, polices chargées localement', async ({ page }) => {
    await page.goto('/');
    await page.evaluate(() => document.fonts.ready);
    const h1 = await page.locator('h1').first().evaluate((e) => { const s = getComputedStyle(e); return { f: s.fontFamily, size: s.fontSize }; });
    expect(h1.f).toMatch(/^"?Fraunces/);
    expect(h1.size).toBe('35px');
    const p = await page.locator('.section p').first().evaluate((e) => { const s = getComputedStyle(e); return { f: s.fontFamily, size: parseFloat(s.fontSize), lh: s.lineHeight }; });
    expect(p.f).toMatch(/^"?Open Sans/);
    expect(p.size).toBeCloseTo(14.67, 1);
    expect(await page.evaluate(() => document.fonts.check('600 35px Fraunces') && document.fonts.check('400 15px "Open Sans"'))).toBe(true);
  });

  const yellowShare = async (page: Page) => {
    const png = (await page.screenshot({ fullPage: true })).toString('base64');
    return page.evaluate(async (b64) => {
      const img = new Image();
      img.src = `data:image/png;base64,${b64}`;
      await img.decode();
      const c = document.createElement('canvas');
      c.width = img.width; c.height = img.height;
      const ctx = c.getContext('2d')!;
      ctx.drawImage(img, 0, 0);
      const d = ctx.getImageData(0, 0, c.width, c.height).data;
      let y = 0;
      // Pixel « jaune » : proche de #ffc40b (tolérance) ou teinte jaune saturée (mélanges).
      for (let i = 0; i < d.length; i += 4) {
        const r = d[i]!, g = d[i + 1]!, b = d[i + 2]!;
        const max = Math.max(r, g, b), min = Math.min(r, g, b);
        const sat = max ? (max - min) / max : 0;
        const hue = max === min ? 0 : max === r ? (60 * ((g - b) / (max - min)) + 360) % 360 : max === g ? 60 * ((b - r) / (max - min)) + 120 : 60 * ((r - g) / (max - min)) + 240;
        if (sat > 0.35 && hue >= 35 && hue <= 60 && max > 150) y++;
      }
      return y / (d.length / 4);
    }, png);
  };

  test('le jaune occupe au plus 10 % de la surface (accueil, questionnaire, résultats)', async ({ page }) => {
    await page.goto('/');
    const home = await yellowShare(page);
    await page.getByRole('button', { name: 'Commencer le questionnaire' }).click();
    await page.locator('.choices .choice').first().click();
    const quiz = await yellowShare(page);
    await completeQuiz(page);
    const results = await yellowShare(page);
    console.log(`Part de jaune : accueil ${(home * 100).toFixed(2)} %, questionnaire ${(quiz * 100).toFixed(2)} %, résultats ${(results * 100).toFixed(2)} %`);
    for (const s of [home, quiz, results]) expect(s).toBeLessThanOrEqual(0.1);
  });
});
