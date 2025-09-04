### Running the Python Playwright Tests

These tests are written in Python using `pytest` and `pytest-playwright`.

#### 1. Prerequisites

Before running the tests, ensure you have the following installed:

*   Python 3.8+
*   pip
*   Docker and Docker Compose

#### 2. Installation

1.  **Install Python dependencies:**

    The required Python packages, including `pytest` and `pytest-playwright`, are listed in the `backend/requirements.txt` file. It's recommended to install these in a Python virtual environment.

    ```bash
    # Create and activate a virtual environment from the root directory
    python -m venv venv
    source venv/bin/activate

    # Install dependencies from the backend requirements file
    pip install -r backend/requirements.txt
    ```

2.  **Install Playwright browsers:**

    After installing the Python packages, you need to install the browser binaries that Playwright uses.

    ```bash
    playwright install
    ```

    If you are on a headless Linux environment (like a CI/CD server), you might need to install additional system dependencies first:
    ```bash
    sudo playwright install-deps
    ```

#### 3. Running the Tests

1.  **Start the application:**

    The tests require the application, including the database and other services, to be running. The recommended way to do this is with `docker-compose`.

    From the root of the repository, run:
    ```bash
    docker-compose -f docker-compose-local.yml up -d
    ```
    **Note:** The application requires several environment variables to be set, including database credentials and secrets for Azure OpenAI (`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, etc.). Make sure these are properly configured in your environment. The tests will fail if the application is not running or not configured correctly.

2.  **Execute the tests:**

    To run all the tests, navigate to the root of the repository and use `pytest`:

    ```bash
    pytest playwright/tests/
    ```

    To run the tests with a visible browser, use the `--headed` flag:
    ```bash
    pytest playwright/tests/ --headed
    ```

    To run a specific test file:
    ```bash
    pytest playwright/tests/test_auth.py
    ```

    If you are running in a headless environment where `--headed` is required, you may need to use `xvfb-run`:
    ```bash
    xvfb-run pytest playwright/tests/ --headed
    ```
