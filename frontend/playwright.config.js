// @ts-check
/* eslint-disable no-undef */
import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for CasualTrader E2E tests
 *
 * Supports:
 * - Chromium (primary browser)
 * - Firefox and WebKit (optional)
 * - Multiple test directories (unit, integration, e2e)
 */
export default defineConfig({
  testDir: './tests',

  // Maximum time per test
  timeout: 30 * 1000,

  // Maximum time for the entire test run
  globalTimeout: 30 * 60 * 1000,

  // Continue running tests even if one fails
  fullyParallel: true,

  // Fail the build if test-only code is left behind
  forbidOnly: !!process.env.CI,

  // Retry failed tests in CI environment
  retries: process.env.CI ? 2 : 0,

  // Number of parallel workers
  workers: process.env.CI ? 1 : undefined,

  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['list'],
  ],

  // Shared settings for all tests
  use: {
    // Base URL for all tests
    baseURL: process.env.BASE_URL || 'http://localhost:3000',

    // Screenshot on failure
    screenshot: 'only-on-failure',

    // Video on failure
    video: 'retain-on-failure',

    // Trace on failure
    trace: 'on-first-retry',

    // Accept downloads
    acceptDownloads: true,
  },

  // Global setup/teardown
  globalSetup: process.env.CI ? undefined : undefined,
  globalTeardown: process.env.CI ? undefined : undefined,

  // Web server configuration
  webServer: process.env.SKIP_WEB_SERVER
    ? undefined
    : {
        command: 'npm run dev',
        url: 'http://localhost:3000',
        reuseExistingServer: !process.env.CI,
        timeout: 120 * 1000,
      },

  // Define projects (browsers to test)
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    // Firefox test (optional, commented out for speed)
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },

    // WebKit test (optional, commented out for speed)
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },

    // Mobile Chrome test (optional)
    // {
    //   name: 'Mobile Chrome',
    //   use: { ...devices['Pixel 5'] },
    // },

    // Mobile Safari test (optional)
    // {
    //   name: 'Mobile Safari',
    //   use: { ...devices['iPhone 12'] },
    // },
  ],
});
