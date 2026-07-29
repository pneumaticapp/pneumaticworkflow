/**
 * E2E: Highlights custom date range filter uses a single datepicker widget.
 * Requires: app running, authenticated session (same as other e2e specs).
 */
import { test, expect } from '@playwright/test';

test.describe('Highlights date range filter', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/workflow-highlights/');
    await page.waitForLoadState('networkidle');
  });

  test('custom range is selected in one widget without Save button', async ({ page }) => {
    const customOption = page.getByLabel(/^Custom$|^Пользовательский$/i);
    await expect(customOption).toBeVisible({ timeout: 15000 });
    await customOption.click();

    const rangeInput = page.locator('.date-filter-custom input').first();
    await expect(rangeInput).toBeVisible();
    await expect(page.locator('.date-filter-custom input')).toHaveCount(1);

    await rangeInput.click();

    const calendar = page.locator('.react-datepicker');
    await expect(calendar).toBeVisible();
    await expect(page.getByRole('button', { name: /^Save$|^Сохранить$/i })).toHaveCount(0);

    const dayButtons = page.locator('.react-datepicker__day:not(.react-datepicker__day--outside-month)');
    await dayButtons.nth(8).click();
    await expect(calendar).toBeVisible();

    await dayButtons.nth(14).click();
    await expect(calendar).toBeHidden({ timeout: 5000 });

    await expect(rangeInput).not.toHaveValue('');
  });
});
