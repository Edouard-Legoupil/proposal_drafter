import pytest
from playwright.sync_api import Page, expect


class TestRoleRequestApprovalWorkflow:
    """Test suite for Role Request Approval Workflow"""

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
