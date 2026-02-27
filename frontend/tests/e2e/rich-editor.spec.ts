import path from 'path';
import { config } from 'dotenv';
import { test, expect, type Page, type Locator } from '@playwright/test';

config({ path: path.resolve(__dirname, '../../.env') });

const E2E_TEMPLATE_ID = process.env.E2E_TEMPLATE_ID;

const TIMEOUT = { short: 3_000, medium: 5_000, long: 10_000, upload: 15_000, nav: 20_000 } as const;

const MOBILE_PROJECTS = ['Mobile Chrome', 'Mobile Safari'];

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

async function selectAll(locator: Locator): Promise<void> {
  await locator.click();
  await locator.evaluate((el) =>
    new Promise<void>((resolve) => {
      const sel = window.getSelection();
      if (!sel) { resolve(); return; }
      const range = document.createRange();
      range.selectNodeContents(el);
      sel.removeAllRanges();
      sel.addRange(range);
      document.dispatchEvent(new Event('selectionchange'));
      requestAnimationFrame(() => resolve());
    }),
  );
}

async function clearEditor(contentEditable: Locator): Promise<void> {
  await selectAll(contentEditable);
  await contentEditable.press('Backspace');
}

async function pasteText(locator: Locator, text: string): Promise<void> {
  await locator.evaluate((el, t) => {
    el.focus();
    const dt = new DataTransfer();
    dt.setData('text/plain', t);
    const event = new ClipboardEvent('paste', { bubbles: true, cancelable: true });
    Object.defineProperty(event, 'clipboardData', { value: dt, writable: false });
    el.dispatchEvent(event);
  }, text);
}

async function focusDescriptionEditor(page: Page) {
  const taskBlock = page.locator('#task-form-1');
  await expect(taskBlock).toBeVisible({ timeout: TIMEOUT.upload });
  await taskBlock.locator('[class*="task_view-title"]').click();

  const editors = page.locator('[data-testid="rich-editor-root"]');
  await expect(editors.first()).toBeVisible({ timeout: TIMEOUT.long });

  const root = editors.nth(1);
  await expect(root).toBeVisible({ timeout: TIMEOUT.medium });

  const contentEditable = root.locator('[data-testid="rich-editor-contenteditable"]');
  await clearEditor(contentEditable);

  const toolbar = root.getByRole('toolbar');

  return { editorRoot: root, contentEditable, toolbar };
}

function toolbarBtn(toolbar: Locator, name: string, exact = false): Locator {
  return toolbar.getByRole('button', { name, exact });
}

function isMobileProject(projectName: string | undefined): boolean {
  return MOBILE_PROJECTS.some((p) => projectName?.includes(p));
}

/* ------------------------------------------------------------------ */
/*  Tests                                                             */
/* ------------------------------------------------------------------ */

