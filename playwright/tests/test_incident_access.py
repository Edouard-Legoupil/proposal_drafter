import pytest
from playwright.sync_api import Page, expect


class TestIncidentAccessManagement:
    """Test suite for Incident Access Management feature"""

    def test_admin_can_access_incident_access_panel(self, admin_page: Page):
        """Test that admin can navigate to incident access panel"""
        # Navigate to admin access management
        admin_page.click("text=Admin")
        admin_page.click("text=Access Management")

        # Verify incident tab exists
        expect(admin_page.locator("button:has-text('Incidents')")).to_be_visible()

        # Click on Incidents tab
        admin_page.click("text=Incidents")
        expect(admin_page).to_have_url("/admin/access/incidents/latest")
        expect(admin_page.locator("h2:has-text('Incidents')")).to_be_visible()

    def test_admin_can_view_incident_list(self, admin_page: Page):
        """Test that admin can view list of incidents"""
        # Navigate to incident access panel
        admin_page.goto("/admin/access/incidents/latest")

        # Verify incident table is visible
        expect(admin_page.locator("table")).to_be_visible()
        expect(admin_page.locator("th:has-text('Incident Type')")).to_be_visible()
        expect(admin_page.locator("th:has-text('Severity')")).to_be_visible()

    def test_admin_can_select_incident_for_access_management(self, admin_page: Page):
        """Test that admin can select an incident to manage access"""
        # Navigate to incident access panel
        admin_page.goto("/admin/access/incidents/latest")

        # Check if there are any incidents
        if admin_page.locator("tbody tr").count() > 0:
            # Click on first incident in the list
            first_incident = admin_page.locator("tbody tr").first
            first_incident.click()

            # Verify we're now viewing incident access details
            expect(admin_page).to_have_url("/admin/access/incidents/latest")
            expect(admin_page.locator("h2")).to_contain_text("Incident")
            expect(admin_page.locator("section:has-text('Access Grants')")).to_be_visible()
        else:
            pytest.skip("No incidents available for testing")

    def test_admin_can_grant_incident_access(self, admin_page: Page):
        """Test that admin can grant access to an incident"""
        # Navigate to a specific incident
        admin_page.goto("/admin/access/incidents/latest")

        # Check if there are any incidents
        if admin_page.locator("tbody tr").count() > 0:
            # Select first incident
            admin_page.locator("tbody tr").first.click()

            # Fill out grant form
            admin_page.select_option("select[name='subjectType']", "user")

            # Try to search for a user
            user_search = admin_page.locator("//input[@placeholder='Search users']")
            if user_search.count() > 0:
                user_search.first.fill("test")
                # Wait for search results
                admin_page.wait_for_timeout(1000)

                # Check some permissions
                admin_page.check("input[value='read']")

                # Submit the form
                admin_page.click("button:has-text('Save grant')")

                # Verify success message or error handling
                expect(admin_page.locator("text=Access granted")).to_be_visible()
            else:
                pytest.skip("User search not available")
        else:
            pytest.skip("No incidents available for testing")

    def test_admin_can_test_incident_access(self, admin_page: Page):
        """Test that admin can test effective access for a subject"""
        # Navigate to incident access details
        admin_page.goto("/admin/access/incidents/latest")

        # Check if there are any incidents
        if admin_page.locator("tbody tr").count() > 0:
            # Select first incident
            admin_page.locator("tbody tr").first.click()

            # Fill out tester form
            admin_page.select_option("select[name='tester.subjectType']", "user")

            # Try to search for a user
            user_search = admin_page.locator("//input[@placeholder='Search users']").nth(1)
            if user_search.count() > 0:
                user_search.fill("test")
                admin_page.wait_for_timeout(1000)

                # Run test
                admin_page.click("button:has-text('Run test')")

                # Verify test results
                expect(admin_page.locator("text=Test complete")).to_be_visible()
            else:
                pytest.skip("User search not available for tester")
        else:
            pytest.skip("No incidents available for testing")

    def test_admin_can_view_incident_audit_logs(self, admin_page: Page):
        """Test that admin can view audit logs for incident access changes"""
        # Navigate to incident access details
        admin_page.goto("/admin/access/incidents/latest")

        # Check if there are any incidents
        if admin_page.locator("tbody tr").count() > 0:
            # Select first incident
            admin_page.locator("tbody tr").first.click()

            # Scroll to audit section
            admin_page.locator("h3:has-text('Recent Audit Events')").scroll_into_view_if_needed()

            # Verify audit logs are visible
            expect(admin_page.locator("section:has-text('Recent Audit Events')")).to_be_visible()
        else:
            pytest.skip("No incidents available for testing")
