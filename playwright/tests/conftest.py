"""
Pytest configuration and fixtures for Playwright end-to-end tests.

This module provides shared fixtures and configuration for the Proposal Drafter
application test suite.
"""

import re
import os
import pytest
import uuid
from typing import Optional, Dict, Any
from playwright.sync_api import (
    sync_playwright,
)


# ============================================================================
# Configuration Constants
# ============================================================================

# Default configuration - can be overridden by environment variables
DEFAULT_CONFIG = {
    "base_url": "http://localhost:8502",
    "headless": False,  # Set to True for CI/CD
    "slow_mo": 500,  # Milliseconds to slow down operations for visibility
    "viewport_width": 1920,
    "viewport_height": 1080,
    "video_dir": "playwright/test-results/videos",
    "screenshot_dir": "playwright/test-results/screenshots",
    "video_size": {"width": 1920, "height": 1080},
    "default_timeout": 30000,  # 30 seconds default timeout
    "long_timeout": 600000,  # 10 minutes for long operations (e.g., generation)
}


def get_config() -> Dict[str, Any]:
    """Get configuration with environment variable overrides."""
    config = DEFAULT_CONFIG.copy()

    # Override from environment variables
    config["base_url"] = os.environ.get("PLAYWRIGHT_BASE_URL", config["base_url"])
    config["headless"] = os.environ.get("PLAYWRIGHT_HEADLESS", "").lower() in (
        "true",
        "1",
        "yes",
    )
    slow_mo_env = os.environ.get("PLAYWRIGHT_SLOW_MO", str(config["slow_mo"]))
    config["slow_mo"] = int(slow_mo_env) if slow_mo_env else 0

    return config


# ============================================================================
# Test User Configuration
# ============================================================================


class TestUser:
    """Represents a test user with credentials and metadata."""

    def __init__(self, email: str, password: str, name: str, team_index: int = 1):
        self.email = email
        self.password = password
        self.name = name
        self.team_index = team_index
        self.security_question = "Favourite animal?"
        self.security_answer = "Dog"

    @classmethod
    def generate_unique(cls, prefix: str = "test_user", team_index: int = 1) -> "TestUser":
        """Generate a test user with unique email."""
        unique_id = uuid.uuid4().hex[:8]
        return cls(
            email=f"{prefix}_{unique_id}@unhcr.org",
            password="password123",
            name=f"{prefix.title().replace('_', ' ')} {unique_id[:4]}",
            team_index=team_index,
        )


# Predefined test users for consistent testing
TEST_USERS = {
    "primary": TestUser(
        email="test_user@unhcr.org",
        password="password123",
        name="Test User",
        team_index=1,
    ),
    "secondary": TestUser(
        email="test_user_bis@unhcr.org",
        password="password123",
        name="Test User Bis",
        team_index=2,
    ),
    "tertiary": TestUser(
        email="test_user_ter@unhcr.org",
        password="password123",
        name="Test User Ter",
        team_index=1,
    ),
}


# ============================================================================
# Pytest Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def config():
    """Session-scoped configuration fixture."""
    return get_config()


@pytest.fixture(scope="session")
def playwright():
    """Session-scoped Playwright instance."""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright, config):
    """Session-scoped browser instance."""
    browser = playwright.chromium.launch(headless=config["headless"], slow_mo=config["slow_mo"])
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def context(browser, config, request):
    """Function-scoped browser context with optional video recording."""
    # Check if the test requests video recording
    record_video = getattr(request, "param", None)

    # Ensure directories exist
    os.makedirs(config["video_dir"], exist_ok=True)
    os.makedirs(config["screenshot_dir"], exist_ok=True)

    context = browser.new_context(
        viewport={
            "width": config["viewport_width"],
            "height": config["viewport_height"],
        },
        record_video_dir=config["video_dir"] if record_video else None,
        record_video_size=config["video_size"] if record_video else None,
    )

    yield context

    # Save video if recording was enabled
    if record_video and context.pages:
        for page in context.pages:
            try:
                video_path = page.video.path()
                if video_path and os.path.exists(video_path):
                    # Rename video to test-specific name
                    test_name = request.node.name
                    safe_name = "".join(c if c.isalnum() else "_" for c in test_name)
                    new_video_path = os.path.join(config["video_dir"], f"{safe_name}_{uuid.uuid4().hex[:8]}.webm")
                    os.rename(video_path, new_video_path)
                    print(f"\n[VIDEO] Saved to: {new_video_path}")
            except Exception as e:
                print(f"\n[WARNING] Could not save video: {e}")

    context.close()


