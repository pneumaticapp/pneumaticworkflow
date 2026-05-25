import { test as setup } from "@playwright/test";

const AUTH_FILE = "e2e/.auth/user.json";

setup("authenticate", async ({ page }) => {
  await page.goto("/auth/signin/");
  await page.waitForLoadState("domcontentloaded");

  await page.locator('[data-test-id="input-login-email"]').fill("test@admin.com");
  await page.locator('[data-test-id="input-login-password"]').fill("qwerty");
  await page.locator('[data-test-id="login-button"]').click();

  await page.waitForURL("**/dashboard/**");

  await page.context().storageState({ path: AUTH_FILE });
});
