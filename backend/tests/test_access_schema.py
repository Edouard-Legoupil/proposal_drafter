from dataclasses import FrozenInstanceError
from pathlib import Path

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
        "teams": {
            "id",
            "name",
            "description",
            "created_by",
            "created_at",
            "updated_at",
        },
        "team_members": {"team_id", "user_id", "status", "joined_at"},
        "roles": {"id", "name", "role_key", "component"},
        "team_roles": {"team_id", "role_key"},
        "team_member_roles": {
            "team_id",
            "user_id",
            "role_key",
            "assigned_by",
            "assigned_at",
        },
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
        connection.execute(text("INSERT INTO roles (name, role_key) VALUES ('TEAM_LEADER', 'TEAM_LEADER')"))
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


def test_team_leader_assignment_requires_active_membership(test_engine):
    with test_engine.begin() as connection:
        connection.execute(text("INSERT INTO teams (id, name) VALUES ('team-1', 'Team 1')"))
        connection.execute(
            text(
                "INSERT INTO users (id, email, password) VALUES "
                "('user-1', 'user@example.org', 'secret'), "
                "('admin-1', 'admin@example.org', 'secret')"
            )
        )
        connection.execute(text("INSERT INTO roles (name, role_key) VALUES ('TEAM_LEADER', 'TEAM_LEADER')"))
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) " "VALUES ('team-1', 'user-1', 'PENDING')")
        )

        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    "INSERT INTO team_member_roles (team_id, user_id, role_key, assigned_by) "
                    "VALUES ('team-1', 'user-1', 'TEAM_LEADER', 'admin-1')"
                )
            )


def test_team_leader_assignment_cannot_move_to_inactive_membership(test_engine):
    with test_engine.begin() as connection:
        connection.execute(text("INSERT INTO teams (id, name) VALUES ('team-1', 'Team 1')"))
        connection.execute(
            text(
                "INSERT INTO users (id, email, password) VALUES "
                "('active-1', 'active@example.org', 'secret'), "
                "('pending-1', 'pending@example.org', 'secret'), "
                "('admin-1', 'admin@example.org', 'secret')"
            )
        )
        connection.execute(text("INSERT INTO roles (name, role_key) VALUES ('TEAM_LEADER', 'TEAM_LEADER')"))
        connection.execute(
            text(
                "INSERT INTO team_members (team_id, user_id, status) VALUES "
                "('team-1', 'active-1', 'ACTIVE'), "
                "('team-1', 'pending-1', 'PENDING')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO team_member_roles (team_id, user_id, role_key, assigned_by) "
                "VALUES ('team-1', 'active-1', 'TEAM_LEADER', 'admin-1')"
            )
        )

        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    "UPDATE team_member_roles SET user_id = 'pending-1' "
                    "WHERE team_id = 'team-1' AND user_id = 'active-1'"
                )
            )


def test_inactive_membership_removes_team_leader_assignment(test_engine):
    with test_engine.begin() as connection:
        connection.execute(text("INSERT INTO teams (id, name) VALUES ('team-1', 'Team 1')"))
        connection.execute(
            text(
                "INSERT INTO users (id, email, password) VALUES "
                "('user-1', 'user@example.org', 'secret'), "
                "('admin-1', 'admin@example.org', 'secret')"
            )
        )
        connection.execute(text("INSERT INTO roles (name, role_key) VALUES ('TEAM_LEADER', 'TEAM_LEADER')"))
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) " "VALUES ('team-1', 'user-1', 'ACTIVE')")
        )
        connection.execute(
            text(
                "INSERT INTO team_member_roles (team_id, user_id, role_key, assigned_by) "
                "VALUES ('team-1', 'user-1', 'TEAM_LEADER', 'admin-1')"
            )
        )

        connection.execute(
            text("UPDATE team_members SET status = 'REJECTED' " "WHERE team_id = 'team-1' AND user_id = 'user-1'")
        )

        assignment_count = connection.execute(
            text("SELECT COUNT(*) FROM team_member_roles " "WHERE team_id = 'team-1' AND user_id = 'user-1'")
        ).scalar_one()
        assert assignment_count == 0


def test_deleted_membership_removes_team_leader_assignment(test_engine):
    with test_engine.begin() as connection:
        connection.execute(text("INSERT INTO teams (id, name) VALUES ('team-1', 'Team 1')"))
        connection.execute(
            text(
                "INSERT INTO users (id, email, password) VALUES "
                "('user-1', 'user@example.org', 'secret'), "
                "('admin-1', 'admin@example.org', 'secret')"
            )
        )
        connection.execute(text("INSERT INTO roles (name, role_key) VALUES ('TEAM_LEADER', 'TEAM_LEADER')"))
        connection.execute(
            text("INSERT INTO team_members (team_id, user_id, status) " "VALUES ('team-1', 'user-1', 'ACTIVE')")
        )
        connection.execute(
            text(
                "INSERT INTO team_member_roles (team_id, user_id, role_key, assigned_by) "
                "VALUES ('team-1', 'user-1', 'TEAM_LEADER', 'admin-1')"
            )
        )

        connection.execute(text("DELETE FROM team_members WHERE team_id = 'team-1' AND user_id = 'user-1'"))

        assert connection.execute(text("SELECT COUNT(*) FROM team_member_roles")).scalar_one() == 0


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


