"""Browser-only administrator access-management journeys."""

import os
import re
import sys
import uuid

import pytest
from playwright.sync_api import Page, expect


ROLE_COMPONENTS = {
    "proposal writer": "ProposalWorkspace",
    "project reviewer": "ReviewWorkspace",
    "knowledge manager donors": "DonorKnowledgeCards",
    "knowledge manager outcome": "OutcomeKnowledgeCards",
    "knowledge manager field context": "FieldContextKnowledgeCards",
    "access_template": "TemplateLibrary",
    "access_metrics": "MetricsDashboard",
    "access_incident": "IncidentDashboard",
    "access_quality_gate": "QualityGate",
    "ui_analysis": "InteractionAnalytics",
}


def _login(page: Page, config, email: str, password: str) -> None:
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("identifier-input").fill(email)
    page.get_by_test_id("password-input").fill(password)
    page.get_by_test_id("submit-button").click()
    expect(page).to_have_url(re.compile(r".*/dashboard(?:/.*)?$"))


def _login_admin(page: Page, config) -> None:
    _login(
        page,
        config,
        os.environ.get("ADMIN_EMAIL", "admin@unhcr.org"),
        os.environ.get("ADMIN_PASSWORD", "admin123"),
    )
    page.get_by_test_id("user-menu-button").click()
    expect(page.get_by_test_id("admin-button")).to_be_visible()
    page.get_by_test_id("admin-button").click()
    expect(page.get_by_role("heading", name="Access Management", exact=True)).to_be_visible()
    expect(page).to_have_url(re.compile(r".*/admin/access/user-access/latest$"))


def _logout(page: Page) -> None:
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("logout-button").click()
    expect(page).to_have_url(re.compile(r".*/login$"))


def _register_member(control_page: Page, config, suffix: str) -> tuple:
    browser = control_page.context.browser
    context = browser.new_context()
    try:
        page = context.new_page()
        page.set_default_timeout(config["default_timeout"])
        name = f"Access {suffix}"
        email = f"access_{suffix}@unhcr.org"
        password = "password123"

        page.goto(f"{config['base_url']}/login")
        page.get_by_test_id("register-link").click()
        page.get_by_test_id("name-input").fill(name)
        page.get_by_test_id("identifier-input").fill(email)
        page.get_by_test_id("password-input").fill(password)
        page.get_by_test_id("security-question-select").select_option(label="Favourite animal?")
        page.get_by_test_id("security-answer-input").fill("otter")
        page.get_by_test_id("acknowledgement-checkbox").check()
        page.get_by_test_id("submit-button").click()
        expect(page).to_have_url(re.compile(r".*/dashboard(?:/.*)?$"))
        _logout(page)
        return context, page, {"name": name, "email": email, "password": password}
    except Exception:
        context.close()
        raise


def _open_admin(page: Page) -> None:
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("admin-button").click()
    expect(page.get_by_role("heading", name="Access Management", exact=True)).to_be_visible()
    expect(page).to_have_url(re.compile(r".*/admin/access/user-access/latest$"))


def _open_admin_tab(page: Page, label: str, route: str) -> None:
    page.get_by_role("button", name=label, exact=True).click()
    expect(page).to_have_url(re.compile(rf".*/admin/access/{re.escape(route)}/latest$"))


def _create_team(page: Page, team_name: str) -> None:
    _open_admin_tab(page, "Teams", "teams")
    page.get_by_role("button", name="Create Team", exact=True).click()
    page.get_by_label("Team name").fill(team_name)
    page.get_by_label("Description").fill("Playwright administrator access journey")
    page.get_by_role("button", name="Create", exact=True).click()
    expect(page.get_by_role("heading", name=f"{team_name} Management", exact=True)).to_be_visible()


def _select_team(page: Page, team_name: str) -> None:
    _open_admin_tab(page, "Teams", "teams")
    page.get_by_placeholder("Search teams…").fill(team_name)
    page.get_by_role("button", name=f"Manage {team_name}", exact=True).click()
    expect(page.get_by_role("heading", name=f"{team_name} Management", exact=True)).to_be_visible()


def _delete_selected_team(page: Page, team_name: str) -> None:
    page.get_by_role("button", name="Delete team", exact=True).click()
    expect(page).to_have_url(re.compile(r".*/admin/access/teams/latest$"))
    expect(page.get_by_role("heading", name="Team Management", exact=True)).to_be_visible()
    page.get_by_placeholder("Search teams…").fill(team_name)
    expect(page.get_by_role("button", name=f"Manage {team_name}", exact=True)).to_have_count(0)


