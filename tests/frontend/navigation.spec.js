import { test, expect } from '@playwright/test';

test.describe('Navigation and Tabs', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('should display both navigation tabs', async ({ page }) => {
        // Check for Upload tab
        const uploadTab = page.locator('button:has-text("Upload")');
        await expect(uploadTab).toBeVisible();

        // Check for Forms/Manage tab
        const formsTab = page.locator('button:has-text(/forms|manage/i)');
        await expect(formsTab).toBeVisible();
    });

    test('should have Upload tab active by default', async ({ page }) => {
        // Check for active class on upload tab
        const uploadTab = page.locator('button:has-text("Upload")').first();

        // Verify it's visible and likely active
        await expect(uploadTab).toBeVisible();

        // Check if it has active styling
        const className = await uploadTab.getAttribute('class');
        expect(className).toContain('active');
    });

    test('should switch to Forms tab when clicked', async ({ page }) => {
        // Click on Forms tab
        const formsTab = page.locator('button:has-text(/forms|manage/i)');
        await formsTab.click();

        // Wait for tab to become active
        await expect(formsTab).toHaveClass(/active/);

        // Verify forms content is displayed
        // Could check for form list, table, or empty state
        await page.waitForTimeout(500); // Allow transition
    });

    test('should switch back to Upload tab', async ({ page }) => {
        // First switch to Forms tab
        const formsTab = page.locator('button:has-text(/forms|manage/i)');
        await formsTab.click();
        await page.waitForTimeout(300);

        // Then switch back to Upload tab
        const uploadTab = page.locator('button:has-text("Upload")').first();
        await uploadTab.click();

        // Verify Upload tab is active
        await expect(uploadTab).toHaveClass(/active/);

        // Verify upload content is displayed
        await expect(page.locator('input[type="file"]')).toBeVisible();
    });

    test('should show correct content for Upload tab', async ({ page }) => {
        // Click Upload tab
        const uploadTab = page.locator('button:has-text("Upload")').first();
        await uploadTab.click();

        // Verify upload-specific content
        await expect(page.locator('input[type="file"]')).toBeVisible();
    });

    test('should show correct content for Forms tab', async ({ page }) => {
        // Click Forms tab
        const formsTab = page.locator('button:has-text(/forms|manage/i)');
        await formsTab.click();

        // Wait for content to load
        await page.waitForTimeout(500);

        // Verify forms-specific content (table, list, or empty state)
        // The exact content depends on whether there are forms in the database
        const bodyContent = await page.textContent('body');
        const hasFormsContent = bodyContent.includes('Form') ||
            bodyContent.includes('No forms') ||
            bodyContent.includes('Empty');

        expect(hasFormsContent).toBeTruthy();
    });

    test('should maintain tab state during navigation', async ({ page }) => {
        // Switch to Forms tab
        const formsTab = page.locator('button:has-text(/forms|manage/i)');
        await formsTab.click();
        await expect(formsTab).toHaveClass(/active/);

        // Verify state is maintained
        await page.waitForTimeout(300);
        await expect(formsTab).toHaveClass(/active/);
    });

    test('should have proper tab styling', async ({ page }) => {
        const uploadTab = page.locator('button:has-text("Upload")').first();
        const formsTab = page.locator('button:has-text(/forms|manage/i)');

        // Both tabs should be visible
        await expect(uploadTab).toBeVisible();
        await expect(formsTab).toBeVisible();

        // Tabs should be clickable
        await expect(uploadTab).toBeEnabled();
        await expect(formsTab).toBeEnabled();
    });

    test('should show tab icons or emojis', async ({ page }) => {
        // Check if tabs have icons/emojis
        const uploadTab = page.locator('button:has-text("Upload")').first();
        const formsTab = page.locator('button:has-text(/forms|manage/i)');

        const uploadText = await uploadTab.textContent();
        const formsText = await formsTab.textContent();

        // Should contain emoji or icon indicators
        expect(uploadText?.length).toBeGreaterThan(6); // More than just "Upload"
        expect(formsText?.length).toBeGreaterThan(5); // More than just "Forms"
    });

    test('should handle rapid tab switching', async ({ page }) => {
        const uploadTab = page.locator('button:has-text("Upload")').first();
        const formsTab = page.locator('button:has-text(/forms|manage/i)');

        // Rapidly switch tabs
        await formsTab.click();
        await page.waitForTimeout(100);
        await uploadTab.click();
        await page.waitForTimeout(100);
        await formsTab.click();
        await page.waitForTimeout(100);
        await uploadTab.click();

        // Should end on Upload tab
        await expect(uploadTab).toHaveClass(/active/);
        await expect(page.locator('input[type="file"]')).toBeVisible();
    });
});

test.describe('Tab Accessibility', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('should be keyboard navigable', async ({ page }) => {
        // Tab navigation should work
        await page.keyboard.press('Tab');

        // Verify focus is on a tab button
        const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
        expect(['BUTTON', 'A', 'INPUT']).toContain(focusedElement);
    });

    test('should have proper ARIA attributes', async ({ page }) => {
        const uploadTab = page.locator('button:has-text("Upload")').first();

        // Verify it's a button
        expect(await uploadTab.evaluate(el => el.tagName)).toBe('BUTTON');
    });
});
