# Playwright End-to-End Testing

This directory contains the end-to-end test suite for the Proposal Drafter application using [Playwright](https://playwright.dev/).

## Test Structure

```
playwright/
├── readme.md              # This file
├── pytest.ini             # Pytest configuration
├── tests/
│   ├── __init__.py        # Python package init
│   ├── conftest.py        # Shared fixtures and configuration
│   ├── test_1_registration.py    # User registration tests
│   ├── test_2_proposal_creation.py # Proposal creation tests
│   ├── test_3_knowledge_card_new.py  # Knowledge card tests
│   ├── test_4_peer_review_new.py  # Peer review workflow tests
│   └── test_5_dashboard.py        # Dashboard and metrics tests
└── test-results/          # Generated test artifacts (videos, screenshots)
```

## Test Organization

The test suite is organized into 5 main test files, each covering a specific user journey:

### 1. User Registration (`test_1_registration.py`)
- Single user registration and login
- Registration with test ID selectors
- Multiple user registration
- Pre-defined user registration (backward compatible)

### 2. Proposal Creation (`test_2_proposal_creation.py`)
- Create new proposals
- Navigate between proposal sections
- Edit and regenerate sections
- Export proposals as Word documents
- Filter proposals by status

### 3. Knowledge Cards (`test_3_knowledge_card_new.py`)
- View knowledge cards dashboard
- Filter knowledge cards by type
- View existing knowledge cards
- View knowledge card history
- Create new knowledge cards for donors, outcomes, and field contexts
- Manage references and ingestion
- Populate and edit card content

### 4. Peer Review (`test_4_peer_review_new.py`)
- Submit proposals for peer review
- Add peer review comments
- Mark reviews as completed
- Respond to peer review comments
- Submit proposals after review

### 5. Dashboard (`test_5_dashboard.py`)
- Dashboard loading and navigation
- Proposal cards display
- Team and status filtering
- Knowledge card counts
- Dashboard metrics
- User menu and logout

## Prerequisites

Before running the tests, ensure you have the following installed:

- Python 3.8+
- pip

## Installation

### 1. Install Python Dependencies

The required Python packages are listed in `backend/requirements.txt`. Install them in a virtual environment:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ../
```

### 2. Install Playwright Browsers

After installing the Python packages, install the browser binaries:

```bash
playwright install
```

For headless Linux environments (CI/CD servers):

```bash
playwright install-deps
```

## Running the Tests

### Start the Application

The tests require the application to be running with all services (database, backend, frontend):

```bash
./start.sh
```

**Important:** Ensure all environment variables are properly configured:
- Database credentials
- Azure OpenAI endpoint and API key (`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`)
- Other required secrets

The tests will fail if the application is not running or not configured correctly.

### Run All Tests

From the root of the repository:

```bash
pytest playwright/tests/ -v
```

### Run with Visible Browser

To see the browser during test execution:

```bash
pytest playwright/tests/ --headed -v
```

For headless environments where `--headed` is required:

```bash
xvfb-run pytest playwright/tests/ --headed -v
```

### Run Specific Test Files

```bash
# Run only registration tests
pytest playwright/tests/test_1_registration.py -v

# Run only proposal creation tests
pytest playwright/tests/test_2_proposal_creation.py -v

# Run only knowledge card tests
pytest playwright/tests/test_3_knowledge_card_new.py -v

# Run only peer review tests
pytest playwright/tests/test_4_peer_review_new.py -v

# Run only dashboard tests
pytest playwright/tests/test_5_dashboard.py -v
```

### Run Specific Tests by Marker

```bash
# Run only smoke tests (quick sanity checks)
pytest playwright/tests/ -m smoke -v

# Run only end-to-end tests
pytest playwright/tests/ -m e2e -v

# Run only regression tests
pytest playwright/tests/ -m regression -v

# Run only user registration tests
pytest playwright/tests/ -m user_registration -v

# Run only proposal creation tests
pytest playwright/tests/ -m proposal_creation -v

# Run only knowledge card tests
pytest playwright/tests/ -m knowledge_card -v

# Run only peer review tests
pytest playwright/tests/ -m peer_review -v

# Run only dashboard tests
pytest playwright/tests/ -m dashboard -v
```

### Run with Custom Configuration

You can override the default configuration using environment variables:

```bash
# Run with custom base URL
PLAYWRIGHT_BASE_URL=http://localhost:8080 pytest playwright/tests/ -v

# Run headless (useful for CI/CD)
PLAYWRIGHT_HEADLESS=true pytest playwright/tests/ -v

# Run with faster execution (no slow_mo)
PLAYWRIGHT_SLOW_MO=0 pytest playwright/tests/ -v
```

## Test Features

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

### Configuration

Default configuration (can be overridden by environment variables):

```python
{
    "base_url": "http://localhost:8502",
    "headless": False,
    "slow_mo": 500,  # milliseconds
    "viewport_width": 1920,
    "viewport_height": 1080,
    "video_dir": "playwright/test-results/videos",
    "screenshot_dir": "playwright/test-results/screenshots",
    "default_timeout": 30000,  # 30 seconds
    "long_timeout": 600000,  # 10 minutes
}
```

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

## Troubleshooting

### Tests Fail with "No existing proposal found"

The test suite expects certain data to exist. Run the registration and proposal creation tests first to set up the necessary data.

```bash
# Run tests in order
pytest playwright/tests/test_1_registration.py -v
pytest playwright/tests/test_2_proposal_creation.py -v
pytest playwright/tests/test_3_knowledge_card_new.py -v
```

### Tests Fail with "Element not found"

The frontend may have changed. Use the codegen tool to update the selectors:

```bash
python3 -m playwright codegen http://localhost:8502
```

### Tests Run Too Slowly

Disable the slow_mo setting:

```bash
PLAYWRIGHT_SLOW_MO=0 pytest playwright/tests/ -v
```

Or run headless:

```bash
PLAYWRIGHT_HEADLESS=true pytest playwright/tests/ -v
```

### Browser Crashes

Ensure all system dependencies are installed:

```bash
playwright install-deps
```

## Test Data Management

The test suite uses predefined test users:

| User | Email | Password | Team Index |
|------|-------|----------|------------|
| Primary | test_user@unhcr.org | password123 | 1 |
| Secondary | test_user_bis@unhcr.org | password123 | 2 |
| Tertiary | test_user_ter@unhcr.org | password123 | 1 |

Tests can also generate unique users on demand using `TestUser.generate_unique()`.

## Continuous Integration

For CI/CD environments, use headless mode and disable slow_mo:

```yaml
# GitHub Actions example
- name: Run Playwright Tests
  run: |
    PLAYWRIGHT_HEADLESS=true \
    PLAYWRIGHT_SLOW_MO=0 \
    pytest playwright/tests/ -v --tb=short
```

Ensure the application is running before tests start.

## Maintenance

### Updating Selectors

When the frontend changes and selectors break:

1. Use the codegen tool to identify new selectors
2. Update the `data-testid` attributes in the frontend
3. Update the test files to use the new selectors
4. Run tests to verify the changes

### Adding New Tests

1. Create a new test function in the appropriate test file
2. Use existing fixtures when possible
3. Add appropriate pytest marks
4. Follow the existing test patterns
5. Add docstrings explaining the test purpose
6. Use `take_screenshot()` for important steps

### Removing Old Tests

The following files have been deprecated and replaced:

- `test_1_register.py` → Use `test_1_registration.py`
- `test_1_register2.py` → Removed (duplicate)
- `test_1_registerB.py` → Removed (duplicate)
- `test_2_create_proposal.py` → Use `test_2_proposal_creation.py`
- `test_3_knowledge_card.py` → Use `test_3_knowledge_card_new.py`
- `test_4_peer_review.py` → Use `test_4_peer_review_new.py`
- `test_5_dashboard.py` → Newly created

The old files are kept for reference but will be removed in future updates.