@pytest.fixture(scope="function")
def page(context, config):
    """Function-scoped page instance."""
    page = context.new_page()
    page.set_default_timeout(config["default_timeout"])
    yield page
    page.close()


# ============================================================================
# Authentication Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def logged_in_page(page, config, user=None):
    """
    Fixture that provides a page with a logged-in user.

    Args:
        page: The page fixture
        config: The config fixture
        user: Optional TestUser object. If None, uses primary test user.

    Returns:
        The authenticated page
    """
    if user is None:
        user = TEST_USERS["primary"]

    # Navigate to login page
    page.goto(f"{config['base_url']}/login")

    # Log in
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("submit-button").click()

    # Verify we're on the dashboard
    page.wait_for_url(re.compile(".*dashboard"))

    return page


@pytest.fixture(scope="function")
def registered_user(context, config, user=None):
    """
    Fixture that registers and returns a new user.

    Args:
        context: Browser context
        config: Configuration
        user: Optional TestUser object. If None, generates a unique user.

    Returns:
        Tuple of (page, TestUser) where page is logged in as the new user
    """
    if user is None:
        user = TestUser.generate_unique()

    page = context.new_page()
    page.set_default_timeout(config["default_timeout"])

    # Navigate to homepage
    page.goto(config["base_url"])

    # Go to registration
    page.get_by_test_id("register-link").click()

    # Fill registration form
    page.get_by_test_id("name-input").fill(user.name)
    page.get_by_test_id("team-select").select_option(index=user.team_index)
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("security-question-select").select_option(user.security_question)
    page.get_by_test_id("security-answer-input").fill(user.security_answer)

    # Submit
    page.get_by_test_id("submit-button").click()

    # Wait for dashboard
    page.wait_for_url(re.compile(".*dashboard"))

    yield page, user

    # Cleanup: logout and close page
    try:
        page.get_by_test_id("user-menu-button").click()
        page.get_by_test_id("logout-button").click()
        page.wait_for_url(re.compile(".*login"))
    except Exception:
        pass  # Ignore cleanup errors
    finally:
        page.close()


# ============================================================================
# Helper Functions
# ============================================================================


def take_screenshot(page, name: str, config: Optional[Dict] = None):
    """Take a screenshot with a standardized name."""
    if config is None:
        config = get_config()

    os.makedirs(config["screenshot_dir"], exist_ok=True)
    safe_name = "".join(c if c.isalnum() else "_" for c in name)
    timestamp = uuid.uuid4().hex[:8]
    path = os.path.join(config["screenshot_dir"], f"{safe_name}_{timestamp}.png")
    page.screenshot(path=path)
    print(f"\n[SCREENSHOT] Saved to: {path}")
    return path


def wait_for_element(page, test_id: str, timeout: Optional[int] = None, state: str = "visible"):
    """Wait for an element to be in the specified state."""
    config = get_config()
    timeout = timeout or config["default_timeout"]

    try:
        if state == "visible":
            page.get_by_test_id(test_id).wait_for(timeout=timeout, state="visible")
        elif state == "hidden":
            page.get_by_test_id(test_id).wait_for(timeout=timeout, state="hidden")
        elif state == "attached":
            page.get_by_test_id(test_id).wait_for(timeout=timeout, state="attached")
        return True
    except Exception as e:
        print(f"\n[WARNING] Element {test_id} not found in state {state}: {e}")
        return False


def expect_url(page, pattern: str, timeout: Optional[int] = None):
    """Expect the page URL to match a pattern."""
    config = get_config()
    timeout = timeout or config["default_timeout"]
    page.wait_for_url(re.compile(".*" + pattern), timeout=timeout)