def _member_item(page: Page, member_email: str):
    return page.get_by_role("listitem").filter(has_text=member_email)


def _add_member(page: Page, member: dict) -> None:
    page.get_by_label("User to add").select_option(label=f"{member['name']} ({member['email']})")
    page.get_by_role("button", name="Add member", exact=True).click()
    expect(_member_item(page, member["email"])).to_be_visible()


def _remove_member(page: Page, member: dict) -> None:
    row = _member_item(page, member["email"])
    row.get_by_role("button", name="Remove member", exact=True).click()
    expect(_member_item(page, member["email"])).to_have_count(0)


def _assign_member_leader(page: Page, member: dict) -> None:
    row = _member_item(page, member["email"])
    row.get_by_role("button", name=f"Make {member['name']} team leader", exact=True).click()
    expect(_member_item(page, member["email"])).to_contain_text("TEAM_LEADER")


def _remove_member_leader(page: Page, member: dict) -> None:
    row = _member_item(page, member["email"])
    row.get_by_role("button", name=f"Remove {member['name']} team leader", exact=True).click()
    expect(_member_item(page, member["email"])).not_to_contain_text("TEAM_LEADER")


def _role_row(page: Page, role_name: str):
    return page.get_by_role("row").filter(has=page.get_by_role("cell", name=role_name, exact=True))


def _assert_role_mappings(page: Page) -> None:
    expect(page.get_by_text("TEAM_LEADER is assigned per member, not to the whole team.")).to_be_visible()
    for role_name, component in ROLE_COMPONENTS.items():
        row = _role_row(page, role_name)
        expect(row).to_contain_text(component)
        expect(row.get_by_role("button", name=f"Assign {role_name}", exact=True)).to_be_visible()
    expect(page.get_by_role("cell", name="TEAM_LEADER", exact=True)).to_have_count(0)
    expect(page.get_by_role("cell", name="system admin", exact=True)).to_have_count(0)
    expect(page.get_by_role("button", name=re.compile(r"Assign.*TEAM_LEADER", re.I))).to_have_count(0)
    expect(page.get_by_role("button", name="Assign system admin", exact=True)).to_have_count(0)


def _assign_team_role(page: Page, role_name: str) -> None:
    row = _role_row(page, role_name)
    row.get_by_role("button", name=f"Assign {role_name}", exact=True).click()
    expect(row.get_by_role("button", name=f"Remove {role_name}", exact=True)).to_be_visible()


def _remove_team_role(page: Page, role_name: str) -> None:
    row = _role_row(page, role_name)
    row.get_by_role("button", name=f"Remove {role_name}", exact=True).click()
    expect(row.get_by_role("button", name=f"Assign {role_name}", exact=True)).to_be_visible()


def _save_scoped_setting(page: Page, member: dict, team_name: str, key: str, value: str) -> None:
    _open_admin_tab(page, "Settings", "settings")
    page.get_by_label("User", exact=True).select_option(label=member["name"])
    page.get_by_label("Team", exact=True).select_option(label=team_name)
    page.get_by_label("Role", exact=True).select_option(label="knowledge manager donors")
    page.get_by_label("Setting key", exact=True).fill(key)
    page.get_by_label("Setting value", exact=True).fill(value)
    page.get_by_role("button", name="Save setting", exact=True).click()
    row = page.get_by_role("row").filter(has_text=key)
    expect(row).to_contain_text(value)


def _delete_scoped_setting(page: Page, key: str) -> None:
    row = page.get_by_role("row").filter(has_text=key)
    row.get_by_role("button", name="Delete", exact=True).click()
    expect(page.get_by_role("row").filter(has_text=key)).to_have_count(0)


def _switch_active_team(page: Page, team_name: str) -> None:
    page.get_by_label("Active team").select_option(label=team_name)
    expect(page.get_by_label("Active team").locator("option:checked")).to_have_text(team_name)


