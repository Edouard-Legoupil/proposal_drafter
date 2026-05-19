# Playwright End-to-End Testing


This directory contains the end-to-end test suite for the Proposal Drafter application using [Playwright](https://playwright.dev/).


## 📁 Test Suite Overview

The test suite covers the complete user journey from registration to advanced features:

### Current Test Files

1. **test_1_user_profile.py** - User registration, login, and profile management
2. **test_2_proposal_creation.py** - Complete proposal creation workflow
3. **test_3_knowledge_card_new.py** - Knowledge card creation and management
4. **test_4_peer_review_new.py** - Proposal peer review functionality
5. **test_5_dashboard.py** - Dashboard navigation and features
6. **test_6_template_management.py** - Template management workflows
7. **test_7_quality_gate_review.py** - Quality gate and review processes
8. **test_8_document_sharing.py** - Document sharing and collaboration
9. **test_coverage_verification.py** - Test coverage verification
10. **test_suite_comprehensive.py** - Comprehensive end-to-end test suite

### Test Execution

#### Prerequisites
- Node.js v18+
- Python 3.10+
- Playwright installed (`npm install -g @playwright/test`)
- Backend server running (`cd backend && uvicorn main:app --host 0.0.0.0 --port 8502`)
- Frontend server running (`cd frontend && npm run dev`)

After installing the Python packages, install the browser binaries:

```bash
playwright install
# Install dependencies
npm install

# Install Playwright browsers
npx playwright install
```

For headless Linux environments (CI/CD servers):

```bash
playwright install-deps

```

#### Running Tests

```bash

source backend/venv/bin/activate
# Run all tests
pytest playwright/tests/ -v

# Run specific test file
pytest playwright/tests/test_1_user_profile.py

# Run in headed mode (show browser)
pytest playwright/tests/ --headed -v

# Run with trace viewing
pytest playwright/tests/ --trace on -v

# Show test report
pytest playwright/tests/ --report
```

### Test Data Management

The test suite includes a preparation script to set up test data:

```bash
# Prepare test data (creates test users, roles, etc.)
pytest playwright/tests/prep_1_registration.py
```

### Test Environment


### Best Practices

1. **Test Isolation**: Each test should clean up after itself
2. **Data Setup**: Use the preparation scripts for consistent test data
3. **Error Handling**: Tests include proper error handling and retries
4. **Screenshots**: Tests capture screenshots on failure for debugging
5. **Traces**: Full execution traces are available for debugging

### Test Maintenance

When adding new features:
1. Create a new test file following the naming convention `test_N_feature_name.py`
2. Follow the existing test patterns and page object models
3. Add the test to the comprehensive suite if it's a core workflow
4. Update this README with the new test file information

### Troubleshooting

**Common Issues:**
- **Database state**: Run preparation scripts to reset test data
- **Browser issues**: Reinstall Playwright browsers with `npx playwright install`
- **Test flakiness**: Use `npx playwright test --retries=2` for flaky tests

### CI/CD Integration

The test suite is designed to run in CI/CD pipelines:
```bash
# Run in CI mode
npx playwright test --project=chromium
```

## 🔧 Test Development

### Page Object Model

The tests use a Page Object Model pattern for maintainability. Key page objects include:
- `LoginPage`
- `DashboardPage`
- `ProposalCreationPage`
- `KnowledgeCardPage`
- `AdminPanel`


### Fixtures

The test suite uses pytest fixtures for better maintainability:

- `config`: Session-scoped configuration with environment variable support
- `playwright`: Session-scoped Playwright instance
- `browser`: Session-scoped browser instance
- `context`: Function-scoped browser context with video recording
- `page`: Function-scoped page instance
- `logged_in_user`: Page with pre-authenticated user
- `registered_user`: Creates and returns a new registered user
- `TestUser`: Class for managing test user credentials
- `TEST_USERS`: Predefined test users dictionary


### Test Data

Test data is managed through:
- Environment variables for credentials
- Preparation scripts for database setup
- Mock data for API responses where needed

### Performance Considerations

- Tests are optimized to run in parallel
- Large tests are split into logical sub-tests
- API calls are mocked where possible to reduce test time

### Test Marks

Tests are categorized using pytest marks:

- `@pytest.mark.smoke` - Quick sanity checks
- `@pytest.mark.e2e` - End-to-end user journeys
- `@pytest.mark.regression` - Regression tests
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.user_registration` - User registration tests
- `@pytest.mark.proposal_creation` - Proposal creation tests
- `@pytest.mark.knowledge_card` - Knowledge card tests
- `@pytest.mark.peer_review` - Peer review tests
- `@pytest.mark.dashboard` - Dashboard tests

### Screenshots and Videos

Screenshots are automatically saved to `playwright/test-results/screenshots/` with descriptive names.

Video recordings are saved to `playwright/test-results/videos/` when enabled. Each test that uses the `context` fixture with video recording enabled will generate a video file.

## Recording User Journeys with Codegen Tool

You can use Playwright's codegen tool to record new test interactions:

```bash
python3 -m playwright codegen http://localhost:8502 --test-id-attribute data-testid
```

The frontend uses `data-testid` attributes for robust element selection. The codegen tool will:

- Record page navigation as `page.goto('url')`
- Record clicks as `page.click('selector')`
- Record text input as `page.fill('selector', 'text')`

After recording, copy the generated Python script into the appropriate test file and refactor as needed to use the fixtures and follow the test patterns.

## Best Practices

1. **Use fixtures**: Prefer using fixtures (`page`, `config`, `logged_in_user`) over manual setup
2. **Use test IDs**: Always use `data-testid` selectors when available
3. **Add assertions**: Use `expect()` to verify UI state
4. **Handle timeouts**: Use appropriate timeouts for long operations (generation can take minutes)
5. **Clean up**: Tests should clean up after themselves when possible
6. **Mark tests**: Use appropriate pytest marks for categorization
7. **Skip when needed**: Use `pytest.skip()` when preconditions aren't met
8. **Document**: Add docstrings explaining test purpose and preconditions



## 📊 Test Coverage

The test suite provides comprehensive coverage of:
- ✅ User authentication and authorization
- ✅ Proposal creation and management
- ✅ Knowledge card workflows
- ✅ Peer review processes
- ✅ Template management
- ✅ Quality assurance workflows
- ✅ Document sharing and collaboration
- ✅ Admin functionality
- ✅ Error handling and edge cases

## 🚀 Future Enhancements

Planned test improvements:
- Add performance testing
- Expand mobile responsiveness testing
- Add accessibility testing
- Implement visual regression testing
- Add more comprehensive error scenario testing
