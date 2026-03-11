import path from 'path';
import fs from 'fs';
import { config } from 'dotenv';
import { chromium, type FullConfig } from '@playwright/test';

config({ path: path.resolve(__dirname, '../../../.env') });

const E2E_LOGIN_EMAIL = process.env.E2E_LOGIN_EMAIL;
const E2E_LOGIN_PASSWORD = process.env.E2E_LOGIN_PASSWORD;

if (!E2E_LOGIN_EMAIL || !E2E_LOGIN_PASSWORD) {
  throw new Error(
    'E2E auth: set E2E_LOGIN_EMAIL and E2E_LOGIN_PASSWORD in .env (root of frontend).'
  );
}

async function globalSetup(playwrightConfig: FullConfig) {
  const projectUse = playwrightConfig.projects[0]?.use;
  const baseURL = projectUse?.baseURL ?? 'http://localhost:8000';
  const storageStatePath = projectUse?.storageState as string | undefined;

  if (!storageStatePath) {
    throw new Error('E2E auth: storageState path is not set in Playwright config.');
  }

  const authDir = path.dirname(storageStatePath);
  fs.mkdirSync(authDir, { recursive: true });

  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.goto(`${baseURL}/auth/signin`);
  await page.waitForLoadState('domcontentloaded');

  await page.locator('[data-test-id="input-login-email"]').fill(E2E_LOGIN_EMAIL as string);
  await page.locator('[data-test-id="input-login-password"]').fill(E2E_LOGIN_PASSWORD as string);
  await page.locator('[data-test-id="login-button"]').click();

  await page.waitForURL(/\/(dashboard|tasks)\//, { timeout: 15000 });

  await page.context().storageState({ path: storageStatePath });
  await browser.close();
}

export default globalSetup;