def _create_proposal(page: Page, title: str) -> None:
    page.get_by_test_id("new-proposal-button").click()
    expect(page).to_have_url(re.compile(r".*/chat$"))
    page.get_by_test_id("doc-type-concept-note-button").click()
    page.get_by_test_id("project-draft-short-name").fill(title)
    page.get_by_placeholder("Provide as much details as possible on your initial project idea!").fill(
        "Provide education and protection services for displaced children."
    )
    page.locator(".main-outcome__input-container").click()
    page.get_by_role("combobox", name="Main Outcome").fill("ed")
    page.get_by_role("option", name="OA11. Education").click()
    page.get_by_test_id("beneficiaries-profile").fill("Displaced children and their caregivers")
    page.get_by_test_id("potential-implementing-partner").fill("UNHCR and local partners")
    page.get_by_test_id("geographical-scope").select_option("One Country Operation")
    page.locator(".country-location-s__input-container").click()
    page.get_by_role("option", name="Afghanistan").click()
    page.locator(".budget-range__input-container").click()
    page.get_by_role("option", name="1M$").click()
    page.locator(".duration__input-container").click()
    page.get_by_role("option", name="12 months").click()
    page.locator(".targeted-donor__input-container").click()
    page.get_by_role("option", name="Sweden - Ministry for Foreign").click()
    page.get_by_role("button", name="Generate", exact=True).click()
    expect(page.get_by_test_id("edit-save-button-summary")).to_be_visible(timeout=600_000)


def _create_donor_knowledge_card(page: Page, summary: str) -> None:
    page.get_by_test_id("logo").click()
    page.get_by_test_id("sidebar-link-knowledge-all").click()
    page.get_by_test_id("new-knowledge-card-button").click()
    page.get_by_test_id("link-type-select").select_option("donor")
    page.locator(".kc-linked-item-select__input-container").click()
    page.get_by_role("combobox", name="Select Item*").fill("kor")
    page.get_by_role("option", name="Republic of Korea - Ministry").click()
    confirm = page.get_by_test_id("confirm-button")
    try:
        expect(confirm).to_be_visible(timeout=2_000)
        confirm.click()
    except AssertionError:
        pass
    page.get_by_test_id("summary-textarea").fill(summary)
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_test_id("identify-references-button").click()
    expect(page).to_have_url(re.compile(r".*/knowledge-card/[0-9a-f-]+$"))
    expect(page.get_by_test_id("loading-modal-overlay")).to_be_visible()
    expect(page.get_by_test_id("loading-modal-overlay")).to_have_count(0, timeout=400_000)
    page.get_by_test_id("logo").click()
    expect(page).to_have_url(re.compile(r".*/dashboard(?:/.*)?$"))


def _delete_proposal(page: Page, title: str) -> None:
    page.get_by_test_id("logo").click()
    page.get_by_test_id("sidebar-link-proposals-all").click()
    page.get_by_test_id("search-input").fill(title)
    card = page.get_by_test_id("project-card").filter(has_text=title)
    expect(card).to_be_visible()
    card.get_by_test_id("project-options-button").click()
    card.get_by_test_id("project-delete-button").click()
    expect(page.get_by_test_id("project-card").filter(has_text=title)).to_have_count(0)


def _delete_knowledge_card(page: Page, summary: str) -> None:
    page.get_by_test_id("logo").click()
    page.get_by_test_id("sidebar-link-knowledge-all").click()
    page.get_by_test_id("search-input").fill(summary)
    card = page.get_by_test_id("knowledge-card").filter(has_text=summary)
    expect(card).to_be_visible()
    delete_button = card.get_by_role("button", name="Delete", exact=True)
    try:
        expect(delete_button).to_be_visible(timeout=2_000)
    except AssertionError:
        # The current dashboard exposes knowledge-card deletion only for duplicate linked cards.
        return
    page.once("dialog", lambda dialog: dialog.accept())
    delete_button.click()
    expect(page.get_by_test_id("knowledge-card").filter(has_text=summary)).to_have_count(0)


def _cleanup_step(errors: list, label: str, operation) -> None:
    try:
        operation()
    except Exception as error:
        errors.append(f"{label}: {error}")


def _cleanup_resource_grant(page: Page, tab_label: str, route: str, resource_name: str, team_name: str) -> None:
    _select_admin_resource(page, tab_label, route, resource_name)
    _revoke_team_grant(page, team_name)


def _cleanup_scoped_setting(page: Page, setting_key: str) -> None:
    _open_admin(page)
    _open_admin_tab(page, "Settings", "settings")
    _delete_scoped_setting(page, setting_key)


def _select_team_for_cleanup(page: Page, team_name: str) -> None:
    _open_admin(page)
    _select_team(page, team_name)


