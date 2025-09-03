import { test, expect } from '@playwright/test';

test.describe('Proposal Generation', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/');
    await page.waitForURL('/login');
    await page.fill('input[name="email"]', 'testuser1@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.getByRole('button', { name: 'Login' }).click();
    await page.waitForURL('/dashboard');
  });

  test('should allow a user to generate a new proposal', async ({ page }) => {
    // Click the "Generate New Proposal" button
    await page.getByRole('button', { name: 'Generate New Proposal' }).click();
    await page.waitForURL('/chat');

    // Fill in the proposal form
    await page.getByLabel('Project Title').fill('Test Project');
    await page.getByLabel('Targeted Donor').selectOption({ label: 'UNHCR' });
    await page.getByLabel('Project Duration (in months)').fill('12');
    await page.getByLabel('Project Budget (in USD)').fill('100000');
    await page.getByLabel('Project Description').fill('This is a test project description.');

    // Click the "Generate" button
    await page.getByRole('button', { name: 'Generate' }).click();

    // Wait for the sections to be generated
    // This will depend on the application's implementation.
    // I will wait for a specific section to be visible.
    await expect(page.locator('h2:has-text("Executive Summary")')).toBeVisible({ timeout: 120000 });
    await expect(page.locator('h2:has-text("Background and Needs Assessment")')).toBeVisible({ timeout: 120000 });
  });

  test('should allow a user to edit and save a proposal', async ({ page }) => {
    // This test depends on the previous test to have created a proposal.
    // In a real-world scenario, we would create a proposal via API in a beforeAll hook.

    // Click on the first proposal in the list
    await page.locator('.proposal-card').first().click();
    await page.waitForURL(/\/chat\/.+/);

    // Edit the executive summary
    const executiveSummaryEditor = page.locator('div[data-testid="section-Executive Summary"] >> .tiptap');
    await executiveSummaryEditor.click();
    await executiveSummaryEditor.fill('This is an edited executive summary.');

    // Click the save button
    await page.getByRole('button', { name: 'Save' }).click();

    // Reload the page
    await page.reload();
    await page.waitForURL(/\/chat\/.+/);


    // Verify the changes have been saved
    await expect(executiveSummaryEditor).toHaveText('This is an edited executive summary.');
  });

  test('should allow a user to download a proposal', async ({ page }) => {
    // This test depends on the previous tests to have created a proposal.
    await page.locator('.proposal-card').first().click();
    await page.waitForURL(/\/chat\/.+/);

    // Click the download button
    await page.getByRole('button', { name: 'Download' }).click();

    // Start waiting for the download
    const downloadPromise = page.waitForEvent('download');

    // Click the PDF download button
    await page.getByRole('button', { name: 'PDF' }).click();

    // Wait for the download to complete
    const download = await downloadPromise;

    // Verify the download
    expect(download.suggestedFilename()).toContain('.pdf');
  });
});
