import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should allow a user to log in and log out', async ({ page }) => {
    // Navigate to the login page
    await page.goto('/');

    // Expect to be redirected to /login
    await page.waitForURL('/login');

    // Fill in the login form
    await page.fill('input[name="email"]', 'testuser1@example.com');
    await page.fill('input[name="password"]', 'password123');

    // Click the login button
    await page.getByRole('button', { name: 'Login' }).click();

    // Wait for navigation to the dashboard and verify
    await page.waitForURL('/dashboard');
    await expect(page.getByRole('heading', { name: 'Proposals Dashboard' })).toBeVisible();

    // Click the logout button
    await page.getByRole('button', { name: 'Logout' }).click();

    // Wait for navigation back to the login page and verify
    await page.waitForURL('/login');
    await expect(page.getByRole('heading', { name: 'Login' })).toBeVisible();
  });
});