def _submit_template_request(page: Page, request_name: str) -> None:
    page.get_by_test_id("sidebar-link-templates-all").click()
    page.get_by_test_id("new-template-button").click()
    expect(page.get_by_role("heading", name="Request New Donor Template", exact=True)).to_be_visible()
    page.get_by_label("Template Name *", exact=True).fill(request_name)
    page.get_by_text("Section Label *", exact=True).locator("..").get_by_role("textbox").fill("Project Summary")
    page.get_by_role("button", name="Submit Request", exact=True).click()
    expect(page).to_have_url(re.compile(r".*/dashboard/templates/all$"))
    expect(page.get_by_test_id("donor-template-card").filter(has_text=request_name)).to_be_visible()


def _approve_template_request(page: Page, request_name: str) -> None:
    page.get_by_test_id("logo").click()
    page.get_by_test_id("sidebar-link-templates-all").click()
    card = page.get_by_test_id("donor-template-card").filter(has_text=request_name)
    expect(card).to_contain_text("pending")
    card.click()
    expect(page.get_by_role("heading", name=request_name, exact=True)).to_be_visible()
    page.get_by_role("button", name="Approve", exact=True).click()
    expect(page.locator(".status-badge")).to_have_text("approved")


def _select_admin_resource(page: Page, tab_label: str, route: str, search_text: str) -> None:
    _open_admin(page)
    _open_admin_tab(page, tab_label, route)
    page.get_by_placeholder("Search resources…").fill(search_text)
    row = page.get_by_role("row").filter(has_text=search_text)
    expect(row).to_be_visible()
    row.get_by_role("button", name="Manage Access", exact=True).click()
    expect(page.get_by_role("button", name=re.compile(r"^All "))).to_be_visible()


def _pick_react_select(page: Page, form_selector: str, option_name: str) -> None:
    form = page.locator(form_selector)
    form.locator(".react-select__input").fill(option_name)
    page.get_by_role("option", name=option_name, exact=True).click()


def _save_team_grant(page: Page, team_name: str, permissions: list) -> None:
    audit_items = page.locator(".audit-panel .audit-list").get_by_role("listitem")
    previous_latest = audit_items.first.inner_text() if audit_items.count() else None
    _pick_react_select(page, ".grant-form", team_name)
    page.locator("#grant-permissions").select_option(permissions)
    page.get_by_role("button", name="Save Grant", exact=True).click()
    status = page.locator(".grant-section .status-message")
    expect(status).to_have_text(re.compile(r"^(Access granted|Grant saved)$"))
    expect(page.locator(".grants-list").get_by_role("listitem").filter(has_text=team_name)).to_be_visible()
    latest_audit = audit_items.first
    expect(latest_audit).to_contain_text("grant_updated")
    expect(latest_audit).to_contain_text("subject type: team")
    for permission in permissions:
        expect(latest_audit).to_contain_text(permission)
    if previous_latest is not None:
        expect(latest_audit).not_to_have_text(previous_latest)


def _test_team_access(page: Page, team_name: str, allowed: bool, operation: str = "GET") -> None:
    _pick_react_select(page, ".tester-form", team_name)
    page.locator(".tester-form").get_by_label("Operation").select_option(operation)
    page.locator(".tester-form").get_by_role("button", name="Run test", exact=True).click()
    result = page.locator(".tester-result")
    expect(result).to_contain_text("Allowed" if allowed else "Denied")


def _revoke_team_grant(page: Page, team_name: str) -> None:
    row = page.locator(".grants-list").get_by_role("listitem").filter(has_text=team_name)
    row.get_by_role("button", name="Revoke", exact=True).click()
    expect(page.locator(".grant-section .status-message")).to_have_text("Grant revoked")
    expect(page.locator(".grants-list").get_by_role("listitem").filter(has_text=team_name)).to_have_count(0)


def _assert_audit_timeline(page: Page, resource_name: str) -> None:
    expect(page.get_by_role("heading", name=resource_name, exact=True)).to_be_visible()
    audit = page.locator(".audit-panel")
    expect(audit.get_by_role("heading", name="Audit Timeline", exact=True)).to_be_visible()
    expect(audit.get_by_role("listitem").filter(has_text="grant_updated").first).to_be_visible()


def _assert_overview(page: Page, team_name: str, resource_names: list) -> None:
    _open_admin_tab(page, "Overview", "overview")
    expect(
        page.get_by_text("Effective access is team membership + active-team role + explicit team grant.")
    ).to_be_visible()
    page.get_by_label("Search permissions").fill(team_name)
    for component in ("ProposalWorkspace", "DonorKnowledgeCards", "TemplateLibrary"):
        expect(page.get_by_role("row").filter(has_text=f"Component: {component}")).to_contain_text(team_name)
    for resource_name in resource_names:
        expect(page.get_by_role("row").filter(has_text=resource_name)).to_contain_text("Granted")


