import path from 'path';
import { config } from 'dotenv';
import { test, expect } from '@playwright/test';

config({ path: path.resolve(__dirname, '../../.env') });

const E2E_TEMPLATE_ID = process.env.E2E_TEMPLATE_ID;
const TIMEOUT = { medium: 5_000, nav: 20_000 } as const;

test.describe('Template view toggle', () => {
  test.beforeEach(async ({ page }) => {
    if (E2E_TEMPLATE_ID) {
      await page.goto(`/templates/edit/${E2E_TEMPLATE_ID}/`);
      await page.waitForLoadState('domcontentloaded');
    } else {
      await page.goto('/templates/');
      await page.waitForURL(/\/templates\/$/);
      const link = page.locator('a[href*="/templates/edit/"]').first();
      await expect(link).toBeVisible({ timeout: TIMEOUT.nav });
      await link.click();
      await page.waitForURL(/\/templates\/edit\/\d+/, { timeout: TIMEOUT.nav });
    }

    await expect(page.getByTestId('template-view-toggle')).toBeVisible({ timeout: TIMEOUT.nav });
  });

  test('should switch template editor from Line to Graph and back', async ({ page }) => {
    const toggle = page.getByTestId('template-view-toggle');
    const lineButton = toggle.getByRole('button', { name: 'Line' });
    const graphButton = toggle.getByRole('button', { name: 'Graph' });

    await expect(lineButton).toBeVisible();
    await expect(page.locator('#task-form-1')).toBeVisible({ timeout: TIMEOUT.medium });

    await graphButton.click();
    await expect(page.getByTestId('template-graph-editor')).toBeVisible({ timeout: TIMEOUT.medium });
    await expect(page.getByTestId('graph-kickoff-node')).toBeVisible({ timeout: TIMEOUT.medium });
    await expect(page.locator('.react-flow__minimap')).toHaveCount(0);
    await expect(page.locator('.react-flow__controls')).toHaveCount(0);
    await expect(page.locator('#task-form-1')).toHaveCount(0);

    await lineButton.click();
    await expect(page.locator('#task-form-1')).toBeVisible({ timeout: TIMEOUT.medium });
    await expect(page.getByTestId('template-graph-editor')).toHaveCount(0);
  });

  test('should open the task editor panel over the graph and close it', async ({ page }) => {
    await page.getByTestId('template-view-toggle').getByRole('button', { name: 'Graph' }).click();
    await expect(page.getByTestId('template-graph-editor')).toBeVisible({ timeout: TIMEOUT.medium });

    await page.getByTestId('graph-node-edit').first().click();
    await expect(page.getByTestId('graph-task-editor')).toBeVisible({ timeout: TIMEOUT.medium });
    await expect(page.getByTestId('template-graph-editor')).toBeVisible();

    await page.getByTestId('graph-task-editor-close').click();
    await expect(page.getByTestId('graph-task-editor')).toHaveCount(0);
    await expect(page.getByTestId('template-graph-editor')).toBeVisible();
  });

  test('should keep Line selected when the active segment is clicked again', async ({ page }) => {
    const lineButton = page.getByTestId('template-view-toggle').getByRole('button', { name: 'Line' });

    await lineButton.click();
    await expect(page.locator('#task-form-1')).toBeVisible({ timeout: TIMEOUT.medium });
  });
});
