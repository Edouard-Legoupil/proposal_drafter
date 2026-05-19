# Playwright End-to-End Testing

This directory contains the comprehensive end-to-end test suite for the Proposal Drafter application using Playwright.

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

#### Running Tests

```bash
# Install dependencies
npm install

# Install Playwright browsers
npx playwright install

# Run all tests
npx playwright test

# Run specific test file
npx playwright test test_1_user_profile.py

# Run in headed mode (show browser)
npx playwright test --headed

# Run with trace viewing
npx playwright test --trace on

# Show test report
npx playwright show-report
```

### Test Data Management

The test suite includes a preparation script to set up test data:

```bash
# Prepare test data (creates test users, roles, etc.)
npx playwright run prep_1_registration.py
```

### Test Environment

Tests are configured to run against:
- **Backend**: `http://localhost:8502`
- **Frontend**: `http://localhost:5173`

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
- **Port conflicts**: Ensure backend (8502) and frontend (5173) are running
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

### Test Data

Test data is managed through:
- Environment variables for credentials
- Preparation scripts for database setup
- Mock data for API responses where needed

### Performance Considerations

- Tests are optimized to run in parallel
- Large tests are split into logical sub-tests
- API calls are mocked where possible to reduce test time

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

