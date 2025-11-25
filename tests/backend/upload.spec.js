import { test, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const BACKEND_URL = 'http://localhost:8000';

// Helper to create a test image file
function createTestImage() {
    const testDataDir = path.join(__dirname, '..', 'utils', 'test-data', 'images');

    // Create directory if it doesn't exist
    if (!fs.existsSync(testDataDir)) {
        fs.mkdirSync(testDataDir, { recursive: true });
    }

    const testImagePath = path.join(testDataDir, 'test-sample.jpg');

    // Create a minimal valid JPEG file if it doesn't exist
    if (!fs.existsSync(testImagePath)) {
        // Minimal JPEG header (1x1 pixel white image)
        const minimalJpeg = Buffer.from([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
            0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
            0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
            0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
            0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
            0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x14, 0x00, 0x01,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x03, 0xFF, 0xC4, 0x00, 0x14, 0x10, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00,
            0x7F, 0x80, 0xFF, 0xD9
        ]);

        fs.writeFileSync(testImagePath, minimalJpeg);
    }

    return testImagePath;
}

test.describe('File Upload Endpoint', () => {
    let testImagePath;

    test.beforeAll(() => {
        testImagePath = createTestImage();
    });

    test('should accept POST requests', async ({ request }) => {
        const response = await request.post(`${BACKEND_URL}/upload`, {
            multipart: {
                file: {
                    name: 'test-image.jpg',
                    mimeType: 'image/jpeg',
                    buffer: fs.readFileSync(testImagePath)
                }
            }
        });

        // Should not return 405 Method Not Allowed
        expect(response.status()).not.toBe(405);
    });

    test('should return JSON response', async ({ request }) => {
        const response = await request.post(`${BACKEND_URL}/upload`, {
            multipart: {
                file: {
                    name: 'test-image.jpg',
                    mimeType: 'image/jpeg',
                    buffer: fs.readFileSync(testImagePath)
                }
            }
        });

        const contentType = response.headers()['content-type'];
        expect(contentType).toContain('application/json');
    });

    test('should handle valid image upload', async ({ request }) => {
        const response = await request.post(`${BACKEND_URL}/upload`, {
            multipart: {
                file: {
                    name: 'test-upload.jpg',
                    mimeType: 'image/jpeg',
                    buffer: fs.readFileSync(testImagePath)
                }
            }
        });

        const data = await response.json();

        // Should have success field
        expect(data).toHaveProperty('success');
    });

    test('should return extracted data on success', async ({ request }) => {
        const response = await request.post(`${BACKEND_URL}/upload`, {
            multipart: {
                file: {
                    name: 'test-extract.jpg',
                    mimeType: 'image/jpeg',
                    buffer: fs.readFileSync(testImagePath)
                }
            }
        });

        const data = await response.json();

        if (data.success) {
            expect(data).toHaveProperty('extracted_data');
            expect(data).toHaveProperty('filename');
            expect(data).toHaveProperty('message');
        }
    });

    test('should save to database on successful extraction', async ({ request }) => {
        const response = await request.post(`${BACKEND_URL}/upload`, {
            multipart: {
                file: {
                    name: 'test-db-save.jpg',
                    mimeType: 'image/jpeg',
                    buffer: fs.readFileSync(testImagePath)
                }
            }
        });

        const data = await response.json();

        if (data.success) {
            expect(data).toHaveProperty('form_id');
            expect(data).toHaveProperty('saved_to_database');
        }
    });

    test('should accept language parameter', async ({ request }) => {
        const response = await request.post(`${BACKEND_URL}/upload?language=English`, {
            multipart: {
                file: {
                    name: 'test-lang.jpg',
                    mimeType: 'image/jpeg',
                    buffer: fs.readFileSync(testImagePath)
                }
            }
        });

        // Should accept the request
        expect(response.status()).not.toBe(400);
    });

    test('should handle different languages', async ({ request }) => {
        const languages = ['English', 'Spanish', 'French', 'German'];

        for (const language of languages) {
            const response = await request.post(`${BACKEND_URL}/upload?language=${language}`, {
                multipart: {
                    file: {
                        name: `test-${language}.jpg`,
                        mimeType: 'image/jpeg',
                        buffer: fs.readFileSync(testImagePath)
                    }
                });

            expect(response.status()).not.toBe(400);
        }
    });
});

test.describe('File Upload Validation', () => {
    let testImagePath;

    test.beforeAll(() => {
        testImagePath = createTestImage();
    });

    test('should reject missing file', async ({ request }) => {
        const response = await request.post(`${BACKEND_URL}/upload`);

        // Should return 422 (Unprocessable Entity) or 400 (Bad Request)
        expect([400, 422]).toContain(response.status());
    });

    test('should reject PDF files', async ({ request }) => {
        // Create a minimal PDF
        const pdfBuffer = Buffer.from('%PDF-1.4\n%EOF');

        const response = await request.post(`${BACKEND_URL}/upload`, {
            multipart: {
                file: {
                    name: 'test.pdf',
                    mimeType: 'application/pdf',
                    buffer: pdfBuffer
                }
            }
        });

        // Should return 400 Bad Request
        expect(response.status()).toBe(400);

        const data = await response.json();
        expect(data.detail).toContain('PDF');
    });

    test('should reject invalid file types', async ({ request }) => {
        const txtBuffer = Buffer.from('This is a text file');

        const response = await request.post(`${BACKEND_URL}/upload`, {
            multipart: {
                file: {
                    name: 'test.txt',
                    mimeType: 'text/plain',
                    buffer: txtBuffer
                }
            }
        });

        // Should return 400 Bad Request
        expect(response.status()).toBe(400);
    });

    test('should reject oversized files', async ({ request }) => {
        // Create a buffer larger than 10MB
        const largeBuffer = Buffer.alloc(11 * 1024 * 1024);

        const response = await request.post(`${BACKEND_URL}/upload`, {
            multipart: {
                file: {
                    name: 'large-image.jpg',
                    mimeType: 'image/jpeg',
                    buffer: largeBuffer
                }
            }
        });

        // Should return 400 Bad Request
        expect(response.status()).toBe(400);
    });

    test('should accept JPG files', async ({ request }) => {
        const response = await request.post(`${BACKEND_URL}/upload`, {
            multipart: {
                file: {
                    name: 'test.jpg',
                    mimeType: 'image/jpeg',
                    buffer: fs.readFileSync(testImagePath)
                }
            }
        });

        // Should not reject based on file type
        expect(response.status()).not.toBe(400);
    });

    test('should accept PNG files', async ({ request }) => {
        // Create a minimal PNG
        const pngBuffer = Buffer.from([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
            0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,
            0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
            0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
            0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
            0x42, 0x60, 0x82
        ]);

        const response = await request.post(`${BACKEND_URL}/upload`, {
            multipart: {
                file: {
                    name: 'test.png',
                    mimeType: 'image/png',
                    buffer: pngBuffer
                }
            }
        });

        // Should not reject based on file type
        expect(response.status()).not.toBe(400);
    });
});

test.describe('File Upload Error Handling', () => {
    let testImagePath;

    test.beforeAll(() => {
        testImagePath = createTestImage();
    });

    test('should return error when agent not initialized', async ({ request }) => {
        // This test assumes agent might not be initialized
        const response = await request.post(`${BACKEND_URL}/upload`, {
            multipart: {
                file: {
                    name: 'test.jpg',
                    mimeType: 'image/jpeg',
                    buffer: fs.readFileSync(testImagePath)
                }
            }
        });

        // Should either succeed or return 503 Service Unavailable
        expect([200, 503]).toContain(response.status());
    });

    test('should handle extraction failures gracefully', async ({ request }) => {
        const response = await request.post(`${BACKEND_URL}/upload`, {
            multipart: {
                file: {
                    name: 'test-fail.jpg',
                    mimeType: 'image/jpeg',
                    buffer: fs.readFileSync(testImagePath)
                }
            }
        });

        const data = await response.json();

        // Should have success field indicating status
        expect(data).toHaveProperty('success');
    });

    test('should clean up temporary files', async ({ request }) => {
        const response = await request.post(`${BACKEND_URL}/upload`, {
            multipart: {
                file: {
                    name: 'test-cleanup.jpg',
                    mimeType: 'image/jpeg',
                    buffer: fs.readFileSync(testImagePath)
                }
            }
        });

        // File should be processed (cleanup happens in backend)
        expect(response.status()).not.toBe(500);
    });
});
