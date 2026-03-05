import { Locator } from '@playwright/test';

export async function openFieldDropdown(fieldLocator: Locator): Promise<void> {
  await fieldLocator.hover();

  await fieldLocator.locator('button[aria-haspopup]').dispatchEvent('click');
}
