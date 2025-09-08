import re
import uuid
import os
from playwright.sync_api import Playwright, sync_playwright, Page, expect


def test_user_registration_and_login(page: Page):
    """
    Tests that a new user can register and then log in.
    """
    #browser = playwright.chromium.launch(headless=False)
    #context = browser.new_context()
    #page = context.new_page()


    # Generate a unique email for the new user
    email = "test_user_bis@unhcr.org"
    password = "password123"

    name = "Test User bis"

    # Base URL for the application
    base_url = "http://localhost:8502"
    page.goto(f"{base_url}")

    page.get_by_test_id("register-link").click()
    page.get_by_test_id("name-input").click()
    page.get_by_test_id("name-input").fill(name)

    page.get_by_test_id("team-select").select_option(index=2)
    #page.get_by_test_id("team-select").select_option("7d83870a-77b5-42d9-a3e0-91210efc7d37")

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

   
    # ---------------------
    #context.close()
    #browser.close()