def test_team_roles_requires_role_key(test_engine):
    with test_engine.connect() as connection:
        connection.execute(text("INSERT INTO teams (id, name) VALUES ('team-1', 'Team 1')"))
        connection.execute(
            text(
                "INSERT INTO roles (id, name, role_key, component) "
                "VALUES (1, 'proposal writer', 'proposal writer', 'ProposalWorkspace')"
            )
        )

        with pytest.raises(IntegrityError):
            connection.execute(text("INSERT INTO team_roles (team_id, role_id) VALUES ('team-1', 1)"))


def test_team_roles_rejects_mismatched_role_identity(test_engine):
    with test_engine.connect() as connection:
        connection.execute(text("INSERT INTO teams (id, name) VALUES ('team-1', 'Team 1')"))
        connection.execute(
            text(
                "INSERT INTO roles (id, name, role_key, component) VALUES "
                "(1, 'proposal writer', 'proposal writer', 'ProposalWorkspace'), "
                "(2, 'project reviewer', 'project reviewer', 'ReviewWorkspace')"
            )
        )

        with pytest.raises(IntegrityError):
            connection.execute(
                text("INSERT INTO team_roles (team_id, role_id, role_key) " "VALUES ('team-1', 1, 'project reviewer')")
            )


def test_sqlite_foreign_keys_are_enabled(test_engine):
    with test_engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1


def test_migration_reports_multi_team_assignments_even_if_one_team_already_has_role():
    migration = (Path(__file__).parents[2] / "db/migrations/20260727_access_management_compliance.sql").read_text()

    assert "am.team_ids IS NULL OR cardinality(am.team_ids) <> 1 OR safe.user_id IS NULL" in migration


def test_migration_contract_scopes_constraints_and_installs_membership_triggers():
    root = Path(__file__).parents[2]
    migration = (root / "db/migrations/20260727_access_management_compliance.sql").read_text()
    bootstrap = (root / "db/database-setup.sql").read_text()

    assert "SELECT 1 FROM pg_constraint WHERE conname" not in migration
    assert migration.count("conrelid =") >= 6
    for sql in (migration, bootstrap):
        assert "enforce_active_team_leader_membership" in sql
        assert "remove_inactive_team_leader_assignment" in sql
        assert "tm.status = 'ACTIVE'" in sql
        assert "FOR UPDATE" in sql


def test_bootstrap_settings_inheritance_requires_active_membership():
    bootstrap = (Path(__file__).parents[2] / "db/database-setup.sql").read_text()

    inherited_function = bootstrap.split("CREATE OR REPLACE FUNCTION get_inherited_settings_for_user", 1)[1].split(
        "CREATE OR REPLACE FUNCTION apply_inherited_settings_to_user", 1
    )[0]
    apply_function = bootstrap.split("CREATE OR REPLACE FUNCTION apply_inherited_settings_to_user", 1)[1].split(
        "CREATE OR REPLACE FUNCTION handle_team_settings_inheritance", 1
    )[0]
    trigger_function = bootstrap.split("CREATE OR REPLACE FUNCTION handle_team_settings_inheritance", 1)[1].split(
        "CREATE TRIGGER team_settings_inheritance_trigger", 1
    )[0]
    settings_view = bootstrap.split("CREATE OR REPLACE VIEW user_effective_settings", 1)[1].split(
        "CREATE TABLE IF NOT EXISTS user_role_requests", 1
    )[0]

    assert "status = 'ACTIVE'" in inherited_function
    assert "status = 'ACTIVE'" in apply_function
    assert "status = 'ACTIVE'" in trigger_function
    assert "tm.status = 'ACTIVE'" in settings_view


def test_bootstrap_system_inherited_settings_are_dynamically_gated():
    bootstrap = (Path(__file__).parents[2] / "db/database-setup.sql").read_text()

    inherited_function = bootstrap.split("CREATE OR REPLACE FUNCTION get_inherited_settings_for_user", 1)[1].split(
        "CREATE OR REPLACE FUNCTION apply_inherited_settings_to_user", 1
    )[0]
    settings_view = bootstrap.split("CREATE OR REPLACE VIEW user_effective_settings", 1)[1].split(
        "CREATE TABLE IF NOT EXISTS user_role_requests", 1
    )[0]

    for sql in (inherited_function, settings_view):
        assert "approved_by" in sql
        assert "approved_by IS NOT NULL" in sql
        assert "'system'" not in sql
        assert "tm.status = 'ACTIVE'" in sql
        assert "JOIN team_settings" in sql


