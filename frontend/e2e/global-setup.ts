import { chromium, FullConfig } from '@playwright/test';

const ADMIN_EMAIL = 'test@admin.com';
const ADMIN_PASSWORD = 'qwerty';
const AUTH_FILE = 'e2e/.auth/user.json';

async function globalSetup(config: FullConfig) {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.goto(`${config.projects[0].use.baseURL}/auth/signin/`);
  await page.waitForLoadState('domcontentloaded');
  await page.locator('[data-test-id="input-login-email"]').fill(ADMIN_EMAIL);
  await page.locator('[data-test-id="input-login-password"]').fill(ADMIN_PASSWORD);
  await page.locator('[data-test-id="login-button"]').click();
  await page.waitForURL('**/dashboard/**');

  await page.context().storageState({ path: AUTH_FILE });
  await browser.close();
}

export default globalSetup;
