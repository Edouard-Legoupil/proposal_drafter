import re
import uuid
import os
from playwright.sync_api import Playwright, sync_playwright, Page, expect


def test_user_registration_and_login():  # page: Page argument is removed when using sync_playwright() block
    """
    Tests that a new user can register and then log in, with video recording.
    """
    # Base URL for the application
    base_url = "http://localhost:8502"


    # Define where the video will be saved.
    VIDEO_DIR = "playwright/test-results/videos"

    # Ensure the directory exists
    os.makedirs(VIDEO_DIR, exist_ok=True)


    # Use the sync_playwright context manager to launch and control the browser lifecycle
    with sync_playwright() as playwright:
        # Launch browser (use chromium, firefox, or webkit)
        browser = playwright.chromium.launch(headless=False, slow_mo=500)
        
        # 2. Create a new context and set the video recording directory
        # Video recording starts now.
        context = browser.new_context(
            record_video_dir=VIDEO_DIR,
            # Set viewport to a high resolution (e.g., Full HD) for maximum screen space
            viewport={"width": 1920, "height": 1080}, 
            # Set the video output size to match the viewport for best quality
            record_video_size={"width": 1920, "height": 1080}
        )
        
        # 3. Get a new page from the context
        page = context.new_page()

        # Generate a unique email for the new user
        email = "test_user_bis@unhcr.org"   
        name = "Test User bis"
        password = "password123"

        page.goto(f"{base_url}")

        page.get_by_test_id("register-link").click()
        page.get_by_test_id("name-input").click()
        page.get_by_test_id("name-input").fill(name)

        page.get_by_test_id("team-select").select_option(index=2)

        page.get_by_test_id("email-input").click()
        page.get_by_test_id("email-input").fill(email)

        page.get_by_test_id("password-input").click()
        page.get_by_test_id("password-input").fill(password)

        page.get_by_test_id("security-question-select").select_option("Favourite animal?")
        page.get_by_test_id("security-answer-input").click()
        page.get_by_test_id("security-answer-input").fill("Dog")
        
        page.get_by_test_id("submit-button").click()
        page.get_by_test_id("user-menu-button").click()
        page.get_by_test_id("logout-button").click()

 
        # -------------------
        # End of Test Logic
        # -------------------

        # 4. Close the context and browser
        # The video file is saved when the context closes.
        video_path = page.video.path()
        context.close()
        browser.close()
        
        # Optional: Rename the file to something more descriptive
        new_video_path = os.path.join(VIDEO_DIR, "user_registration.webm")
        os.rename(video_path, new_video_path)
        print(f"Video saved successfully to: {new_video_path}")


# To run this test, you might need to use a test runner like pytest, or uncomment 
# and adjust the last part to call the function directly if you aren't using one.
# For example:
# test_user_registration_and_login()