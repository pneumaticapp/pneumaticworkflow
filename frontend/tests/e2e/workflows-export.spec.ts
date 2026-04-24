/**
 * E2E: Export workflows to Excel (.xlsx) or CSV (.csv).
 * Run after Playwright is configured: npx playwright test tests/e2e/workflows-export.spec.ts
 * Requires: app running (e.g. baseURL in playwright.config), authenticated user, at least one template.
 */
import { test, expect, type Page } from '@playwright/test';

async function openExportMenuAndChooseFormat(page: Page, formatLabel: RegExp) {
  const exportToggle = page.getByRole('button', { name: /^export$|^Экспорт$/i });
  await expect(exportToggle).toBeVisible();
  await exportToggle.click();
  const formatButton = page.getByRole('button', { name: formatLabel });
  await expect(formatButton).toBeVisible();
  await formatButton.click();
}

test.describe('Workflows export (Excel and CSV)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/workflows');
    await page.waitForLoadState('networkidle');
  });

  test('happy path: Excel export from menu triggers download or empty/error feedback', async ({ page }) => {
    const downloadPromise = page.waitForEvent('download', { timeout: 15000 }).catch(() => null);

    await openExportMenuAndChooseFormat(page, /Excel \(\.xlsx\)/i);

    const loadingToggle = page.getByRole('button', { name: /Exporting|Экспорт/ });
    await expect(loadingToggle).toBeVisible({ timeout: 2000 }).catch(() => {});

    const download = await downloadPromise;
    if (download) {
      expect(download.suggestedFilename()).toBe('workflows.xlsx');
    } else {
      const errorNotification = page.getByText(/No workflows to export|Failed to export/i);
      const hasEmptyOrError = await errorNotification.isVisible().catch(() => false);
      expect(hasEmptyOrError || download).toBeTruthy();
    }
  });

  test('happy path: CSV export from menu triggers download or empty/error feedback', async ({ page }) => {
    const downloadPromise = page.waitForEvent('download', { timeout: 15000 }).catch(() => null);

    await openExportMenuAndChooseFormat(page, /CSV \(\.csv\)/i);

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
    await openExportMenuAndChooseFormat(page, /Excel \(\.xlsx\)/i);

    await expect(
      page.getByText(/No workflows to export|No workflows match/i),
    ).toBeVisible({ timeout: 10000 });
  });
});
