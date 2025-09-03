// playwright.config.js
// @ts-check

/** @type {import('@playwright/test').PlaywrightTestConfig} */
const config = {
  testDir: './tests',
  use: {
    browserName: 'chromium',
    headless: true,
    baseURL: 'http://localhost:8503',
  },
};

module.exports = config;
