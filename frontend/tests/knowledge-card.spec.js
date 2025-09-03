import { test, expect } from '@playwright/test';

test.describe('Knowledge Card Creation', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/');
    await page.waitForURL('/login');
    await page.fill('input[name="email"]', 'testuser1@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.getByRole('button', { name: 'Login' }).click();
    await page.waitForURL('/dashboard');
  });

  test('should allow a user to create a new knowledge card', async ({ page }) => {
    // Navigate to the new knowledge card page
    await page.goto('/knowledge-card/new');

    // Fill in the form
    await page.getByLabel('Link To').selectOption({ label: 'Donor' });
    await page.getByLabel('Select Item').click();
    await page.locator('.react-select__control').click();
    await page.locator('#react-select-2-input').fill('New Donor');
    await page.getByText('Create "New Donor"').click();
    await page.getByLabel('Title*').fill('Test Knowledge Card');
    await page.getByLabel('Description').fill('This is a test knowledge card.');
    await page.getByPlaceholder('https://example.com').fill('https://example.com');
    await page.getByPlaceholder('Reference Type').fill('Test Reference');

    // Click the save button
    page.on('dialog', async dialog => {
      expect(dialog.message()).toContain('Knowledge card created successfully!');
      await dialog.accept();
    });

    await page.getByRole('button', { name: 'Save Card' }).click();
  });
});
