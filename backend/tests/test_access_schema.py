from dataclasses import FrozenInstanceError

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError


EXPECTED_COMPONENTS = {
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
    "system admin": None,
    "TEAM_LEADER": None,
}


def test_static_role_registry_is_complete_and_immutable():
    from backend.core.access_roles import ACCESS_ROLES, ROLE_REGISTRY

    assert ACCESS_ROLES is ROLE_REGISTRY
    assert {key: role.component for key, role in ROLE_REGISTRY.items()} == EXPECTED_COMPONENTS
    assert all(key == role.role_key for key, role in ROLE_REGISTRY.items())

    with pytest.raises(TypeError):
        ROLE_REGISTRY["new role"] = object()
    with pytest.raises(FrozenInstanceError):
        ROLE_REGISTRY["proposal writer"].component = "OtherWorkspace"


def test_sqlite_access_schema_has_normalized_columns(test_engine):
    inspector = inspect(test_engine)

    expected_columns = {
        "teams": {"id", "name", "description", "created_by", "created_at", "updated_at"},
        "team_members": {"team_id", "user_id", "status", "joined_at"},
        "roles": {"id", "name", "role_key", "component"},
        "team_roles": {"team_id", "role_key"},
        "team_member_roles": {"team_id", "user_id", "role_key", "assigned_by", "assigned_at"},
        "access_settings": {
            "id",
            "user_id",
            "team_id",
            "role_key",
            "key",
            "value",
            "created_by",
            "updated_at",
        },
    }

    for table_name, columns in expected_columns.items():
        actual = {column["name"] for column in inspector.get_columns(table_name)}
        assert columns <= actual, f"{table_name} is missing {columns - actual}"


def test_team_member_roles_only_accepts_team_leader(test_engine):
    with test_engine.begin() as connection:
        connection.execute(text("INSERT INTO teams (id, name) VALUES ('team-1', 'Team 1')"))
        connection.execute(
            text("INSERT INTO users (id, email, password) VALUES ('user-1', 'user@example.org', 'secret')")
        )
        connection.execute(
            text("INSERT INTO users (id, email, password) VALUES ('admin-1', 'admin@example.org', 'secret')")
        )
        connection.execute(text("INSERT INTO team_members (team_id, user_id) VALUES ('team-1', 'user-1')"))
        connection.execute(
            text(
                "INSERT INTO team_member_roles (team_id, user_id, role_key, assigned_by) "
                "VALUES ('team-1', 'user-1', 'TEAM_LEADER', 'admin-1')"
            )
        )

        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    "INSERT INTO team_member_roles (team_id, user_id, role_key, assigned_by) "
                    "VALUES ('team-1', 'user-1', 'proposal writer', 'admin-1')"
                )
            )


def test_team_members_rejects_unknown_status(test_engine):
    with test_engine.connect() as connection:
        with pytest.raises(IntegrityError):
            connection.execute(
                text("INSERT INTO team_members (team_id, user_id, status) " "VALUES ('team-1', 'user-1', 'UNKNOWN')")
            )


def test_team_roles_rejects_non_component_special_roles(test_engine):
    with test_engine.connect() as connection:
        connection.execute(text("INSERT INTO teams (id, name) VALUES ('team-1', 'Team 1')"))
        connection.execute(text("INSERT INTO roles (id, name, role_key) " "VALUES (1, 'TEAM_LEADER', 'TEAM_LEADER')"))

        with pytest.raises(IntegrityError):
            connection.execute(
                text("INSERT INTO team_roles (team_id, role_id, role_key) " "VALUES ('team-1', 1, 'TEAM_LEADER')")
            )


def test_access_settings_uniqueness_is_scoped_to_user_team_role_and_key(test_engine):
    statement = text(
        "INSERT INTO access_settings "
        "(user_id, team_id, role_key, key, value, created_by) "
        "VALUES ('user-1', 'team-1', 'proposal writer', 'region', :value, 'admin-1')"
    )

    with test_engine.connect() as connection:
        connection.execute(statement, {"value": "east"})
        with pytest.raises(IntegrityError):
            connection.execute(statement, {"value": "west"})
