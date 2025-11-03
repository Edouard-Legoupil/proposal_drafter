import re
import uuid
import os
from playwright.sync_api import Playwright, sync_playwright, Page, expect


def test_user_registration():  # page: Page argument is removed when using sync_playwright() block
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
        email = "test_user@unhcr.org"
        password = "password123"
        name = "Test User"

        # Base URL for the application
        base_url = "http://localhost:8502"

        page.goto(f"{base_url}")

        # Take screenshot landing 
        page.screenshot(path="playwright/test-results/register_landing.png")

        # Navigate to the registration page

        page.get_by_test_id("register-link").click()
        # Assuming the registration page is at /register


        # Fill out the registration form
        # These are common labels, but might need adjustment
        page.get_by_label("Name").fill(name)
        page.get_by_label("Email").fill(email)
        page.get_by_label("Password").fill(password)
        # Select a team, security question and answer
        page.get_by_label("Team").select_option(index=1)
        page.get_by_label("Security Question").select_option(label="Favourite animal?")
        page.get_by_label("Answer").fill("Dog")

        # Create test-results directory if it doesn't exist
        os.makedirs("playwright/test-results", exist_ok=True)
        
        # Take screenshot before clicking register
        page.screenshot(path="playwright/test-results/register_page_before_submit.png")

        # Click the register button
        # Assuming the button has the text "Register"
        page.get_by_role("button", name="Register").click()



        # Expect to be redirected to the dashboard
        expect(page).to_have_url(re.compile(".*dashboard"))
        # The dashboard heading might be different
        expect(page.get_by_text("Draft Smart Project Proposals with AI, Curated Knowledge and Peer Review.")).to_be_visible()

        # Take screenshot after clicking register
        page.screenshot(path="playwright/test-results/register_page_after_submit.png")

        # Click the user menu to reveal the logout button, then click logout
        page.locator("button[popovertarget='ID_Chat_logoutPopover']").click()
        page.get_by_text("Logout").click()

        # Expect to be back on the login page
        expect(page).to_have_url(re.compile(".*login"))

        # Now, log in with the new user
        page.get_by_label("Email").fill(email)
        page.get_by_label("Password").fill(password)
        page.get_by_role("button", name="LOGIN").click()

        # Expect to be redirected to the dashboard
        expect(page).to_have_url(re.compile(".*dashboard"))


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




