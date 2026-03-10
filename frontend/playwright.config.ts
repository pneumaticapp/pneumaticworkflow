/// <reference types="node" />
import { defineConfig, devices } from '@playwright/test';

const STORAGE_STATE = 'e2e/.auth/user.json';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:8000',
    trace: 'on-first-retry',
    launchOptions: {
      slowMo: Number(process.env.SLOW_MO) || 0,
    },
  },
  projects: [
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
    },

    /* --- DESKTOP BROWSERS --- */
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: STORAGE_STATE,
      },
      dependencies: ['setup'],
    },
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        storageState: STORAGE_STATE,
      },
      dependencies: ['setup'],
    },
    {
      name: 'webkit',
      use: {
        ...devices['Desktop Safari'],
        storageState: STORAGE_STATE,
      },
      dependencies: ['setup'],
    },

    /* --- MOBILE DEVICES (narrowest viewport) --- */
    {
      name: 'Mobile Chrome',
      use: {
        ...devices['Galaxy S8'],
        storageState: STORAGE_STATE,
      },
      dependencies: ['setup'],
    },
    {
      name: 'Mobile Safari',
      use: {
        ...devices['iPhone SE'],
        storageState: STORAGE_STATE,
      },
      dependencies: ['setup'],
    },
  ],
  webServer: {
    command: 'npm run local',
    url: 'http://localhost:8000',
    reuseExistingServer: true,
    timeout: 120000,
  },
});
