/// <reference types="node" />
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  globalSetup: './e2e/global-setup.ts',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:8000',
    storageState: 'e2e/.auth/user.json',
    trace: 'on-first-retry',
    launchOptions: {
      slowMo: 1200,
    },
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'npm run local',
    url: 'http://localhost:8000',
    reuseExistingServer: true,
    timeout: 120000,
  },
});
