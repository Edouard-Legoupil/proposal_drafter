### Running the Python Playwright Tests


This project uses [Playwright](https://playwright.dev/) for end-to-end testing. The tests are located in the `playwright/tests` directory.

These tests are written in Python using `pytest` and `pytest-playwright`.


#### 1. Prerequisites

Before running the tests, ensure you have the following installed:

*   Python 3.8+
*   pip

#### 2. Installation

1.  **Install Python dependencies:**

The required Python packages, including `pytest` and `pytest-playwright`, are listed in the `backend/requirements.txt` file. It's recommended to install these in a Python virtual environment.

The below is already mamanged throug the regular app set up.

```bash
cd backend
# Create and activate a virtual environment from the root directory
python -m venv venv
source venv/bin/activate

# Install dependencies from the backend requirements file
pip install -r requirements.txt

cd ../
```

2.  **Install Playwright browsers:**

After installing the Python packages, you need to install the browser binaries that Playwright uses.

```bash
playwright install
```

If you are on a headless Linux environment (like a CI/CD server), you might need to install additional system dependencies first:
```bash
playwright install-deps
```

#### 3. Running the Tests

1.  **First, Start the application:**

The tests require the application, including the database and other services, to be running. The recommended way to do this is with `start.sh` once you have the app running locally.

**Note:** The application requires several environment variables to be set, including database credentials and secrets for Azure OpenAI (`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, etc.). This means testing can be done onluy through a local environement - Make sure these are properly configured in your environment. The tests will fail if the application is not running or not configured correctly.

From the root of the repository, run:

```bash
./start.sh
```

2.  **Then Execute the tests:**

There are __6 set of user journey__ to test:

 * test_1_register.py -- create a new user
 * test_2_auth.py  -- login with the newly created user
 * test_3_dashboard.py -- test that all dashbaord feature works
 * test_4_proposal.py  -- test the creation of new proposal
 * test_5_knowledge_card.py -- test the creation of a knowledge card
 * test_6_peer_review.py  -- test the proposal peer review process


To run all the tests, navigate to the root of the repository and use `pytest`:

```bash
pytest playwright/tests/
```

To run the tests with a visible browser, use the `--headed` flag:
```bash
pytest playwright/tests/ --headed
```
Note that if you are running in a headless environment where `--headed` is required, you may need to use `xvfb-run`:
```bash
xvfb-run pytest playwright/tests/ --headed
```


To run a specific test file:
```bash
pytest playwright/tests/test_1_register.py --headed
```

