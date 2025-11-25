import { test, expect } from '@playwright/test';

const BACKEND_URL = 'http://localhost:8000';

test.describe('Health Check Endpoint', () => {
    test('should return 200 status code', async ({ request }) => {
        const response = await request.get(`${BACKEND_URL}/health`);
        expect(response.status()).toBe(200);
    });

    test('should return JSON response', async ({ request }) => {
        const response = await request.get(`${BACKEND_URL}/health`);
        expect(response.headers()['content-type']).toContain('application/json');
    });

    test('should contain status field', async ({ request }) => {
        const response = await request.get(`${BACKEND_URL}/health`);
        const data = await response.json();

        expect(data).toHaveProperty('status');
        expect(data.status).toBe('healthy');
    });

    test('should report agent initialization status', async ({ request }) => {
        const response = await request.get(`${BACKEND_URL}/health`);
        const data = await response.json();

        expect(data).toHaveProperty('agent_initialized');
        expect(typeof data.agent_initialized).toBe('boolean');
    });

    test('should report langchain agent initialization status', async ({ request }) => {
        const response = await request.get(`${BACKEND_URL}/health`);
        const data = await response.json();

        expect(data).toHaveProperty('langchain_agent_initialized');
        expect(typeof data.langchain_agent_initialized).toBe('boolean');
    });

    test('should report Ollama configuration', async ({ request }) => {
        const response = await request.get(`${BACKEND_URL}/health`);
        const data = await response.json();

        expect(data).toHaveProperty('ollama_host');
        expect(data).toHaveProperty('ollama_model');
        expect(typeof data.ollama_host).toBe('string');
        expect(typeof data.ollama_model).toBe('string');
    });

    test('should report backend URL', async ({ request }) => {
        const response = await request.get(`${BACKEND_URL}/health`);
        const data = await response.json();

        expect(data).toHaveProperty('backend_url');
        expect(typeof data.backend_url).toBe('string');
    });

    test('should report Langfuse configuration status', async ({ request }) => {
        const response = await request.get(`${BACKEND_URL}/health`);
        const data = await response.json();

        expect(data).toHaveProperty('langfuse_configured');
        expect(typeof data.langfuse_configured).toBe('boolean');
    });

    test('should respond quickly (under 1 second)', async ({ request }) => {
        const startTime = Date.now();
        await request.get(`${BACKEND_URL}/health`);
        const endTime = Date.now();

        const responseTime = endTime - startTime;
        expect(responseTime).toBeLessThan(1000);
    });

    test('should handle multiple concurrent requests', async ({ request }) => {
        const requests = Array(5).fill(null).map(() =>
            request.get(`${BACKEND_URL}/health`)
        );

        const responses = await Promise.all(requests);

        responses.forEach(response => {
            expect(response.status()).toBe(200);
        });
    });
});

test.describe('Health Check Reliability', () => {
    test('should be idempotent', async ({ request }) => {
        const response1 = await request.get(`${BACKEND_URL}/health`);
        const data1 = await response1.json();

        const response2 = await request.get(`${BACKEND_URL}/health`);
        const data2 = await response2.json();

        expect(data1.status).toBe(data2.status);
    });

    test('should not require authentication', async ({ request }) => {
        // Health check should be publicly accessible
        const response = await request.get(`${BACKEND_URL}/health`);
        expect(response.status()).toBe(200);
    });

    test('should work with CORS', async ({ request }) => {
        const response = await request.get(`${BACKEND_URL}/health`, {
            headers: {
                'Origin': 'http://localhost:5000'
            }
        });

        expect(response.status()).toBe(200);
    });
});

test.describe('Health Check Error Scenarios', () => {
    test('should handle OPTIONS request for CORS preflight', async ({ request }) => {
        const response = await request.fetch(`${BACKEND_URL}/health`, {
            method: 'OPTIONS',
            headers: {
                'Origin': 'http://localhost:5000',
                'Access-Control-Request-Method': 'GET'
            }
        });

        // Should either return 200 or 204
        expect([200, 204]).toContain(response.status());
    });

    test('should reject POST requests', async ({ request }) => {
        const response = await request.post(`${BACKEND_URL}/health`);

        // Should return 405 Method Not Allowed or 404
        expect([404, 405]).toContain(response.status());
    });
});
