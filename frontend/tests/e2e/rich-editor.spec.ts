import path from 'path';
import { config } from 'dotenv';
import { test, expect } from '@playwright/test';

config({ path: path.resolve(__dirname, '../../.env') });

const E2E_TEMPLATE_ID = process.env.E2E_TEMPLATE_ID;

/**
 * RichEditor E2E: expects a template with at least one task.
 * Set E2E_TEMPLATE_ID in .env to open that template directly; otherwise uses first template from /templates/.
 */
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

  test('renders and allows typing in the editor', async ({ page }) => {
    const firstTaskBlock = page.locator('#task-form-1');
    await expect(firstTaskBlock).toBeVisible({ timeout: 15000 });
    await firstTaskBlock.locator('[class*="task_view-title"]').click();

    const editorRoot = page.locator('[data-testid="rich-editor-root"]').first();
    await expect(editorRoot).toBeVisible({ timeout: 10000 });

    const contentEditable = editorRoot.locator('[data-testid="rich-editor-contenteditable"]');
    await contentEditable.click();
    await contentEditable.fill('E2E test text');

    await expect(contentEditable).toContainText('E2E test text');
  });

  test('toolbar applies bold formatting', async ({ page }) => {
    const firstTaskBlock = page.locator('#task-form-1');
    await expect(firstTaskBlock).toBeVisible({ timeout: 15000 });
    await firstTaskBlock.locator('[class*="task_view-title"]').click();

    const editorRoot = page.locator('[data-testid="rich-editor-root"]').first();
    await expect(editorRoot).toBeVisible({ timeout: 10000 });

    const contentEditable = editorRoot.locator('[data-testid="rich-editor-contenteditable"]');
    await contentEditable.click();
    await contentEditable.fill('Bold text');
    await contentEditable.press('Control+a');

    const boldButton = page.getByRole('toolbar').getByRole('button', { name: 'Bold' });
    await boldButton.click();

    await expect(boldButton).toHaveClass(/is-active/);
  });

  test('toolbar has format and list controls', async ({ page }) => {
    const firstTaskBlock = page.locator('#task-form-1');
    await expect(firstTaskBlock).toBeVisible({ timeout: 15000 });
    await firstTaskBlock.locator('[class*="task_view-title"]').click();

    const toolbar = page.getByRole('toolbar');
    await expect(toolbar).toBeVisible({ timeout: 10000 });

    await expect(toolbar.getByRole('button', { name: 'Bold' })).toBeVisible();
    await expect(toolbar.getByRole('button', { name: 'Italic' })).toBeVisible();
    await expect(toolbar.getByRole('button', { name: 'Ordered List', exact: true })).toBeVisible();
    await expect(toolbar.getByRole('button', { name: 'Unordered List', exact: true })).toBeVisible();
    await expect(toolbar.getByRole('button', { name: 'Link' })).toBeVisible();
  });

  test('toolbar inserts ordered list', async ({ page }) => {
    const firstTaskBlock = page.locator('#task-form-1');
    await expect(firstTaskBlock).toBeVisible({ timeout: 15000 });
    await firstTaskBlock.locator('[class*="task_view-title"]').click();

    const editorRoot = page.locator('[data-testid="rich-editor-root"]').first();
    const contentEditable = editorRoot.locator('[data-testid="rich-editor-contenteditable"]');
    await contentEditable.click();
    await contentEditable.fill('Item 1');

    await page.getByRole('toolbar').getByRole('button', { name: 'Ordered List', exact: true }).click();

    await expect(contentEditable.locator('ol')).toBeVisible({ timeout: 3000 });
  });

  test('toolbar inserts unordered list', async ({ page }) => {
    const firstTaskBlock = page.locator('#task-form-1');
    await expect(firstTaskBlock).toBeVisible({ timeout: 15000 });
    await firstTaskBlock.locator('[class*="task_view-title"]').click();

    const editorRoot = page.locator('[data-testid="rich-editor-root"]').first();
    const contentEditable = editorRoot.locator('[data-testid="rich-editor-contenteditable"]');
    await contentEditable.click();
    await contentEditable.fill('Bullet');

    await page.getByRole('toolbar').getByRole('button', { name: 'Unordered List', exact: true }).click();

    await expect(contentEditable.locator('ul')).toBeVisible({ timeout: 3000 });
  });

  test('description editor has Checklist and attachment buttons', async ({ page }) => {
    const firstTaskBlock = page.locator('#task-form-1');
    await expect(firstTaskBlock).toBeVisible({ timeout: 15000 });
    await firstTaskBlock.locator('[class*="task_view-title"]').click();

    const editors = page.locator('[data-testid="rich-editor-root"]');
    await expect(editors.first()).toBeVisible({ timeout: 10000 });
    const descriptionEditor = editors.nth(1);
    await expect(descriptionEditor).toBeVisible({ timeout: 5000 });

    const toolbar = descriptionEditor.getByRole('toolbar');
    await expect(toolbar.getByRole('button', { name: 'Checklist' })).toBeVisible();
    await expect(toolbar.getByRole('button', { name: 'Attach File' })).toBeVisible();
  });

  test('link form: visibility, URL validation, submit and close', async ({ page }) => {
    const firstTaskBlock = page.locator('#task-form-1');
    await expect(firstTaskBlock).toBeVisible({ timeout: 15000 });
    await firstTaskBlock.locator('[class*="task_view-title"]').click();

    const editorRoot = page.locator('[data-testid="rich-editor-root"]').first();
    const contentEditable = editorRoot.locator('[data-testid="rich-editor-contenteditable"]');
    await contentEditable.click();
    await contentEditable.fill('Click here');
    await contentEditable.press('Control+a');

    await page.getByRole('toolbar').getByRole('button', { name: 'Link' }).click();

    const urlInput = page.getByPlaceholder('Paste or type link');
    await expect(urlInput).toBeVisible({ timeout: 5000 });

    await urlInput.fill('not-a-url');
    await page.getByRole('button', { name: 'Add Link' }).click();
    await expect(page.getByText('Please enter correct link')).toBeVisible({ timeout: 3000 });

    await urlInput.fill('https://example.com');
    await page.getByRole('button', { name: 'Add Link' }).click();

    await expect(urlInput).not.toBeVisible({ timeout: 3000 });
    await expect(contentEditable.locator('a[href="https://example.com"]')).toBeVisible({ timeout: 3000 });
  });
});
