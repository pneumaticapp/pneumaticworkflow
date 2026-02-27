import path from 'path';
import { config } from 'dotenv';
import { test, expect } from '@playwright/test';

config({ path: path.resolve(__dirname, '../../.env') });

const E2E_TEMPLATE_ID = process.env.E2E_TEMPLATE_ID;

/**
 * RichEditor E2E: runs in all configured browsers (chromium, firefox, webkit, mobile).
 * Expects a template with at least one task. Set E2E_TEMPLATE_ID in .env to open that template directly.
 */

async function focusTitleEditor(page: import('@playwright/test').Page) {
  const firstTaskBlock = page.locator('#task-form-1');
  await expect(firstTaskBlock).toBeVisible({ timeout: 15000 });
  await firstTaskBlock.locator('[class*="task_view-title"]').click();
  const editorRoot = page.locator('[data-testid="rich-editor-root"]').first();
  await expect(editorRoot).toBeVisible({ timeout: 10000 });
  const contentEditable = editorRoot.locator('[data-testid="rich-editor-contenteditable"]');
  await contentEditable.click();
  return { editorRoot, contentEditable, toolbar: page.getByRole('toolbar') };
}

async function focusDescriptionEditor(page: import('@playwright/test').Page) {
  const firstTaskBlock = page.locator('#task-form-1');
  await expect(firstTaskBlock).toBeVisible({ timeout: 15000 });
  await firstTaskBlock.locator('[class*="task_view-title"]').click();
  const editors = page.locator('[data-testid="rich-editor-root"]');
  await expect(editors.first()).toBeVisible({ timeout: 10000 });
  const descriptionRoot = editors.nth(1);
  await expect(descriptionRoot).toBeVisible({ timeout: 5000 });
  const contentEditable = descriptionRoot.locator('[data-testid="rich-editor-contenteditable"]');
  await contentEditable.click();
  const toolbar = descriptionRoot.getByRole('toolbar');
  return { editorRoot: descriptionRoot, contentEditable, toolbar };
}

