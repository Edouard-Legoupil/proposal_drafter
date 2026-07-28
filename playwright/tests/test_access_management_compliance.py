"""End-to-end acceptance flow for team-scoped access management.

The flow requires a running application plus E2E_MEMBER_EMAIL and
E2E_MEMBER_PASSWORD for a non-admin account. It deliberately uses the public
HTTP contract so the same scenario can run locally and in CI.
"""

import os
import uuid

import pytest

pytestmark = pytest.mark.skipif(
    not (os.environ.get("E2E_MEMBER_EMAIL") and os.environ.get("E2E_MEMBER_PASSWORD")),
    reason="E2E member credentials are not configured",
)


@pytest.mark.admin
def test_team_role_and_grant_are_all_required(admin_page, config):
    member_email = os.environ.get("E2E_MEMBER_EMAIL")
    member_password = os.environ.get("E2E_MEMBER_PASSWORD")

    api = admin_page.request
    users = api.get("/api/admin/users").json()
    member = next((user for user in users if user["email"] == member_email), None)
    if member is None:
        pytest.skip("Configured E2E member does not exist")
    proposals = api.get("/api/admin/proposals/list").json()
    if not proposals:
        pytest.skip("An existing proposal is required for the object-grant flow")

    team_name = f"Access E2E {uuid.uuid4().hex[:8]}"
    team = api.post("/api/teams", data={"name": team_name, "description": "E2E acceptance team"}).json()
    team_id = team["id"]
    proposal_id = proposals[0]["id"]
    grant_id = None

    try:
        assert api.post(f"/api/teams/{team_id}/members/{member['id']}").ok
        assert api.put(f"/api/teams/{team_id}/leaders/{member['id']}").ok
        assert api.post(f"/api/teams/{team_id}/roles", data={"role_key": "proposal writer"}).ok
        grant_response = api.post(
            f"/api/admin/proposals/{proposal_id}/access",
            data={"subject_type": "team", "subject_id": team_id, "permissions": ["read"]},
        )
        assert grant_response.ok
        grant_id = grant_response.json()["grant"]["id"]

        member_context = admin_page.context.browser.new_context()
        member_page = member_context.new_page()
        member_page.goto(config["base_url"])
        continue_button = member_page.get_by_role("button", name="Continue Anyway")
        if continue_button.count():
            continue_button.click()
        member_page.get_by_test_id("identifier-input").fill(member_email)
        member_page.get_by_test_id("password-input").fill(member_password)
        member_page.get_by_test_id("submit-button").click()
        member_page.wait_for_url("**/dashboard**")

        switch_response = member_page.request.put("/api/profile/active-team", data={"team_id": team_id})
        assert switch_response.ok
        allowed = member_page.request.get(f"/api/proposals/{proposal_id}", headers={"X-Team-ID": team_id})
        assert allowed.ok

        assert api.delete(f"/api/teams/{team_id}/roles/proposal%20writer").ok
        denied = member_page.request.get(f"/api/proposals/{proposal_id}", headers={"X-Team-ID": team_id})
        assert denied.status in {403, 404}
        member_context.close()
    finally:
        if grant_id is not None:
            api.delete(f"/api/admin/proposals/{proposal_id}/access", data={"grant_id": grant_id})
        api.delete(f"/api/teams/{team_id}/leaders/{member['id']}")
        api.delete(f"/api/teams/{team_id}/members/{member['id']}")
        api.delete(f"/api/teams/{team_id}/roles/proposal%20writer")
        api.delete(f"/api/teams/{team_id}")
