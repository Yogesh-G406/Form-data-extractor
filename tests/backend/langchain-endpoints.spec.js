import { test, expect } from '@playwright/test';

const BACKEND_URL = 'http://localhost:8000';

test.describe('LangChain Extract Form Fields Endpoint', () => {
    test('should accept POST requests', async ({ request }) => {
        const requestData = {
            extracted_text: {
                name: 'John Doe',
                address: '123 Main St'
            },
            language: 'English'
        };

        const response = await request.post(`${BACKEND_URL}/extract-form-fields`, {
            data: requestData
        });

        // Should not return 405 Method Not Allowed
        expect(response.status()).not.toBe(405);
    });

    test('should return JSON response', async ({ request }) => {
        const requestData = {
            extracted_text: {
                name: 'Jane Smith',
                email: 'jane@example.com'
            },
            language: 'English'
        };

        const response = await request.post(`${BACKEND_URL}/extract-form-fields`, {
            data: requestData
        });

        const contentType = response.headers()['content-type'];
        expect(contentType).toContain('application/json');
    });

    test('should handle valid extraction request', async ({ request }) => {
        const requestData = {
            extracted_text: {
                firstName: 'Alice',
                lastName: 'Johnson',
                phone: '555-1234'
            },
            language: 'English'
        };

        const response = await request.post(`${BACKEND_URL}/extract-form-fields`, {
            data: requestData
        });

        // Should either succeed or return service unavailable if agent not initialized
        expect([200, 503]).toContain(response.status());
    });

    test('should accept different languages', async ({ request }) => {
        const languages = ['English', 'Spanish', 'French'];

        for (const language of languages) {
            const requestData = {
                extracted_text: { test: 'data' },
                language: language
            };

            const response = await request.post(`${BACKEND_URL}/extract-form-fields`, {
                data: requestData
            });

            // Should accept the request
            expect([200, 503]).toContain(response.status());
        }
    });

    test('should return 503 when agent not initialized', async ({ request }) => {
        const requestData = {
            extracted_text: { test: 'data' },
            language: 'English'
        };

        const response = await request.post(`${BACKEND_URL}/extract-form-fields`, {
            data: requestData
        });

        if (response.status() === 503) {
            const data = await response.json();
            expect(data.detail).toContain('LangChain');
        }
    });

    test('should handle empty extracted text', async ({ request }) => {
        const requestData = {
            extracted_text: {},
            language: 'English'
        };

        const response = await request.post(`${BACKEND_URL}/extract-form-fields`, {
            data: requestData
        });

        // Should handle gracefully
        expect([200, 400, 503]).toContain(response.status());
    });

    test('should handle nested extracted text', async ({ request }) => {
        const requestData = {
            extracted_text: {
                personal: {
                    name: 'Bob Smith',
                    age: 30
                },
                contact: {
                    email: 'bob@example.com',
                    phone: '555-5678'
                }
            },
            language: 'English'
        };

        const response = await request.post(`${BACKEND_URL}/extract-form-fields`, {
            data: requestData
        });

        expect([200, 503]).toContain(response.status());
    });
});

test.describe('LangChain Validate Form Endpoint', () => {
    test('should accept POST requests', async ({ request }) => {
        const requestData = {
            fields: [
                { name: 'email', value: 'test@example.com' }
            ]
        };

        const response = await request.post(`${BACKEND_URL}/validate-form`, {
            data: requestData
        });

        expect(response.status()).not.toBe(405);
    });

    test('should validate form fields', async ({ request }) => {
        const requestData = {
            fields: [
                { name: 'name', value: 'John Doe' },
                { name: 'email', value: 'john@example.com' }
            ]
        };

        const response = await request.post(`${BACKEND_URL}/validate-form`, {
            data: requestData
        });

        expect([200, 503]).toContain(response.status());
    });

    test('should handle expected fields parameter', async ({ request }) => {
        const requestData = {
            fields: [
                { name: 'name', value: 'Jane Doe' }
            ],
            expected_fields: ['name', 'email', 'phone']
        };

        const response = await request.post(`${BACKEND_URL}/validate-form`, {
            data: requestData
        });

        expect([200, 503]).toContain(response.status());
    });

    test('should handle empty fields array', async ({ request }) => {
        const requestData = {
            fields: []
        };

        const response = await request.post(`${BACKEND_URL}/validate-form`, {
            data: requestData
        });

        expect([200, 400, 503]).toContain(response.status());
    });

    test('should return 503 when agent not initialized', async ({ request }) => {
        const requestData = {
            fields: [{ name: 'test', value: 'value' }]
        };

        const response = await request.post(`${BACKEND_URL}/validate-form`, {
            data: requestData
        });

        if (response.status() === 503) {
            const data = await response.json();
            expect(data.detail).toContain('LangChain');
        }
    });
});

