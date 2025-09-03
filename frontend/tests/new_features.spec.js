import { test, expect } from '@playwright/test';

test.describe('New Features', () => {
    test.beforeEach(async ({ page }) => {
        // Log in before each test
        await page.goto('/');
        await page.waitForURL('/login');
        await page.fill('input[name="email"]', 'user1@example.com');
        await page.fill('input[name="password"]', 'password');
        await page.getByRole('button', { name: 'LOGIN' }).click();
        await page.waitForURL('/dashboard');
    });

    test('Dashboard: should display project options popover', async ({ page }) => {
        await expect(page.getByText('Colombia Shelter Project')).toBeVisible();
        await page.locator('.Dashboard_project_tripleDotsContainer').first().click();
        await expect(page.getByText('View')).toBeVisible();
        await expect(page.getByText('Delete')).toBeVisible();
        await expect(page.getByText('Transfer')).toBeVisible();
    });

    test('Chat: should display updated workflow badges', async ({ page }) => {
        await page.getByText('Child Protection Ukraine').click();
        await page.waitForURL('/chat');
        await expect(page.getByText('Workflow Stage')).toBeVisible();
        await expect(page.getByText('Pre-Submission')).toBeVisible();
        await expect(page.getByTitle('Initial drafting stage - Author + AI')).toBeVisible();
    });

    test('Chat: should display revert buttons for past statuses', async ({ page }) => {
        await page.getByText('Child Protection Ukraine').click();
        await page.waitForURL('/chat');
        await expect(page.getByRole('button', { name: 'Revert' })).toBeVisible();
    });

    test('Chat: should display pre-submission review comments', async ({ page }) => {
        await page.getByText('Colombia Shelter Project').click();
        await page.waitForURL('/chat');
        await expect(page.getByText('Peer Reviews')).toBeVisible();
        await expect(page.getByText('Bob:')).toBeVisible();
        await expect(page.getByPlaceholder('Respond to this review...')).toBeVisible();
    });

    test('Chat: should display upload button for approved proposals', async ({ page }) => {
        await page.getByText('Child Protection Ukraine').click();
        await page.waitForURL('/chat');
        await expect(page.getByLabel('Upload Approved Document')).toBeVisible();
    });

    test('Knowledge Card: should display correct icon on dashboard', async ({ page }) => {
        await page.getByRole('tab', { name: 'Knowledge Card' }).click();
        await expect(page.locator('.fa-money-bill-wave')).toBeVisible();
    });

    test('Knowledge Card: should have updated form layout', async ({ page }) => {
        await page.getByRole('tab', { name: 'Knowledge Card' }).click();
        await page.getByRole('button', { name: 'Create New Knowledge Card' }).click();
        await expect(page.getByLabel('Reference Type*')).toBeVisible();
        await expect(page.locator('.squared-btn')).toBeVisible();
    });
});
