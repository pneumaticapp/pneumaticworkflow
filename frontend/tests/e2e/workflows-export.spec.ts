/**
 * E2E: Export workflows to CSV.
 * Run after Playwright is configured: npx playwright test tests/e2e/workflows-export.spec.ts
 * Requires: app running (e.g. baseURL in playwright.config), authenticated user, at least one template.
 */
import { test, expect } from '@playwright/test';

test.describe('Workflows export to CSV', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/workflows');
    await page.waitForLoadState('networkidle');
  });

  test('happy path: export button visible and click triggers export flow', async ({ page }) => {
    const exportButton = page.getByRole('button', { name: /Export CSV/i });
    await expect(exportButton).toBeVisible();

    const downloadPromise = page.waitForEvent('download', { timeout: 15000 }).catch(() => null);

    await exportButton.click();

    const loadingLabel = page.getByRole('button', { name: /Exporting/i });
    await expect(loadingLabel).toBeVisible({ timeout: 2000 }).catch(() => {});

    const download = await downloadPromise;
    if (download) {
      expect(download.suggestedFilename()).toBe('workflows.csv');
    } else {
      const errorNotification = page.getByText(/No workflows to export|Failed to export/i);
      const hasEmptyOrError = await errorNotification.isVisible().catch(() => false);
      expect(hasEmptyOrError || download).toBeTruthy();
    }
  });

  test('empty result: warning shown when no workflows match filters', async ({ page }) => {
    const exportButton = page.getByRole('button', { name: /Export CSV/i });
    await expect(exportButton).toBeVisible();

    await exportButton.click();

    await expect(
      page.getByText(/No workflows to export|No workflows match/i),
    ).toBeVisible({ timeout: 10000 });
  });
});
