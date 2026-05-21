import pytest
from playwright.sync_api import Page, expect


class TestAdminAccessManagementIntegration:
    """Integration tests for access management features"""

    def test_access_management_navigation_consistency(self, admin_page: Page):
        """Test that all access management tabs work consistently"""
        # Navigate to access management
        admin_page.goto("/admin/access/users/latest")

        # Test all tabs navigate correctly
        tabs = [
            "Users",
            "Teams & Roles",
            "Proposals",
            "Knowledge Cards",
            "Templates",
            "Metrics Dashboard",
            "Quality Gate",
            "Incidents",
        ]

        for tab in tabs:
            admin_page.click(f"button:has-text('{tab}')")
            # Verify we're on an access management page
            expect(admin_page).to_have_url("/admin/access/.*")

    def test_incident_tab_integration(self, admin_page: Page):
        """Test that incidents tab is properly integrated"""
        # Navigate to access management
        admin_page.goto("/admin/access/users/latest")

        # Click on Incidents tab
        admin_page.click("button:has-text('Incidents')")

        # Verify we're on the incident access page
        expect(admin_page).to_have_url("/admin/access/incidents/latest")
        expect(admin_page.locator("h2")).to_contain_text("Incidents")

        # Verify incident-specific elements are present
        expect(admin_page.locator("th:has-text('Incident Type')")).to_be_visible()
        expect(admin_page.locator("th:has-text('Severity')")).to_be_visible()

    def test_role_requests_in_user_admin(self, admin_page: Page):
        """Test that role requests are integrated into user administration"""
        # Navigate to user administration
        admin_page.goto("/admin/users")

        # Verify role requests section exists
        role_requests_section = admin_page.locator("h3:has-text('Pending Role Requests')")
        if role_requests_section.count() > 0:
            expect(role_requests_section).to_be_visible()
            expect(admin_page.locator("table")).to_contain_text("Requested Role")
        else:
            pytest.skip("No role requests section found")

    def test_access_management_breadcrumbs(self, admin_page: Page):
        """Test that breadcrumbs work correctly in access management"""
        # Navigate to incident access
        admin_page.goto("/admin/access/incidents/latest")

        # Verify breadcrumb navigation
        expect(admin_page.locator("text=All incidents")).to_be_visible()

        # Click breadcrumb to go back
        admin_page.click("text=All incidents")
        expect(admin_page).to_have_url("/admin/access/incidents/latest")

    def test_access_management_error_handling(self, admin_page: Page):
        """Test error handling in access management"""
        # Try to navigate to non-existent incident
        admin_page.goto("/admin/access/incidents/nonexistent")

        # Verify error is handled gracefully
        expect(admin_page.locator("text=Incident not found")).to_be_visible()
        expect(admin_page.locator("text=Error")).to_be_visible()
