import { Page, expect } from '@playwright/test';

export async function enableTemplateIfNeeded(page: Page): Promise<void> {
  const enableButton = page.getByRole('button', { name: /enable template/i });

  const isVisible = await enableButton.isVisible();
  if (!isVisible) return;

  await enableButton.click();

  await expect(enableButton).not.toBeVisible({ timeout: 10000 });
}
