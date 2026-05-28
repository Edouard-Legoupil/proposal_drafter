"""
Test suite for Administration

These tests verify that:
1. Admin

User Stories Covered:
- Admin role
"""

import pytest
from playwright.sync_api import Page, expect

# Import shared fixtures and helpers from central conftest


# ============================================================================
# Test: Navigate to Quality Review Page
# ============================================================================


@pytest.mark.admin
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


@pytest.mark.admin
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


@pytest.mark.admin
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


@pytest.mark.admin
def test_access_management_breadcrumbs(self, admin_page: Page):
    """Test that breadcrumbs work correctly in access management"""
    # Navigate to incident access
    admin_page.goto("/admin/access/incidents/latest")

    # Verify breadcrumb navigation
    expect(admin_page.locator("text=All incidents")).to_be_visible()

    # Click breadcrumb to go back
    admin_page.click("text=All incidents")
    expect(admin_page).to_have_url("/admin/access/incidents/latest")


@pytest.mark.admin
def test_access_management_error_handling(self, admin_page: Page):
    """Test error handling in access management"""
    # Try to navigate to non-existent incident
    admin_page.goto("/admin/access/incidents/nonexistent")

    # Verify error is handled gracefully
    expect(admin_page.locator("text=Incident not found")).to_be_visible()
    expect(admin_page.locator("text=Error")).to_be_visible()


@pytest.mark.admin
def test_admin_can_view_pending_role_requests(self, admin_page: Page):
    """Test that admin can view pending role requests"""
    # Navigate to user administration
    admin_page.goto("/admin/users")

    # Check if there are any pending role requests
    if admin_page.locator("h3:has-text('Pending Role Requests')").count() > 0:
        # Verify pending role requests section is visible
        expect(admin_page.locator("h3:has-text('Pending Role Requests')")).to_be_visible()
        expect(admin_page.locator("table")).to_contain_text("Requested Role")
    else:
        pytest.skip("No pending role requests section found")


@pytest.mark.admin
def test_admin_can_open_role_request_review_modal(self, admin_page: Page):
    """Test that admin can open the review modal for a role request"""
    # Navigate to user administration
    admin_page.goto("/admin/users")

    # Check if there are any pending role requests
    if admin_page.locator("tbody tr").count() > 0:
        # Click review button on first request
        first_request = admin_page.locator("tbody tr").first
        first_request.locator("button:has-text('Review')").click()

        # Verify modal appears
        expect(admin_page.locator("div.modal-overlay")).to_be_visible()
        expect(admin_page.locator("h3:has-text('Role Request Review')")).to_be_visible()

        # Verify request details are shown
        expect(admin_page.locator("text=User:")).to_be_visible()
        expect(admin_page.locator("text=Requested Role:")).to_be_visible()

        # Close modal
        admin_page.locator("button.modal-close").click()
    else:
        pytest.skip("No role requests available for testing")


@pytest.mark.admin
def test_admin_can_approve_role_request(self, admin_page: Page):
    """Test that admin can approve a role request"""
    # Navigate to user administration
    admin_page.goto("/admin/users")

    # Check if there are any pending role requests
    if admin_page.locator("tbody tr").count() > 0:
        # Open review modal
        admin_page.locator("tbody tr").first.locator("button:has-text('Review')").click()

        # Add admin note
        admin_note_field = admin_page.locator("textarea")
        if admin_note_field.count() > 0:
            admin_note_field.fill("Approved for project access")

        # Click approve button
        admin_page.click("button:has-text('Approve Request')")

        # Verify modal closes and success message appears
        expect(admin_page.locator("div.modal-overlay")).not_to_be_visible()
        expect(admin_page.locator("text=Role request approved")).to_be_visible()
    else:
        pytest.skip("No role requests available for testing")


@pytest.mark.admin
def test_admin_can_reject_role_request(self, admin_page: Page):
    """Test that admin can reject a role request"""
    # Navigate to user administration
    admin_page.goto("/admin/users")

    # Check if there are any pending role requests
    if admin_page.locator("tbody tr").count() > 0:
        # Open review modal
        admin_page.locator("tbody tr").first.locator("button:has-text('Review')").click()

        # Add admin note
        admin_note_field = admin_page.locator("textarea")
        if admin_note_field.count() > 0:
            admin_note_field.fill("Does not meet requirements")

        # Click reject button
        admin_page.click("button:has-text('Reject Request')")

        # Verify modal closes and success message appears
        expect(admin_page.locator("div.modal-overlay")).not_to_be_visible()
        expect(admin_page.locator("text=Role request rejected")).to_be_visible()
    else:
        pytest.skip("No role requests available for testing")


@pytest.mark.admin
def test_role_request_modal_has_proper_fields(self, admin_page: Page):
    """Test that role request modal has all required fields"""
    # Navigate to user administration
    admin_page.goto("/admin/users")

    # Check if there are any pending role requests
    if admin_page.locator("tbody tr").count() > 0:
        # Open review modal
        admin_page.locator("tbody tr").first.locator("button:has-text('Review')").click()

        # Verify all required fields are present
        expect(admin_page.locator("text=User:")).to_be_visible()
        expect(admin_page.locator("text=Email:")).to_be_visible()
        expect(admin_page.locator("text=Requested Role:")).to_be_visible()
        expect(admin_page.locator("text=Requested On:")).to_be_visible()
        expect(admin_page.locator("text=Admin Note")).to_be_visible()
        expect(admin_page.locator("textarea")).to_be_visible()
        expect(admin_page.locator("button:has-text('Reject Request')")).to_be_visible()
        expect(admin_page.locator("button:has-text('Approve Request')")).to_be_visible()

        # Close modal
        admin_page.locator("button.modal-close").click()
    else:
        pytest.skip("No role requests available for testing")


@pytest.mark.admin
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


@pytest.mark.admin
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


@pytest.mark.admin
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


@pytest.mark.admin
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


@pytest.mark.admin
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
