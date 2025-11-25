import { test, expect } from '@playwright/test';

const BACKEND_URL = 'http://localhost:8000';

// Helper to create test form data
const createTestForm = () => ({
    form_name: `Test Form ${Date.now()}`,
    data: JSON.stringify({
        name: 'Test User',
        email: 'test@example.com',
        phone: '123-456-7890'
    })
});

test.describe('Forms CRUD - Create', () => {
    test('should create a new form', async ({ request }) => {
        const formData = createTestForm();

        const response = await request.post(`${BACKEND_URL}/forms`, {
            data: formData
        });

        expect(response.status()).toBe(200);

        const data = await response.json();
        expect(data).toHaveProperty('id');
        expect(data).toHaveProperty('form_name');
        expect(data).toHaveProperty('data');
        expect(data).toHaveProperty('created_at');
        expect(data).toHaveProperty('updated_at');
    });

    test('should return created form data', async ({ request }) => {
        const formData = createTestForm();

        const response = await request.post(`${BACKEND_URL}/forms`, {
            data: formData
        });

        const data = await response.json();
        expect(data.form_name).toBe(formData.form_name);
        expect(data.data).toBe(formData.data);
    });

    test('should assign unique ID to each form', async ({ request }) => {
        const formData1 = createTestForm();
        const formData2 = createTestForm();

        const response1 = await request.post(`${BACKEND_URL}/forms`, {
            data: formData1
        });

        const response2 = await request.post(`${BACKEND_URL}/forms`, {
            data: formData2
        });

        const data1 = await response1.json();
        const data2 = await response2.json();

        expect(data1.id).not.toBe(data2.id);
    });

    test('should set timestamps on creation', async ({ request }) => {
        const formData = createTestForm();

        const response = await request.post(`${BACKEND_URL}/forms`, {
            data: formData
        });

        const data = await response.json();
        expect(data.created_at).toBeTruthy();
        expect(data.updated_at).toBeTruthy();
    });
});

test.describe('Forms CRUD - Read', () => {
    let createdFormId;

    test.beforeAll(async ({ request }) => {
        // Create a form for testing
        const formData = createTestForm();
        const response = await request.post(`${BACKEND_URL}/forms`, {
            data: formData
        });
        const data = await response.json();
        createdFormId = data.id;
    });

    test('should get all forms', async ({ request }) => {
        const response = await request.get(`${BACKEND_URL}/forms`);

        expect(response.status()).toBe(200);

        const data = await response.json();
        expect(Array.isArray(data)).toBe(true);
    });

    test('should return array of forms', async ({ request }) => {
        const response = await request.get(`${BACKEND_URL}/forms`);
        const data = await response.json();

        expect(Array.isArray(data)).toBe(true);

        if (data.length > 0) {
            expect(data[0]).toHaveProperty('id');
            expect(data[0]).toHaveProperty('form_name');
            expect(data[0]).toHaveProperty('data');
        }
    });

    test('should get specific form by ID', async ({ request }) => {
        const response = await request.get(`${BACKEND_URL}/forms/${createdFormId}`);

        expect(response.status()).toBe(200);

        const data = await response.json();
        expect(data.id).toBe(createdFormId);
    });

    test('should return 404 for non-existent form', async ({ request }) => {
        const response = await request.get(`${BACKEND_URL}/forms/999999`);

        expect(response.status()).toBe(404);
    });

    test('should return complete form data', async ({ request }) => {
        const response = await request.get(`${BACKEND_URL}/forms/${createdFormId}`);
        const data = await response.json();

        expect(data).toHaveProperty('id');
        expect(data).toHaveProperty('form_name');
        expect(data).toHaveProperty('data');
        expect(data).toHaveProperty('created_at');
        expect(data).toHaveProperty('updated_at');
    });
});