test.describe('RichEditor', () => {
  test.beforeEach(async ({ page }) => {
    if (E2E_TEMPLATE_ID) {
      await page.goto(`/templates/edit/${E2E_TEMPLATE_ID}/`);
      await page.waitForLoadState('domcontentloaded');
      await expect(
        page.locator('#task-form-1, [data-testid="rich-editor-root"]').first(),
      ).toBeVisible({ timeout: TIMEOUT.nav });
    } else {
      await page.goto('/templates/');
      await page.waitForURL(/\/templates\/$/);
      const link = page.locator('a[href*="/templates/edit/"]').first();
      await expect(link).toBeVisible({ timeout: TIMEOUT.nav });
      await link.click();
      await page.waitForURL(/\/templates\/edit\/\d+/, { timeout: TIMEOUT.upload });
    }
  });

  /* ================================================================ */
  /*  Universal tests (desktop + mobile)                              */
  /* ================================================================ */

  test('input: typing in the editor', async ({ page }) => {
    const { contentEditable } = await focusDescriptionEditor(page);
    await contentEditable.fill('E2E test text');
    await expect(contentEditable).toContainText('E2E test text');
  });

  test('paste: plain text via ClipboardEvent', async ({ page }) => {
    const { contentEditable } = await focusDescriptionEditor(page);
    await pasteText(contentEditable, 'Pasted text');
    await expect(contentEditable).toContainText('Pasted text');
  });

  test('undo and redo', async ({ page }) => {
    const { contentEditable } = await focusDescriptionEditor(page);
    const mod = process.platform === 'darwin' ? 'Meta' : 'Control';
    await contentEditable.pressSequentially('Hello', { delay: 20 });
    await expect(contentEditable).toContainText('Hello');
    await page.waitForTimeout(1500);
    await contentEditable.pressSequentially(' World', { delay: 20 });
    await expect(contentEditable).toContainText('Hello World');
    await contentEditable.press(`${mod}+z`);
    await expect(contentEditable).toContainText('Hello');
    await expect(contentEditable).not.toContainText('World');
    await contentEditable.press(`${mod}+Shift+z`);
    await expect(contentEditable).toContainText('Hello World');
  });

  test('variables: open list and insert (if variables exist)', async ({ page }) => {
    const { editorRoot } = await focusDescriptionEditor(page);
    const insertBtn = page.getByRole('button', { name: 'Insert' }).first();
    await insertBtn.click();
    const item = page.locator('[class*="variable-list__scrollbar"] [class*="variable-list-item"]').first();
    const count = await item.count();
    if (count > 0) {
      await item.click();
      await expect(editorRoot.locator('[data-lexical-variable]')).toBeVisible({ timeout: TIMEOUT.short });
    }
  });

  test('mentions: type @ opens menu (if mentions exist)', async ({ page }) => {
    const { contentEditable } = await focusDescriptionEditor(page);
    await contentEditable.pressSequentially('@', { delay: 80 });
    const menu = page.locator('[role="listbox"]').filter({ has: page.locator('[id^="mention-option-"]') });
    await menu.waitFor({ state: 'visible', timeout: TIMEOUT.medium }).catch(() => {});

    if (await menu.isVisible()) {
      const selectedName = await page.locator('[id^="mention-option-"]').first().textContent();
      await contentEditable.press('Enter');
      await expect(menu).not.toBeVisible({ timeout: TIMEOUT.short });
      await expect(
        contentEditable.locator('[contenteditable="false"]').filter({ hasText: '@' }),
      ).toBeVisible({ timeout: TIMEOUT.medium });
      if (selectedName?.trim()) {
        await expect(contentEditable).toContainText(selectedName.trim());
      }
    }
  });

  /* ---------- Attachments (mobile: only file) ---------- */

  test('file: attach, display, delete', async ({ page }) => {
    const { editorRoot, contentEditable } = await focusDescriptionEditor(page);
    const fileInputs = editorRoot.locator('input[type="file"]');
    const count = await fileInputs.count();
    const fileInput = count >= 3 ? fileInputs.nth(2) : fileInputs.first();
    await fileInput.setInputFiles({ name: 'doc.pdf', mimeType: 'application/pdf', buffer: Buffer.alloc(200) });
    const doc = contentEditable.locator('[class*="document-container"]');
    await expect(doc).toBeVisible({ timeout: TIMEOUT.upload });
    await doc.getByRole('button').first().click();
    await expect(doc).not.toBeVisible({ timeout: TIMEOUT.medium });
  });

  /* ================================================================ */
  /*  Desktop-only tests (toolbar hidden on mobile)                   */
  /* ================================================================ */

  test.describe('desktop toolbar', () => {
    test.beforeEach(async ({}, testInfo) => {
      if (isMobileProject(testInfo.project.name)) {
        test.skip();
      }
    });

    /* ---------- Formatting ---------- */

    test('formatting: bold', async ({ page }) => {
      const { contentEditable, toolbar } = await focusDescriptionEditor(page);
      await contentEditable.fill('Bold text');
      await selectAll(contentEditable);
      await toolbarBtn(toolbar, 'Bold').click();
      await expect(toolbarBtn(toolbar, 'Bold')).toHaveClass(/is-active/);
    });

    test('formatting: italic', async ({ page }) => {
      const { contentEditable, toolbar } = await focusDescriptionEditor(page);
      await contentEditable.fill('Italic text');
      await selectAll(contentEditable);
      await toolbarBtn(toolbar, 'Italic').click();
      await expect(toolbarBtn(toolbar, 'Italic')).toHaveClass(/is-active/);
    });

    test('formatting: toolbar reflects active state for bold/italic', async ({ page }) => {
      const { contentEditable, toolbar } = await focusDescriptionEditor(page);
      await contentEditable.fill('Selected');
      await selectAll(contentEditable);
      await toolbarBtn(toolbar, 'Bold').click();
      await expect(toolbarBtn(toolbar, 'Bold')).toHaveClass(/is-active/);
      await toolbarBtn(toolbar, 'Italic').click();
      await expect(toolbarBtn(toolbar, 'Italic')).toHaveClass(/is-active/);
    });

    test('select all and format multiline', async ({ page }) => {
      const { contentEditable, toolbar } = await focusDescriptionEditor(page);
      const boldBtn = toolbarBtn(toolbar, 'Bold');

      await contentEditable.pressSequentially('Line one', { delay: 20 });
      await contentEditable.press('Enter');
      await contentEditable.pressSequentially('Line two', { delay: 20 });
      await selectAll(contentEditable);
      await boldBtn.click();
      await expect(boldBtn).toHaveClass(/is-active/, { timeout: TIMEOUT.medium });
      const strongs = contentEditable.locator('strong');
      await expect(strongs).toHaveCount(2, { timeout: TIMEOUT.medium });
      await expect(strongs.nth(0)).toContainText('Line one');
      await expect(strongs.nth(1)).toContainText('Line two');
    });

    test('selection: partial selection and format', async ({ page }) => {
      const { contentEditable, toolbar } = await focusDescriptionEditor(page);
      await contentEditable.pressSequentially('one two three', { delay: 20 });
      await contentEditable.evaluate((el) =>
        new Promise<void>((resolve) => {
          const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
          const textNode = walker.nextNode();
          if (!textNode || !window.getSelection()) { resolve(); return; }
          const range = document.createRange();
          range.setStart(textNode, 0);
          range.setEnd(textNode, 3);
          const sel = window.getSelection()!;
          sel.removeAllRanges();
          sel.addRange(range);
          document.dispatchEvent(new Event('selectionchange'));
          requestAnimationFrame(() => resolve());
        }),
      );
      await toolbarBtn(toolbar, 'Bold').click();
      await expect(toolbarBtn(toolbar, 'Bold')).toHaveClass(/is-active/, { timeout: TIMEOUT.short });
      await expect(contentEditable.locator('strong').first()).toContainText('one', { timeout: TIMEOUT.medium });
    });

    test('copy and paste: select all, copy, paste', async ({ page }) => {
      const { contentEditable } = await focusDescriptionEditor(page);
      await contentEditable.fill('Copy me');
      await selectAll(contentEditable);
      await contentEditable.press('Control+c');
      await contentEditable.press('End');
      await contentEditable.press('Control+v');
      await expect(contentEditable).toContainText('Copy me');
    });

    /* ---------- Toolbar visibility ---------- */

    test('toolbar: format and list controls visible', async ({ page }) => {
      const { toolbar } = await focusDescriptionEditor(page);
      await expect(toolbarBtn(toolbar, 'Bold')).toBeVisible();
      await expect(toolbarBtn(toolbar, 'Italic')).toBeVisible();
      await expect(toolbarBtn(toolbar, 'Ordered List', true)).toBeVisible();
      await expect(toolbarBtn(toolbar, 'Unordered List', true)).toBeVisible();
      await expect(toolbarBtn(toolbar, 'Link')).toBeVisible();
    });

    test('toolbar: checklist and attach file buttons', async ({ page }) => {
      const { toolbar } = await focusDescriptionEditor(page);
      await expect(toolbarBtn(toolbar, 'Checklist')).toBeVisible();
      await expect(toolbarBtn(toolbar, 'Attach File')).toBeVisible();
    });

    /* ---------- Lists ---------- */

    test('lists: ordered list', async ({ page }) => {
      const { contentEditable, toolbar } = await focusDescriptionEditor(page);
      await contentEditable.fill('Item 1');
      await toolbarBtn(toolbar, 'Ordered List', true).click();
      await expect(contentEditable.locator('ol')).toBeVisible({ timeout: TIMEOUT.short });
    });

    test('lists: unordered list', async ({ page }) => {
      const { contentEditable, toolbar } = await focusDescriptionEditor(page);
      await contentEditable.fill('Bullet');
      await toolbarBtn(toolbar, 'Unordered List', true).click();
      await expect(contentEditable.locator('ul')).toBeVisible({ timeout: TIMEOUT.short });
    });

    /* ---------- Checklist ---------- */

    test('checklist: insert and display', async ({ page }) => {
      const { editorRoot, contentEditable, toolbar } = await focusDescriptionEditor(page);
      await contentEditable.fill('Step');
      await contentEditable.click();
      await toolbarBtn(toolbar, 'Checklist').click();
      await expect(
        editorRoot.locator('[data-lexical-checklist-list]').first(),
      ).toBeVisible({ timeout: TIMEOUT.long });
      await expect(
        editorRoot.locator('[data-lexical-checklist-item]').first(),
      ).toBeVisible({ timeout: TIMEOUT.short });
    });

    /* ---------- Links ---------- */

    test('link: form with selected text', async ({ page }) => {
      const { contentEditable, toolbar } = await focusDescriptionEditor(page);
      await contentEditable.fill('Click here');
      await selectAll(contentEditable);
      await toolbarBtn(toolbar, 'Link').click();
      const urlInput = page.getByPlaceholder('Paste or type link');
      await expect(urlInput).toBeVisible({ timeout: TIMEOUT.medium });
      await urlInput.fill('https://example.com');
      await page.getByRole('button', { name: 'Add Link' }).click();
      await expect(urlInput).not.toBeVisible({ timeout: TIMEOUT.short });
      await expect(contentEditable.locator('a[href="https://example.com"]')).toBeVisible({ timeout: TIMEOUT.short });
    });

    test('link: form without selection (create from scratch)', async ({ page }) => {
      const { contentEditable, toolbar } = await focusDescriptionEditor(page);
      await toolbarBtn(toolbar, 'Link').click();
      const textInput = page.getByPlaceholder('Enter text');
      const urlInput = page.getByPlaceholder('Paste or type link');
      await expect(textInput).toBeVisible({ timeout: TIMEOUT.medium });
      await expect(urlInput).toBeVisible({ timeout: TIMEOUT.short });
      await textInput.fill('Link text');
      await urlInput.fill('https://scratch.com');
      await page.getByRole('button', { name: 'Add Link' }).click();
      await expect(contentEditable.locator('a[href="https://scratch.com"]')).toBeVisible({ timeout: TIMEOUT.short });
      await expect(contentEditable).toContainText('Link text');
    });

    test('link: tooltip on inserted link', async ({ page }) => {
      const { contentEditable, toolbar } = await focusDescriptionEditor(page);
      await contentEditable.fill('Link');
      await selectAll(contentEditable);
      await toolbarBtn(toolbar, 'Link').click();
      const urlInput = page.getByPlaceholder('Paste or type link');
      await urlInput.fill('https://tooltip.example.com');
      await page.getByRole('button', { name: 'Add Link' }).click();
      const insertedLink = contentEditable.locator('a[href="https://tooltip.example.com"]');
      await expect(insertedLink).toBeVisible({ timeout: TIMEOUT.short });
      await insertedLink.hover();
      await expect(page.getByText(/tooltip\.example\.com/)).toBeVisible({ timeout: TIMEOUT.short });
    });

    /* ---------- Desktop attachments (image, video) ---------- */

    test('image: attach, display, delete', async ({ page }) => {
      const { editorRoot, contentEditable } = await focusDescriptionEditor(page);
      const fileInput = editorRoot.locator('input[type="file"][accept="image/*"]');
      const minimalPng = Buffer.from(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
        'base64',
      );
      await fileInput.setInputFiles({ name: 'dot.png', mimeType: 'image/png', buffer: minimalPng });
      await expect(contentEditable.locator('img')).toBeVisible({ timeout: TIMEOUT.upload });
      await page.getByRole('button', { name: 'Delete image' }).first().click();
      await expect(contentEditable.locator('img')).not.toBeVisible({ timeout: TIMEOUT.medium });
    });

    test('video: attach, display, delete', async ({ page }) => {
      const { editorRoot, contentEditable } = await focusDescriptionEditor(page);
      const videoInput = editorRoot.locator('input[type="file"][accept="video/*"]');
      await videoInput.setInputFiles({ name: 'sample.mp4', mimeType: 'video/mp4', buffer: Buffer.alloc(100) });
      await expect(contentEditable.locator('video')).toBeVisible({ timeout: TIMEOUT.upload });
      await page.getByRole('button', { name: 'Delete video' }).first().click();
      await expect(contentEditable.locator('video')).not.toBeVisible({ timeout: TIMEOUT.medium });
    });
  });
});
