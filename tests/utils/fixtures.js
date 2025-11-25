import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Test fixtures and utilities for Playwright tests
 */

// API Base URLs
export const FRONTEND_URL = 'http://localhost:5000';
export const BACKEND_URL = 'http://localhost:8000';

// Test data paths
export const TEST_DATA_DIR = path.join(__dirname, 'test-data');
export const TEST_IMAGES_DIR = path.join(TEST_DATA_DIR, 'images');

// Sample form data
export const SAMPLE_FORM_DATA = {
    form_name: 'Test Form',
    data: JSON.stringify({
        name: 'John Doe',
        email: 'john@example.com',
        phone: '123-456-7890'
    })
};

// Mock extracted data response
export const MOCK_EXTRACTION_RESPONSE = {
    success: true,
    filename: 'test-image.jpg',
    message: 'Handwriting extracted successfully',
    extracted_data: {
        name: 'Jane Smith',
        address: '123 Main St',
        city: 'New York',
        phone: '555-1234'
    },
    form_id: 1,
    saved_to_database: true
};

// Mock health check response
export const MOCK_HEALTH_RESPONSE = {
    status: 'healthy',
    agent_initialized: true,
    langchain_agent_initialized: true,
    ollama_host: 'http://localhost:11434',
    ollama_model: 'llava',
    backend_url: 'http://localhost:8000',
    langfuse_configured: true
};

// Helper function to create a test image file
export function createTestImagePath(filename) {
    return path.join(TEST_IMAGES_DIR, filename);
}

// Helper function to wait for element with timeout
export async function waitForElement(page, selector, timeout = 5000) {
    await page.waitForSelector(selector, { timeout });
}

// Helper function to upload file
export async function uploadFile(page, filePath) {
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
}

// Helper function to wait for API response
export async function waitForAPIResponse(page, urlPattern) {
    return await page.waitForResponse(response =>
        response.url().includes(urlPattern) && response.status() === 200
    );
}

// Helper to create mock form in database
export async function createMockForm(request, formData = SAMPLE_FORM_DATA) {
    const response = await request.post(`${BACKEND_URL}/forms`, {
        data: formData
    });
    return await response.json();
}

// Helper to cleanup test forms
export async function cleanupTestForms(request) {
    const response = await request.get(`${BACKEND_URL}/forms`);
    const forms = await response.json();

    for (const form of forms) {
        if (form.form_name.includes('Test')) {
            await request.delete(`${BACKEND_URL}/forms/${form.id}`);
        }
    }
}

// Helper to check if backend is ready
export async function isBackendReady(request) {
    try {
        const response = await request.get(`${BACKEND_URL}/health`);
        const health = await response.json();
        return health.status === 'healthy';
    } catch (error) {
        return false;
    }
}

// Helper to check if frontend is ready
export async function isFrontendReady(page) {
    try {
        await page.goto(FRONTEND_URL, { waitUntil: 'networkidle', timeout: 5000 });
        return true;
    } catch (error) {
        return false;
    }
}