test.describe('RichEditor', () => {
  test.beforeEach(async ({ page }) => {
    if (E2E_TEMPLATE_ID) {
      await page.goto(`/templates/edit/${E2E_TEMPLATE_ID}/`);
      await page.waitForLoadState('domcontentloaded');
      await expect(page.locator('#task-form-1, [data-testid="rich-editor-root"]').first()).toBeVisible({ timeout: 20000 });
    } else {
      await page.goto('/templates/');
      await page.waitForURL(/\/templates\/$/);
      const firstEditLink = page.locator('a[href*="/templates/edit/"]').first();
      await expect(firstEditLink).toBeVisible({ timeout: 20000 });
      await firstEditLink.click();
      await page.waitForURL(/\/templates\/edit\/\d+/, { timeout: 15000 });
    }
  });

  test('input: typing in the editor', async ({ page }) => {
    const { contentEditable } = await focusTitleEditor(page);
    await contentEditable.fill('E2E test text');
    await expect(contentEditable).toContainText('E2E test text');
  });

  test('formatting: bold', async ({ page }) => {
    const { contentEditable, toolbar } = await focusTitleEditor(page);
    await contentEditable.fill('Bold text');
    await contentEditable.press('Control+a');
    await toolbar.getByRole('button', { name: 'Bold' }).click();
    await expect(toolbar.getByRole('button', { name: 'Bold' })).toHaveClass(/is-active/);
  });

  test('formatting: italic', async ({ page }) => {
    const { contentEditable, toolbar } = await focusTitleEditor(page);
    await contentEditable.fill('Italic text');
    await contentEditable.press('Control+a');
    await toolbar.getByRole('button', { name: 'Italic' }).click();
    await expect(toolbar.getByRole('button', { name: 'Italic' })).toHaveClass(/is-active/);
  });

  test('formatting: toolbar reflects active state for bold/italic', async ({ page }) => {
    const { contentEditable, toolbar } = await focusTitleEditor(page);
    await contentEditable.fill('Selected');
    await contentEditable.press('Control+a');
    await toolbar.getByRole('button', { name: 'Bold' }).click();
    await expect(toolbar.getByRole('button', { name: 'Bold' })).toHaveClass(/is-active/);
    await toolbar.getByRole('button', { name: 'Italic' }).click();
    await expect(toolbar.getByRole('button', { name: 'Italic' })).toHaveClass(/is-active/);
  });

  test('link: form with selected text', async ({ page }) => {
    const { contentEditable, toolbar } = await focusTitleEditor(page);
    await contentEditable.fill('Click here');
    await contentEditable.press('Control+a');
    await toolbar.getByRole('button', { name: 'Link' }).click();
    const urlInput = page.getByPlaceholder('Paste or type link');
    await expect(urlInput).toBeVisible({ timeout: 5000 });
    await urlInput.fill('https://example.com');
    await page.getByRole('button', { name: 'Add Link' }).click();
    await expect(urlInput).not.toBeVisible({ timeout: 3000 });
    await expect(contentEditable.locator('a[href="https://example.com"]')).toBeVisible({ timeout: 3000 });
  });

  test('link: form without selection (create from scratch)', async ({ page }) => {
    const { contentEditable, toolbar } = await focusTitleEditor(page);
    await contentEditable.click();
    await toolbar.getByRole('button', { name: 'Link' }).click();
    await expect(page.getByPlaceholder('Enter text')).toBeVisible({ timeout: 5000 });
    await expect(page.getByPlaceholder('Paste or type link')).toBeVisible({ timeout: 2000 });
    await page.getByPlaceholder('Enter text').fill('Link text');
    await page.getByPlaceholder('Paste or type link').fill('https://scratch.com');
    await page.getByRole('button', { name: 'Add Link' }).click();
    await expect(contentEditable.locator('a[href="https://scratch.com"]')).toBeVisible({ timeout: 3000 });
    await expect(contentEditable).toContainText('Link text');
  });

  test('link: URL validation and tooltip', async ({ page }) => {
    const { contentEditable, toolbar } = await focusTitleEditor(page);
    await contentEditable.fill('Link');
    await contentEditable.press('Control+a');
    await toolbar.getByRole('button', { name: 'Link' }).click();
    const urlInput = page.getByPlaceholder('Paste or type link');
    await urlInput.fill('not-a-url');
    await page.getByRole('button', { name: 'Add Link' }).click();
    await expect(page.getByText('Please enter correct link')).toBeVisible({ timeout: 3000 });
    await urlInput.fill('https://tooltip.example.com');
    await page.getByRole('button', { name: 'Add Link' }).click();
    const link = contentEditable.locator('a[href="https://tooltip.example.com"]');
    await expect(link).toBeVisible({ timeout: 3000 });
    await link.hover();
    await expect(page.getByText(/tooltip\.example\.com/)).toBeVisible({ timeout: 3000 });
  });

  test('toolbar: format and list controls visible', async ({ page }) => {
    const { toolbar } = await focusTitleEditor(page);
    await expect(toolbar.getByRole('button', { name: 'Bold' })).toBeVisible();
    await expect(toolbar.getByRole('button', { name: 'Italic' })).toBeVisible();
    await expect(toolbar.getByRole('button', { name: 'Ordered List', exact: true })).toBeVisible();
    await expect(toolbar.getByRole('button', { name: 'Unordered List', exact: true })).toBeVisible();
    await expect(toolbar.getByRole('button', { name: 'Link' })).toBeVisible();
  });

  test('lists: ordered list', async ({ page }) => {
    const { contentEditable, toolbar } = await focusTitleEditor(page);
    await contentEditable.fill('Item 1');
    await toolbar.getByRole('button', { name: 'Ordered List', exact: true }).click();
    await expect(contentEditable.locator('ol')).toBeVisible({ timeout: 3000 });
  });

  test('lists: unordered list', async ({ page }) => {
    const { contentEditable, toolbar } = await focusTitleEditor(page);
    await contentEditable.fill('Bullet');
    await toolbar.getByRole('button', { name: 'Unordered List', exact: true }).click();
    await expect(contentEditable.locator('ul')).toBeVisible({ timeout: 3000 });
  });

  test('description editor: Checklist and Attach File buttons', async ({ page }) => {
    const { toolbar } = await focusDescriptionEditor(page);
    await expect(toolbar.getByRole('button', { name: 'Checklist' })).toBeVisible();
    await expect(toolbar.getByRole('button', { name: 'Attach File' })).toBeVisible();
  });

  test('checklist: insert and display', async ({ page }) => {
    const { contentEditable, toolbar } = await focusDescriptionEditor(page);
    await contentEditable.fill('Step');
    await toolbar.getByRole('button', { name: 'Checklist' }).click();
    await expect(contentEditable.locator('[data-lexical-checklist-list]')).toBeVisible({ timeout: 5000 });
    await expect(contentEditable.locator('[data-lexical-checklist-item]')).toBeVisible({ timeout: 2000 });
  });

  test('variables: open list and insert (if variables exist)', async ({ page }) => {
    await focusDescriptionEditor(page);
    const insertBtn = page.getByRole('button', { name: 'Insert' }).first();
    await insertBtn.click();
    const list = page.locator('[class*="variable-list__scrollbar"]');
    const item = list.locator('[class*="variable-list-item"]').first();
    const count = await item.count();
    if (count > 0) {
      await item.click();
      const editor = page.locator('[data-testid="rich-editor-root"]').nth(1);
      await expect(editor.locator('[data-lexical-variable]')).toBeVisible({ timeout: 3000 });
    }
  });

  test('mentions: type @ opens menu (if mentions exist)', async ({ page }) => {
    const { contentEditable } = await focusDescriptionEditor(page);
    await contentEditable.fill('@');
    const menu = page.locator('[id^="mention-option-"]').first();
    await menu.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {});
    const visible = await menu.isVisible();
    if (visible) {
      await menu.click();
      await expect(contentEditable.locator('[data-lexical-mention]')).toBeVisible({ timeout: 3000 });
    }
  });

  test('paste: paste plain text', async ({ page }) => {
    const { contentEditable } = await focusTitleEditor(page);
    await page.evaluate(() => navigator.clipboard.writeText('Pasted text'));
    await contentEditable.press('Control+v');
    await expect(contentEditable).toContainText('Pasted text');
  });

  test('copy and paste: select all, copy, paste', async ({ page }) => {
    const { contentEditable } = await focusTitleEditor(page);
    await contentEditable.fill('Copy me');
    await contentEditable.press('Control+a');
    await contentEditable.press('Control+c');
    await contentEditable.press('End');
    await contentEditable.press('Control+v');
    await expect(contentEditable).toContainText('Copy me');
  });

  test('selection: partial selection and format', async ({ page }) => {
    const { contentEditable, toolbar } = await focusTitleEditor(page);
    await contentEditable.fill('one two three');
    await contentEditable.press('Home');
    await contentEditable.press('Control+Shift+ArrowRight');
    await contentEditable.press('Control+Shift+ArrowRight');
    await contentEditable.press('Control+Shift+ArrowRight');
    await toolbar.getByRole('button', { name: 'Bold' }).click();
    await expect(toolbar.getByRole('button', { name: 'Bold' })).toHaveClass(/is-active/);
    await expect(contentEditable.locator('strong')).toContainText('one');
  });

  test('undo and redo', async ({ page }) => {
    const { contentEditable } = await focusTitleEditor(page);
    await contentEditable.fill('First');
    await contentEditable.fill('Second');
    await expect(contentEditable).toContainText('Second');
    await contentEditable.press('Control+z');
    await expect(contentEditable).toContainText('First');
    await contentEditable.press('Control+Shift+z');
    await expect(contentEditable).toContainText('Second');
  });

  test('select all and format', async ({ page }) => {
    const { contentEditable, toolbar } = await focusTitleEditor(page);
    await contentEditable.fill('Line one');
    await contentEditable.press('Enter');
    await contentEditable.type('Line two');
    await contentEditable.press('Control+a');
    await toolbar.getByRole('button', { name: 'Bold' }).click();
    await expect(contentEditable.locator('strong')).toContainText('Line one');
    await expect(contentEditable.locator('strong')).toContainText('Line two');
  });

  test('image: attach, display, delete', async ({ page }) => {
    const { editorRoot, contentEditable, toolbar } = await focusDescriptionEditor(page);
    const fileInput = editorRoot.locator('input[type="file"][accept="image/*"]');
    const minimalPng = Buffer.from(
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
      'base64',
    );
    await fileInput.setInputFiles({ name: 'dot.png', mimeType: 'image/png', buffer: minimalPng });
    await expect(contentEditable.locator('img')).toBeVisible({ timeout: 15000 });
    await page.getByRole('button', { name: 'Delete image' }).first().click();
    await expect(contentEditable.locator('img')).not.toBeVisible({ timeout: 5000 });
  });

  test('video: attach, display, delete', async ({ page }) => {
    const { editorRoot, contentEditable, toolbar } = await focusDescriptionEditor(page);
    const videoInput = editorRoot.locator('input[type="file"][accept="video/*"]');
    const minimalMp4 = Buffer.alloc(100);
    await videoInput.setInputFiles({ name: 'sample.mp4', mimeType: 'video/mp4', buffer: minimalMp4 });
    await expect(contentEditable.locator('video')).toBeVisible({ timeout: 15000 });
    await page.getByRole('button', { name: 'Delete video' }).first().click();
    await expect(contentEditable.locator('video')).not.toBeVisible({ timeout: 5000 });
  });

  test('file: attach, display, delete', async ({ page }) => {
    const { editorRoot, contentEditable } = await focusDescriptionEditor(page);
    const fileInputs = editorRoot.locator('input[type="file"]');
    const count = await fileInputs.count();
    const fileInput = count >= 3 ? fileInputs.nth(2) : fileInputs.first();
    await fileInput.setInputFiles({ name: 'doc.pdf', mimeType: 'application/pdf', buffer: Buffer.alloc(200) });
    await expect(contentEditable.locator('[class*="document-container"]')).toBeVisible({ timeout: 15000 });
    const deleteBtn = contentEditable.locator('[class*="document-container"]').getByRole('button').first();
    await deleteBtn.click();
    await expect(contentEditable.locator('[class*="document-container"]')).not.toBeVisible({ timeout: 5000 });
  });
});
