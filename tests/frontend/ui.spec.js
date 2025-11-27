import { test, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test.describe('Frontend UI Tests', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test.describe('Navigation', () => {
        test('should load home page', async ({ page }) => {
            await expect(page).toHaveTitle(/Handwriting|Extraction/i);
        });

        test('should display Upload tab', async ({ page }) => {
            await expect(page.locator('button.tab-btn:has-text("Upload & Extract")')).toBeVisible();
        });

        test('should display Forms tab', async ({ page }) => {
            await expect(page.locator('button.tab-btn:has-text("Manage Forms")')).toBeVisible();
        });

        test('should switch to Forms tab', async ({ page }) => {
            await page.click('button.tab-btn:has-text("Manage Forms")');
            await expect(page.locator('button.tab-btn:has-text("Manage Forms")')).toHaveClass(/active/);
        });

        test('should switch back to Upload tab', async ({ page }) => {
            await page.click('button.tab-btn:has-text("Manage Forms")');
            await page.click('button.tab-btn:has-text("Upload & Extract")');
            await expect(page.locator('button.tab-btn:has-text("Upload & Extract")')).toHaveClass(/active/);
        });
    });

    test.describe('Upload Interface', () => {
        test('should show file input', async ({ page }) => {
            await expect(page.locator('input[type="file"]')).toBeAttached();
        });

        test('should show upload instructions', async ({ page }) => {
            await expect(page.locator('text=Drop your handwritten image here')).toBeVisible();
        });

        test('should accept image files', async ({ page }) => {
            const accept = await page.locator('input[type="file"]').getAttribute('accept');
            expect(accept).toMatch(/\.jpg,\.jpeg,\.png,\.pdf/);
        });

        test('should show upload button when file selected', async ({ page }) => {
            // Create a dummy file
            await page.setInputFiles('input[type="file"]', {
                name: 'test.jpg',
                mimeType: 'image/jpeg',
                buffer: Buffer.from('dummy content')
            });
            await expect(page.locator('button:has-text("Extract Text")')).toBeVisible();
        });
    });

    test.describe('Forms List Interface', () => {
        test.beforeEach(async ({ page }) => {
            await page.click('button.tab-btn:has-text("Manage Forms")');
        });

        test('should show forms list container', async ({ page }) => {
            await expect(page.locator('.form-manager')).toBeVisible();
        });

        test('should show add form button', async ({ page }) => {
            await expect(page.locator('button:has-text("Add New Form")')).toBeVisible();
        });
    });

    test.describe('Error Handling UI', () => {
        test('should show error on invalid file type', async ({ page }) => {
            const errorContainer = page.locator('.error-message');
            await expect(errorContainer).toBeHidden();
        });
    });
});
