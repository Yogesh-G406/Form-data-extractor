# Test Suite for Handwriting Extraction AI

Comprehensive test suite covering frontend UI, backend API, and Python OCR service.

## 📋 Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Installation](#installation)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Writing New Tests](#writing-new-tests)
- [CI/CD Integration](#cicd-integration)

## 🎯 Overview

This test suite provides comprehensive coverage for:

1. **Frontend Tests** (Playwright) - UI/UX testing for React application
2. **Backend API Tests** (Playwright) - API endpoint testing for FastAPI service
3. **Python OCR Service Tests** (Pytest) - Unit and integration tests for OCR agents

## 📁 Test Structure

```
tests/
├── frontend/                    # Frontend UI tests
│   ├── upload.spec.js          # File upload component tests
│   ├── navigation.spec.js      # Navigation and tab tests
│   ├── form-manager.spec.js    # Form manager component tests
│   ├── result-display.spec.js  # Result display tests
│   └── error-handling.spec.js  # Error handling tests
│
├── backend/                     # Backend API tests
│   ├── health.spec.js          # Health check endpoint tests
│   ├── upload.spec.js          # File upload endpoint tests
│   ├── forms-crud.spec.js      # CRUD operations tests
│   └── langchain-endpoints.spec.js  # LangChain endpoints tests
│
├── ocr/                         # Python OCR service tests
│   ├── test_agent.py           # HandwritingExtractionAgent tests
│   ├── test_langchain_agent.py # LangChainFormAgent tests
│   └── test_integration.py     # Integration tests
│
└── utils/                       # Test utilities
    ├── fixtures.js             # Shared fixtures and helpers
    └── test-data/              # Test images and sample data
        └── images/             # Test image files
```

## 🚀 Installation

### 1. Install Playwright Dependencies

```bash
# Install Playwright
npm install

# Install Playwright browsers
npx playwright install
```

### 2. Install Python Test Dependencies

```bash
# Install Python test dependencies
pip install -r requirements-test.txt
```

## 🧪 Running Tests

### Frontend Tests

```bash
# Run all frontend tests
npm run test:frontend

# Run in headed mode (see browser)
npm run test:frontend -- --headed

# Run in UI mode (interactive)
npm run test:ui

# Run specific test file
npx playwright test tests/frontend/upload.spec.js
```

### Backend API Tests

```bash
# Run all backend tests
npm run test:backend

# Run in headed mode
npm run test:backend -- --headed

# Run specific test file
npx playwright test tests/backend/health.spec.js
```

### Python OCR Tests

```bash
# Run all Python tests
pytest tests/ocr -v

# Run with coverage
pytest tests/ocr -v --cov=backend --cov-report=html

# Run specific test file
pytest tests/ocr/test_agent.py -v

# Run specific test class
pytest tests/ocr/test_agent.py::TestAgentInitialization -v

# Run specific test
pytest tests/ocr/test_agent.py::TestAgentInitialization::test_agent_initializes_successfully -v
```

### Run All Tests

```bash
# Run all Playwright tests
npm run test:all

# Run all Python tests
pytest tests/ocr -v

# Or run both sequentially
npm run test:all && pytest tests/ocr -v
```

## 📊 Test Coverage

### Frontend Coverage

The frontend tests cover:
- ✅ File upload component (drag & drop, file selection, validation)
- ✅ Navigation and tab switching
- ✅ Form manager (list, view, edit, delete)
- ✅ Result display (JSON formatting, copy functionality)
- ✅ Error handling (network errors, validation errors)
- ✅ Responsive design
- ✅ Accessibility features

### Backend API Coverage

The backend tests cover:
- ✅ Health check endpoint
- ✅ File upload endpoint (validation, processing)
- ✅ Forms CRUD operations (Create, Read, Update, Delete)
- ✅ LangChain endpoints (extract, validate, classify)
- ✅ Error responses and status codes
- ✅ Request/response validation
- ✅ Multi-language support

### Python OCR Service Coverage

The Python tests cover:
- ✅ Agent initialization
- ✅ Image preprocessing
- ✅ Image encoding (base64)
- ✅ JSON parsing
- ✅ Translation functionality
- ✅ Handwriting extraction
- ✅ Form field extraction
- ✅ Form validation
- ✅ Form classification
- ✅ Error handling
- ✅ Integration workflows

## 📝 Writing New Tests

### Frontend Test Example

```javascript
import { test, expect } from '@playwright/test';

test.describe('My New Feature', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should do something', async ({ page }) => {
    // Your test code here
    await expect(page.locator('h1')).toBeVisible();
  });
});
```

### Backend API Test Example

```javascript
import { test, expect } from '@playwright/test';

const BACKEND_URL = 'http://localhost:8000';

test.describe('My API Endpoint', () => {
  test('should return expected response', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/my-endpoint`);
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('expected_field');
  });
});
```

### Python Test Example

```python
import pytest

class TestMyFeature:
    def test_something(self):
        # Your test code here
        assert True
    
    @pytest.fixture
    def my_fixture(self):
        # Setup code
        yield "fixture_value"
        # Teardown code
```

## 🔧 Test Configuration

### Playwright Configuration

See `playwright.config.js` for:
- Browser configurations
- Test timeouts
- Screenshot/video settings
- Web server configuration

### Pytest Configuration

See `pytest.ini` for:
- Test discovery patterns
- Coverage settings
- Test markers

## 📈 Generating Test Reports

### Playwright Reports

```bash
# Generate HTML report
npm run test:report

# This will open the report in your browser
```

### Python Coverage Reports

```bash
# Generate HTML coverage report
pytest tests/ocr --cov=backend --cov-report=html

# Open htmlcov/index.html in your browser
```

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          npm install
          npx playwright install --with-deps
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run Playwright tests
        run: npm run test:all
      
      - name: Run Python tests
        run: pytest tests/ocr -v --cov=backend
```

## 🐛 Debugging Tests

### Playwright Debugging

```bash
# Run in debug mode
npm run test:debug

# Run with headed browser
npm run test:headed

# Use Playwright Inspector
npx playwright test --debug
```

### Python Debugging

```bash
# Run with verbose output
pytest tests/ocr -vv

# Run with print statements visible
pytest tests/ocr -v -s

# Run with pdb debugger
pytest tests/ocr --pdb
```

## 📌 Best Practices

1. **Keep tests independent** - Each test should be able to run independently
2. **Use descriptive names** - Test names should clearly describe what they test
3. **Clean up after tests** - Remove test data created during tests
4. **Mock external services** - Don't rely on external APIs in unit tests
5. **Test edge cases** - Include tests for error conditions and edge cases
6. **Maintain test data** - Keep test images and data in `tests/utils/test-data/`

## 🆘 Troubleshooting

### Common Issues

**Issue**: Playwright tests fail with "Target closed"
- **Solution**: Increase timeout in `playwright.config.js`

**Issue**: Backend tests fail with connection errors
- **Solution**: Ensure backend is running on port 8000

**Issue**: Python tests fail with import errors
- **Solution**: Ensure `backend` directory is in Python path

**Issue**: Tests fail intermittently
- **Solution**: Add appropriate waits and increase timeouts

## 📚 Additional Resources

- [Playwright Documentation](https://playwright.dev/)
- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [React Testing Best Practices](https://react.dev/learn/testing)

## 🤝 Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Maintain test coverage above 80%
4. Update this README if adding new test categories

---

**Happy Testing! 🎉**
