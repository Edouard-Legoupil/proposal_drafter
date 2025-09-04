import { test, expect } from '@playwright/test';

test.describe('Peer Review', () => {
  test('should allow a user to submit a proposal for peer review and another user to submit a review', async ({ page }) => {
    // Part 1: Submit for review as testuser1
    await page.goto('/');
    await page.waitForURL('/login');
    await page.fill('input[name="email"]', 'testuser1@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.getByRole('button', { name: 'Login' }).click();
    await page.waitForURL('/dashboard');

    await page.getByRole('button', { name: 'Generate New Proposal' }).click();
    await page.waitForURL('/chat');
    await page.getByLabel('Project Title').fill('Peer Review Test Project');
    await page.getByLabel('Targeted Donor').selectOption({ label: 'UNHCR' });
    await page.getByLabel('Project Duration (in months)').fill('12');
    await page.getByLabel('Project Budget (in USD)').fill('100000');
    await page.getByLabel('Project Description').fill('This is a test project for peer review.');
    await page.getByRole('button', { name: 'Generate' }).click();
    await expect(page.locator('h2:has-text("Executive Summary")')).toBeVisible({ timeout: 120000 });

    const url = page.url();
    const proposalId = url.split('/').pop();

    await page.getByRole('button', { name: 'Peer Review' }).click();

    await page.locator('.multi-select-modal').waitFor();
    await page.getByText('Test User 2').click();
    await page.getByRole('button', { name: 'Confirm' }).click();

    await expect(page.locator('.status-badge.active')).toHaveText('Peer Review');
    await page.getByRole('button', { name: 'Logout' }).click();
    await page.waitForURL('/login');

    // Part 2: Submit review as testuser2
    await page.fill('input[name="email"]', 'testuser2@example.com');
    await page.fill('input[name="password"]', 'password456');
    await page.getByRole('button', { name: 'Login' }).click();
    await page.waitForURL('/dashboard');

    await page.goto(`/review/${proposalId}`);
    await page.waitForURL(`/review/${proposalId}`);

    await page.locator('textarea').first().fill('This is a test review comment.');

    await page.getByRole('button', { name: 'Review Completed' }).click();

    await page.waitForURL('/dashboard');
    await expect(page.getByRole('heading', { name: 'Proposals Dashboard' })).toBeVisible();
  });
});