test.describe('Forms CRUD - Update', () => {
    let testFormId;

    test.beforeEach(async ({ request }) => {
        // Create a fresh form for each test
        const formData = createTestForm();
        const response = await request.post(`${BACKEND_URL}/forms`, {
            data: formData
        });
        const data = await response.json();
        testFormId = data.id;
    });

    test('should update form name', async ({ request }) => {
        const updateData = {
            form_name: 'Updated Form Name'
        };

        const response = await request.put(`${BACKEND_URL}/forms/${testFormId}`, {
            data: updateData
        });

        expect(response.status()).toBe(200);

        const data = await response.json();
        expect(data.form_name).toBe(updateData.form_name);
    });

    test('should update form data', async ({ request }) => {
        const updateData = {
            data: JSON.stringify({ updated: true })
        };

        const response = await request.put(`${BACKEND_URL}/forms/${testFormId}`, {
            data: updateData
        });

        expect(response.status()).toBe(200);

        const data = await response.json();
        expect(data.data).toBe(updateData.data);
    });

    test('should update both name and data', async ({ request }) => {
        const updateData = {
            form_name: 'Fully Updated Form',
            data: JSON.stringify({ complete: 'update' })
        };

        const response = await request.put(`${BACKEND_URL}/forms/${testFormId}`, {
            data: updateData
        });

        const data = await response.json();
        expect(data.form_name).toBe(updateData.form_name);
        expect(data.data).toBe(updateData.data);
    });

    test('should update timestamp on update', async ({ request }) => {
        // Get original form
        const originalResponse = await request.get(`${BACKEND_URL}/forms/${testFormId}`);
        const originalData = await originalResponse.json();

        // Wait a moment
        await new Promise(resolve => setTimeout(resolve, 100));

        // Update form
        const updateResponse = await request.put(`${BACKEND_URL}/forms/${testFormId}`, {
            data: { form_name: 'Updated' }
        });

        const updatedData = await updateResponse.json();

        // Updated timestamp should be different
        expect(updatedData.updated_at).not.toBe(originalData.updated_at);
    });

    test('should return 404 for non-existent form update', async ({ request }) => {
        const response = await request.put(`${BACKEND_URL}/forms/999999`, {
            data: { form_name: 'Test' }
        });

        expect(response.status()).toBe(404);
    });

    test('should handle partial updates', async ({ request }) => {
        // Update only form_name
        const response = await request.put(`${BACKEND_URL}/forms/${testFormId}`, {
            data: { form_name: 'Partial Update' }
        });

        expect(response.status()).toBe(200);

        const data = await response.json();
        expect(data.form_name).toBe('Partial Update');
        expect(data.data).toBeTruthy(); // Original data should still exist
    });
});

test.describe('Forms CRUD - Delete', () => {
    let testFormId;

    test.beforeEach(async ({ request }) => {
        // Create a form to delete
        const formData = createTestForm();
        const response = await request.post(`${BACKEND_URL}/forms`, {
            data: formData
        });
        const data = await response.json();
        testFormId = data.id;
    });

    test('should delete a form', async ({ request }) => {
        const response = await request.delete(`${BACKEND_URL}/forms/${testFormId}`);

        expect(response.status()).toBe(200);
    });

    test('should return success message on delete', async ({ request }) => {
        const response = await request.delete(`${BACKEND_URL}/forms/${testFormId}`);
        const data = await response.json();

        expect(data).toHaveProperty('message');
        expect(data.message).toContain('deleted');
    });

    test('should actually remove form from database', async ({ request }) => {
        // Delete the form
        await request.delete(`${BACKEND_URL}/forms/${testFormId}`);

        // Try to get the deleted form
        const getResponse = await request.get(`${BACKEND_URL}/forms/${testFormId}`);

        expect(getResponse.status()).toBe(404);
    });

    test('should return 404 when deleting non-existent form', async ({ request }) => {
        const response = await request.delete(`${BACKEND_URL}/forms/999999`);

        expect(response.status()).toBe(404);
    });

    test('should not affect other forms when deleting', async ({ request }) => {
        // Create another form
        const formData = createTestForm();
        const createResponse = await request.post(`${BACKEND_URL}/forms`, {
            data: formData
        });
        const otherForm = await createResponse.json();

        // Delete the test form
        await request.delete(`${BACKEND_URL}/forms/${testFormId}`);

        // Other form should still exist
        const getResponse = await request.get(`${BACKEND_URL}/forms/${otherForm.id}`);
        expect(getResponse.status()).toBe(200);

        // Cleanup
        await request.delete(`${BACKEND_URL}/forms/${otherForm.id}`);
    });
});

test.describe('Forms CRUD - Edge Cases', () => {
    test('should handle empty form list', async ({ request }) => {
        const response = await request.get(`${BACKEND_URL}/forms`);
        const data = await response.json();

        expect(Array.isArray(data)).toBe(true);
    });

    test('should handle special characters in form name', async ({ request }) => {
        const formData = {
            form_name: 'Test Form with Special Chars: @#$%^&*()',
            data: JSON.stringify({ test: true })
        };

        const response = await request.post(`${BACKEND_URL}/forms`, {
            data: formData
        });

        expect(response.status()).toBe(200);

        const data = await response.json();

        // Cleanup
        await request.delete(`${BACKEND_URL}/forms/${data.id}`);
    });

    test('should handle large JSON data', async ({ request }) => {
        const largeData = {
            form_name: 'Large Data Form',
            data: JSON.stringify({
                field1: 'A'.repeat(1000),
                field2: 'B'.repeat(1000),
                nested: {
                    deep: {
                        data: 'C'.repeat(1000)
                    }
                }
            })
        };

        const response = await request.post(`${BACKEND_URL}/forms`, {
            data: largeData
        });

        expect(response.status()).toBe(200);

        const data = await response.json();

        // Cleanup
        await request.delete(`${BACKEND_URL}/forms/${data.id}`);
    });
});