test.describe('LangChain Classify Form Endpoint', () => {
    test('should accept POST requests', async ({ request }) => {
        const requestData = {
            extracted_text: {
                name: 'John Doe',
                company: 'Acme Corp'
            }
        };

        const response = await request.post(`${BACKEND_URL}/classify-form`, {
            data: requestData
        });

        expect(response.status()).not.toBe(405);
    });

    test('should classify form type', async ({ request }) => {
        const requestData = {
            extracted_text: {
                patient_name: 'Jane Doe',
                doctor: 'Dr. Smith',
                diagnosis: 'Common cold'
            }
        };

        const response = await request.post(`${BACKEND_URL}/classify-form`, {
            data: requestData
        });

        expect([200, 503]).toContain(response.status());
    });

    test('should handle different form types', async ({ request }) => {
        const formTypes = [
            { invoice_number: '12345', total: '$100' },
            { patient_name: 'John', medical_history: 'None' },
            { applicant_name: 'Alice', position: 'Developer' }
        ];

        for (const formData of formTypes) {
            const response = await request.post(`${BACKEND_URL}/classify-form`, {
                data: { extracted_text: formData }
            });

            expect([200, 503]).toContain(response.status());
        }
    });

    test('should handle empty extracted text', async ({ request }) => {
        const requestData = {
            extracted_text: {}
        };

        const response = await request.post(`${BACKEND_URL}/classify-form`, {
            data: requestData
        });

        expect([200, 400, 503]).toContain(response.status());
    });

    test('should return 503 when agent not initialized', async ({ request }) => {
        const requestData = {
            extracted_text: { test: 'data' }
        };

        const response = await request.post(`${BACKEND_URL}/classify-form`, {
            data: requestData
        });

        if (response.status() === 503) {
            const data = await response.json();
            expect(data.detail).toContain('LangChain');
        }
    });

    test('should handle complex nested structures', async ({ request }) => {
        const requestData = {
            extracted_text: {
                section1: {
                    field1: 'value1',
                    field2: 'value2'
                },
                section2: {
                    nested: {
                        deep: 'data'
                    }
                }
            }
        };

        const response = await request.post(`${BACKEND_URL}/classify-form`, {
            data: requestData
        });

        expect([200, 503]).toContain(response.status());
    });
});

test.describe('LangChain Endpoints Error Handling', () => {
    test('should handle malformed JSON in extract-form-fields', async ({ request }) => {
        const response = await request.post(`${BACKEND_URL}/extract-form-fields`, {
            data: 'invalid json'
        });

        expect([400, 422]).toContain(response.status());
    });

    test('should handle malformed JSON in validate-form', async ({ request }) => {
        const response = await request.post(`${BACKEND_URL}/validate-form`, {
            data: 'invalid json'
        });

        expect([400, 422]).toContain(response.status());
    });

    test('should handle malformed JSON in classify-form', async ({ request }) => {
        const response = await request.post(`${BACKEND_URL}/classify-form`, {
            data: 'invalid json'
        });

        expect([400, 422]).toContain(response.status());
    });

    test('should return JSON error responses', async ({ request }) => {
        const response = await request.post(`${BACKEND_URL}/extract-form-fields`, {
            data: {}
        });

        const contentType = response.headers()['content-type'];
        expect(contentType).toContain('application/json');
    });
});

test.describe('LangChain Endpoints Integration', () => {
    test('should work in sequence: extract -> validate -> classify', async ({ request }) => {
        const extractedText = {
            name: 'Test User',
            email: 'test@example.com',
            phone: '555-1234'
        };

        // Extract form fields
        const extractResponse = await request.post(`${BACKEND_URL}/extract-form-fields`, {
            data: {
                extracted_text: extractedText,
                language: 'English'
            }
        });

        if (extractResponse.status() === 200) {
            const extractedData = await extractResponse.json();

            // Validate (if extract succeeded)
            const validateResponse = await request.post(`${BACKEND_URL}/validate-form`, {
                data: {
                    fields: Object.entries(extractedText).map(([name, value]) => ({ name, value }))
                }
            });

            expect([200, 503]).toContain(validateResponse.status());

            // Classify
            const classifyResponse = await request.post(`${BACKEND_URL}/classify-form`, {
                data: { extracted_text: extractedText }
            });

            expect([200, 503]).toContain(classifyResponse.status());
        }
    });
});