def _select_first_template(page: Page) -> str:
    _open_admin(page)
    _open_admin_tab(page, "Templates", "templates")
    expect(page.locator(".resource-picker-loading")).to_have_count(0)
    if page.get_by_text("No resources found.", exact=True).is_visible():
        pytest.skip("A seeded template is required for the template grant journey")
    default_rows = page.locator(".resource-picker-table tbody tr").filter(has_text="Default")
    if default_rows.count() == 0:
        pytest.skip("A seeded template is required for the template grant journey")
    default_row = default_rows.first
    expect(default_row).to_be_visible()
    default_row.get_by_role("button", name="Manage Access", exact=True).click()
    expect(page.get_by_role("button", name="All templates", exact=True)).to_be_visible()
    heading = page.locator(".template-access > header h2")
    expect(heading).to_be_visible()
    return heading.inner_text()


@pytest.mark.admin
@pytest.mark.administrative
def test_admin_navigation_matches_current_access_management(page: Page, config) -> None:
    _login_admin(page, config)
    expect(page.get_by_role("heading", name="User Access", exact=True)).to_be_visible()
    expect(page.get_by_text("Direct user-role assignments are not supported.", exact=False)).to_be_visible()
    expect(page.get_by_role("table")).to_be_visible()
    expect(page.get_by_role("button", name=re.compile(r"assign|remove role", re.I))).to_have_count(0)

    panels = [
        ("Overview", "overview", "Permissions Overview"),
        ("User Access", "user-access", "User Access"),
        ("Teams", "teams", "Team Management"),
        ("Settings", "settings", "Scoped Settings"),
        ("Proposals", "proposals", "Proposals — Select a proposal to manage access"),
        ("Knowledge Cards", "knowledge-cards", "Knowledge Cards — Select a card to manage access"),
        ("Templates", "templates", "Templates — Select a template to manage access"),
    ]
    for label, route, heading in panels:
        _open_admin_tab(page, label, route)
        expect(page.get_by_role("heading", name=heading, exact=True)).to_be_visible()