def test_team_settings_sql_uses_uuid_safe_system_provenance():
    root = Path(__file__).parents[2]

    for path in (root / "db/database-setup.sql", root / "db/migrations/20240818_add_team_settings.sql"):
        sql = path.read_text()
        assert "'system' -- Mark as system-approved" not in sql


def _normalized_function_definition(sql: str, name: str) -> str:
    start = sql.index(f"CREATE OR REPLACE FUNCTION {name}")
    end_marker = "$$ LANGUAGE plpgsql;"
    end = sql.index(end_marker, start) + len(end_marker)
    return " ".join(sql[start:end].split())


def _normalized_effective_settings_view(sql: str) -> str:
    start = sql.index("CREATE OR REPLACE VIEW user_effective_settings")
    end = sql.index("\n\n--", start)
    return " ".join(sql[start:end].split())


def test_current_access_migration_refreshes_legacy_team_settings_policy():
    root = Path(__file__).parents[2]
    bootstrap = (root / "db/database-setup.sql").read_text()
    migration = (root / "db/migrations/20260727_access_management_compliance.sql").read_text()

    for function_name in (
        "get_inherited_settings_for_user",
        "apply_inherited_settings_to_user",
        "handle_team_settings_inheritance",
    ):
        assert _normalized_function_definition(migration, function_name) == _normalized_function_definition(
            bootstrap, function_name
        )

    assert _normalized_effective_settings_view(migration) == _normalized_effective_settings_view(bootstrap)
    assert "approved_by IS NOT NULL" in migration
    assert "NULL -- NULL provenance marks system-materialized inheritance" in migration
    assert migration.count("status = 'ACTIVE'") >= 3


def test_current_settings_functions_use_postgresql_uuid_types():
    root = Path(__file__).parents[2]
    bootstrap = (root / "db/database-setup.sql").read_text()
    migration = (root / "db/migrations/20260727_access_management_compliance.sql").read_text()

    for sql in (bootstrap, migration):
        inherited = _normalized_function_definition(sql, "get_inherited_settings_for_user")
        apply_inherited = _normalized_function_definition(sql, "apply_inherited_settings_to_user")
        assert "get_inherited_settings_for_user(user_id UUID)" in inherited
        assert "source_id UUID" in inherited
        assert "apply_inherited_settings_to_user(user_id UUID)" in apply_inherited
        assert "user_id VARCHAR" not in inherited
        assert "user_id VARCHAR" not in apply_inherited
        assert "WHERE user_id =" not in inherited
        assert "WHERE user_id =" not in apply_inherited

    assert "DROP FUNCTION IF EXISTS get_inherited_settings_for_user(VARCHAR);" in migration
    assert "DROP FUNCTION IF EXISTS apply_inherited_settings_to_user(VARCHAR);" in migration


def test_access_settings_uniqueness_is_scoped_to_user_team_role_and_key(test_engine):
    statement = text(
        "INSERT INTO access_settings "
        "(user_id, team_id, role_key, key, value, created_by) "
        "VALUES ('user-1', 'team-1', 'proposal writer', 'region', :value, 'admin-1')"
    )

    with test_engine.connect() as connection:
        connection.execute(text("INSERT INTO teams (id, name) VALUES ('team-1', 'Team 1')"))
        connection.execute(
            text(
                "INSERT INTO users (id, email, password) VALUES "
                "('user-1', 'user@example.org', 'secret'), "
                "('admin-1', 'admin@example.org', 'secret')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO roles (name, role_key, component) "
                "VALUES ('proposal writer', 'proposal writer', 'ProposalWorkspace')"
            )
        )
        connection.execute(statement, {"value": '"east"'})
        with pytest.raises(IntegrityError):
            connection.execute(statement, {"value": '"west"'})


def test_access_settings_requires_json_value(test_engine):
    with test_engine.begin() as connection:
        connection.execute(text("INSERT INTO teams (id, name) VALUES ('team-1', 'Team 1')"))
        connection.execute(
            text(
                "INSERT INTO users (id, email, password) VALUES "
                "('user-1', 'user@example.org', 'secret'), "
                "('admin-1', 'admin@example.org', 'secret')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO roles (name, role_key, component) "
                "VALUES ('proposal writer', 'proposal writer', 'ProposalWorkspace')"
            )
        )

        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    "INSERT INTO access_settings "
                    "(user_id, team_id, role_key, key, value, created_by) VALUES "
                    "('user-1', 'team-1', 'proposal writer', 'region', 'not-json', 'admin-1')"
                )
            )
