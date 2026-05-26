import { test, expect, Page } from '@playwright/test';
import { injectVisualCursor } from './utils/injectVisualCursor';
import { loginAsNonAdmin } from './utils/auth';
import { enMessages } from '../src/public/lang/locales/en_US';

const LABEL = {
  profile: enMessages['nav.profile'],
  settings: enMessages['nav.settings'],
  team: enMessages['nav.team'],
  integration: enMessages['nav.integration'],
  signOut: enMessages['user.sign-out'],
} as const;

const AVATAR_BUTTON = '[data-test-id="open-user-menu-button"]';

async function openProfileDropdown(page: Page) {
  await page.locator(AVATAR_BUTTON).click();
  const dropdown = page.locator('[class*="dropdown-menu_show"]');
  await expect(dropdown).toBeVisible({ timeout: 5000 });
  return dropdown;
}

async function expectDivider(page: Page, dropdownText: string, shouldExist: boolean) {
  const option = page.locator('[class*="dropdown-menu_show"]').getByText(dropdownText, { exact: true });
  await expect(option).toBeVisible();
  const container = option.locator('xpath=ancestor::div[1]');
  const divider = container.locator('hr[class*="line"]');

  if (shouldExist) {
    await expect(divider).toBeVisible();
  } else {
    await expect(divider).not.toBeVisible();
  }
}

test.describe('TopNav — User dropdown menu (PR 45016)', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/');
    await page.waitForURL('**/dashboard/**');
    await injectVisualCursor(page);
  });

  test('1.1 — Admin menu: all items visible', async ({ page }) => {
    const dropdown = await openProfileDropdown(page);

    await expect(dropdown.getByText(LABEL.profile, { exact: true })).toBeVisible();
    await expect(dropdown.getByText(LABEL.settings, { exact: true })).toBeVisible();
    await expect(dropdown.getByText(LABEL.signOut, { exact: true })).toBeVisible();

    await expect(dropdown.getByText(LABEL.team, { exact: true })).toBeVisible();
    await expect(dropdown.getByText(LABEL.integration, { exact: true })).toBeVisible();
  });

  test('1.2 — Username displayed as first item (bold, non-clickable)', async ({ page }) => {
    const dropdown = await openProfileDropdown(page);

    const userNameItem = dropdown.locator('[class*="user-name-item"]');
    await expect(userNameItem).toBeVisible();

    const nameText = await userNameItem.textContent();
    expect(nameText?.trim().length).toBeGreaterThan(0);

    const pointerEvents = await userNameItem.evaluate(
      (el) => window.getComputedStyle(el).pointerEvents,
    );
    expect(pointerEvents).toBe('none');
  });

  test('1.3 — Divider before Profile is present (when name is filled)', async ({ page }) => {
    await openProfileDropdown(page);
    await expectDivider(page, LABEL.profile, true);
  });

  test('1.4 — Divider before Team is present', async ({ page }) => {
    await openProfileDropdown(page);
    await expectDivider(page, LABEL.team, true);
  });

  test('1.5 — Divider before Sign Out is always present', async ({ page }) => {
    await openProfileDropdown(page);
    await expectDivider(page, LABEL.signOut, true);
  });

  test('1.6 — Click Team navigates to /team/', async ({ page }) => {
    const dropdown = await openProfileDropdown(page);

    await dropdown.getByText(LABEL.team, { exact: true }).click();
    await page.waitForURL('**/team/**', { timeout: 10000 });
    expect(page.url()).toContain('/team/');
  });

  test('1.7 — Click Integration navigates to /integrations/', async ({ page }) => {
    const dropdown = await openProfileDropdown(page);

    await dropdown.getByText(LABEL.integration, { exact: true }).click();
    await page.waitForURL('**/integrations/**', { timeout: 10000 });
    expect(page.url()).toContain('/integrations/');
  });

  test('1.8 — Each menu item has an icon', async ({ page }) => {
    const dropdown = await openProfileDropdown(page);

    const menuLabels = [LABEL.profile, LABEL.settings, LABEL.team, LABEL.integration, LABEL.signOut];

    for (const label of menuLabels) {
      const option = dropdown.getByText(label, { exact: true });
      await expect(option).toBeVisible();

      const itemButton = option.locator('xpath=ancestor::button[1]');
      const icon = itemButton.locator('svg[class*="dropdown-item-icon"]');
      await expect(icon).toBeVisible();
    }
  });

  test('2.1 — Non-admin menu: Team and Integration are hidden', async ({ page }) => {
    await loginAsNonAdmin(page);

    const dropdown = await openProfileDropdown(page);

    await expect(dropdown.getByText(LABEL.profile, { exact: true })).toBeVisible();
    await expect(dropdown.getByText(LABEL.settings, { exact: true })).toBeVisible();
    await expect(dropdown.getByText(LABEL.signOut, { exact: true })).toBeVisible();
    await expect(dropdown.getByText(LABEL.team, { exact: true })).not.toBeVisible();
    await expect(dropdown.getByText(LABEL.integration, { exact: true })).not.toBeVisible();
  });

  test('2.2 — Empty username: name item hidden, divider before Profile absent', async ({ page }) => {
    await loginAsNonAdmin(page);

    const dropdown = await openProfileDropdown(page);
    const userNameItem = dropdown.locator('[class*="user-name-item"]');
    await expect(userNameItem).not.toBeVisible();

    await expectDivider(page, LABEL.profile, false);
  });

  test('2.3 — Sign Out is styled in red', async ({ page }) => {
    const dropdown = await openProfileDropdown(page);

    const signOutItem = dropdown.locator('[class*="dropdown-item_red"]');
    await expect(signOutItem).toBeVisible();
    await expect(signOutItem.getByText(LABEL.signOut, { exact: true })).toBeVisible();
  });
});