@pytest.mark.admin
@pytest.mark.administrative
@pytest.mark.e2e
@pytest.mark.slow
def test_full_administrator_access_journey(page: Page, config) -> None:
    _login_admin(page, config)
    suffix = uuid.uuid4().hex[:8]
    team_name = f"Access Team {suffix}"
    proposal_title = f"Access proposal {suffix}"
    card_summary = f"Access donor card {suffix}"
    request_name = f"Access template {suffix}"
    setting_key = f"donor_setting_{suffix}"
    member_context, member_page, member = _register_member(page, config, suffix)
    required_roles = ["proposal writer", "knowledge manager donors", "access_template"]
    assigned_roles = []
    team_created = member_added = leader_assigned = setting_saved = False
    proposal_created = card_created = False
    granted_resources = []

    try:
        _create_team(page, team_name)
        team_created = True
        _assert_role_mappings(page)
        _add_member(page, member)
        member_added = True
        _assign_member_leader(page, member)
        leader_assigned = True
        for role_name in required_roles:
            _assign_team_role(page, role_name)
            assigned_roles.append(role_name)

        _save_scoped_setting(page, member, team_name, setting_key, f"enabled-{suffix}")
        setting_saved = True

        _login(member_page, config, member["email"], member["password"])
        _switch_active_team(member_page, team_name)
        proposal_created = True
        _create_proposal(member_page, proposal_title)
        card_created = True
        _create_donor_knowledge_card(member_page, card_summary)
        _submit_template_request(member_page, request_name)
        _logout(member_page)

        _approve_template_request(page, request_name)

        _select_admin_resource(page, "Proposals", "proposals", proposal_title)
        _save_team_grant(page, team_name, ["read", "edit"])
        granted_resources.append(("Proposals", "proposals", proposal_title))
        _test_team_access(page, team_name, allowed=True)
        _assert_audit_timeline(page, proposal_title)

        _select_admin_resource(page, "Knowledge Cards", "knowledge-cards", card_summary)
        _save_team_grant(page, team_name, ["read", "edit"])
        granted_resources.append(("Knowledge Cards", "knowledge-cards", card_summary))
        _test_team_access(page, team_name, allowed=True)
        _assert_audit_timeline(page, card_summary)

        _assert_overview(page, team_name, [proposal_title, card_summary])

        for tab_label, route, resource_name in list(granted_resources):
            _select_admin_resource(page, tab_label, route, resource_name)
            _revoke_team_grant(page, team_name)
            _test_team_access(page, team_name, allowed=False)
            granted_resources.remove((tab_label, route, resource_name))
    finally:
        primary_failure = sys.exc_info()[0] is not None
        cleanup_errors: list[str] = []
        for tab_label, route, resource_name in list(reversed(granted_resources)):
            _cleanup_step(
                cleanup_errors,
                f"revoke {resource_name}",
                lambda label=tab_label, path=route, name=resource_name: _cleanup_resource_grant(
                    page, label, path, name, team_name
                ),
            )
        if proposal_created or card_created:
            _cleanup_step(
                cleanup_errors,
                "member login for resource cleanup",
                lambda: _login(member_page, config, member["email"], member["password"]),
            )
        if proposal_created:
            _cleanup_step(cleanup_errors, "delete proposal", lambda: _delete_proposal(member_page, proposal_title))
        if card_created:
            _cleanup_step(
                cleanup_errors,
                "delete knowledge card",
                lambda: _delete_knowledge_card(member_page, card_summary),
            )
        if setting_saved:
            _cleanup_step(
                cleanup_errors,
                "delete scoped setting",
                lambda: _cleanup_scoped_setting(page, setting_key),
            )
        if team_created:
            _cleanup_step(
                cleanup_errors,
                "select team for cleanup",
                lambda: _select_team_for_cleanup(page, team_name),
            )
            for role_name in reversed(assigned_roles):
                _cleanup_step(
                    cleanup_errors,
                    f"remove {role_name}",
                    lambda role=role_name: _remove_team_role(page, role),
                )
            if leader_assigned:
                _cleanup_step(cleanup_errors, "remove team leader", lambda: _remove_member_leader(page, member))
            if member_added:
                _cleanup_step(cleanup_errors, "remove member", lambda: _remove_member(page, member))
            _cleanup_step(cleanup_errors, "delete team", lambda: _delete_selected_team(page, team_name))
        _cleanup_step(cleanup_errors, "close member context", member_context.close)
        # Template requests, registered users, and non-duplicate cards have no deletion control in the current frontend.
        if cleanup_errors:
            print("Cleanup issues: " + " | ".join(cleanup_errors))
            if not primary_failure:
                pytest.fail("UI cleanup failed: " + " | ".join(cleanup_errors))


@pytest.mark.admin
@pytest.mark.administrative
@pytest.mark.e2e
def test_admin_can_grant_seeded_template_to_team(page: Page, config) -> None:
    _login_admin(page, config)
    suffix = uuid.uuid4().hex[:8]
    team_name = f"Template Team {suffix}"
    member_context, _, member = _register_member(page, config, suffix)
    team_created = member_added = role_assigned = grant_saved = False

    try:
        _create_team(page, team_name)
        team_created = True
        _add_member(page, member)
        member_added = True
        _assign_team_role(page, "access_template")
        role_assigned = True
        template_name = _select_first_template(page)
        _save_team_grant(page, team_name, ["read"])
        grant_saved = True
        _test_team_access(page, team_name, allowed=True, operation="view")
        _assert_audit_timeline(page, template_name)
        _revoke_team_grant(page, team_name)
        grant_saved = False
        _test_team_access(page, team_name, allowed=False, operation="view")
    finally:
        primary_failure = sys.exc_info()[0] is not None
        cleanup_errors: list[str] = []
        if grant_saved:
            _cleanup_step(cleanup_errors, "revoke template grant", lambda: _revoke_team_grant(page, team_name))
        if team_created:
            _cleanup_step(
                cleanup_errors,
                "select template team for cleanup",
                lambda: _select_team_for_cleanup(page, team_name),
            )
            if role_assigned:
                _cleanup_step(
                    cleanup_errors,
                    "remove access_template",
                    lambda: _remove_team_role(page, "access_template"),
                )
            if member_added:
                _cleanup_step(cleanup_errors, "remove template member", lambda: _remove_member(page, member))
            _cleanup_step(cleanup_errors, "delete template team", lambda: _delete_selected_team(page, team_name))
        _cleanup_step(cleanup_errors, "close template member context", member_context.close)
        if cleanup_errors:
            print("Cleanup issues: " + " | ".join(cleanup_errors))
            if not primary_failure:
                pytest.fail("UI cleanup failed: " + " | ".join(cleanup_errors))
