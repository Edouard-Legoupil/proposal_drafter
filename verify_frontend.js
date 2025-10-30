const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    await page.goto('http://localhost:8504/');

    // Wait for the main prompt area to be visible, indicating the page is loaded
    await page.waitForSelector('#main-prompt', { timeout: 60000 });
    console.log('Main prompt is visible.');

    // Click the Wizzard button to open the modal
    await page.click('button:has-text("Wizzard")');
    console.log('Clicked "Wizzard" button.');

    // Wait for the modal to appear to ensure it is loaded
    await page.waitForSelector('h2:has-text("Wizzard Insights")');
    console.log('Wizard modal opened successfully. Taking screenshot...');

    // Take a screenshot
    await page.screenshot({ path: 'wizzard_modal_verification.png' });
    console.log('Screenshot saved to wizzard_modal_verification.png');

  } catch (error) {
    console.error('An error occurred during verification:', error);
  } finally {
    await browser.close();
  }
})();
