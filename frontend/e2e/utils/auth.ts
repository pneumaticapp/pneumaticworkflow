/**
 * Auth utilities for E2E tests.
 *
 * Test accounts:
 *   - Admin:     test@admin.com / qwerty     (isAdmin=true)
 *   - Non-admin: test@nonadmin.com / qwerty  (isAdmin=false, empty name)
 */

import { Page } from '@playwright/test';

interface LoginCredentials {
  email: string;
  password: string;
}

export const TEST_ACCOUNTS = {
  admin: { email: 'test@admin.com', password: 'qwerty' } as LoginCredentials,
  nonAdmin: { email: 'test@nonadmin.com', password: 'qwerty' } as LoginCredentials,
} as const;

/**
 * Sign out of current session and log in as a different account.
 * Clears cookies and localStorage, then performs UI login.
 */
export async function loginAs(page: Page, credentials: LoginCredentials) {
  // Clear current session (from auth.setup or previous test)
  await page.context().clearCookies();
  await page.goto('/auth/signin/');
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await page.waitForLoadState('domcontentloaded');

  await page.locator('[data-test-id="input-login-email"]').fill(credentials.email);
  await page.locator('[data-test-id="input-login-password"]').fill(credentials.password);
  await page.locator('[data-test-id="login-button"]').click();

  await page.waitForURL('**/dashboard/**', { timeout: 15000 });
}

/** Log in as non-admin (test@nonadmin.com). isAdmin=false, empty name. */
export async function loginAsNonAdmin(page: Page) {
  await loginAs(page, TEST_ACCOUNTS.nonAdmin);
}

/** Log in as admin (test@admin.com). isAdmin=true. */
export async function loginAsAdmin(page: Page) {
  await loginAs(page, TEST_ACCOUNTS.admin);
}
