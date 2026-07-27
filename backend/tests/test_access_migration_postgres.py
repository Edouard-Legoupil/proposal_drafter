import os
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine


POSTGRES_URL = os.getenv("ACCESS_MIGRATION_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="ACCESS_MIGRATION_TEST_POSTGRES_URL is not configured",
)


def test_access_migration_is_idempotent_and_preserves_only_safe_assignments():
    schema = f"access_migration_{uuid.uuid4().hex}"
    migration = (Path(__file__).parents[2] / "db/migrations/20260727_access_management_compliance.sql").read_text()
    engine = create_engine(POSTGRES_URL)
    dbapi_error = engine.dialect.dbapi.Error
    raw_connection = engine.raw_connection()
    raw_connection.autocommit = True
    cursor = raw_connection.cursor()

    try:
        cursor.execute(f'CREATE SCHEMA "{schema}"')
        cursor.execute(f'SET search_path TO "{schema}"')
        cursor.execute(
            """
            CREATE TABLE roles (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            );
            CREATE TABLE teams (
                id UUID PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            );
            CREATE TABLE users (
                id UUID PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT,
                team_id UUID REFERENCES teams(id),
                requested_role_id INTEGER REFERENCES roles(id)
            );
            CREATE TABLE user_roles (
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
                PRIMARY KEY (user_id, role_id)
            );
            CREATE TABLE team_members (
                team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                PRIMARY KEY (team_id, user_id)
            );
            CREATE TABLE team_roles (
                team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
                role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
                PRIMARY KEY (team_id, role_id)
            );
            """
        )

        team_ids = [uuid.uuid4() for _ in range(4)]
        user_ids = {name: uuid.uuid4() for name in ("safe", "peer", "multi", "zero", "leader", "pending")}
        cursor.executemany(
            "INSERT INTO teams (id, name) VALUES (%s, %s)",
            [(team_id, f"Team {index}") for index, team_id in enumerate(team_ids, start=1)],
        )
        cursor.executemany(
            "INSERT INTO users (id, email, password, team_id) VALUES (%s, %s, 'secret', %s)",
            [
                (user_ids["safe"], "safe@example.org", team_ids[0]),
                (user_ids["peer"], "peer@example.org", team_ids[0]),
                (user_ids["multi"], "multi@example.org", team_ids[1]),
                (user_ids["zero"], "zero@example.org", None),
                (user_ids["leader"], "leader@example.org", team_ids[3]),
                (user_ids["pending"], "pending@example.org", team_ids[1]),
            ],
        )
        cursor.execute("INSERT INTO roles (name) VALUES " "('proposal writer'), ('project reviewer'), ('TEAM_LEADER')")
        cursor.execute("SELECT id, name FROM roles")
        role_ids = {name: role_id for role_id, name in cursor.fetchall()}
        cursor.executemany(
            "INSERT INTO team_members (team_id, user_id) VALUES (%s, %s)",
            [
                (team_ids[0], user_ids["safe"]),
                (team_ids[0], user_ids["peer"]),
                (team_ids[1], user_ids["multi"]),
                (team_ids[2], user_ids["multi"]),
                (team_ids[3], user_ids["leader"]),
                (team_ids[1], user_ids["pending"]),
            ],
        )
        cursor.execute("ALTER TABLE team_members ADD COLUMN status TEXT NOT NULL DEFAULT 'ACTIVE'")
        cursor.execute(
            "UPDATE team_members SET status = 'PENDING' WHERE user_id = %s",
            (user_ids["pending"],),
        )
        cursor.executemany(
            "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
            [
                (user_ids["safe"], role_ids["proposal writer"]),
                (user_ids["peer"], role_ids["proposal writer"]),
                (user_ids["multi"], role_ids["proposal writer"]),
                (user_ids["zero"], role_ids["project reviewer"]),
                (user_ids["leader"], role_ids["TEAM_LEADER"]),
            ],
        )
        cursor.executemany(
            "INSERT INTO team_roles (team_id, role_id) VALUES (%s, %s)",
            [
                (team_ids[1], role_ids["proposal writer"]),
                (team_ids[2], role_ids["TEAM_LEADER"]),
            ],
        )

        cursor.execute(migration)
        cursor.execute(migration)

        cursor.execute(
            "SELECT t.name, r.role_key FROM team_roles tr "
            "JOIN teams t ON t.id = tr.team_id JOIN roles r ON r.id = tr.role_id "
            "ORDER BY t.name, r.role_key"
        )
        assert cursor.fetchall() == [
            ("Team 1", "proposal writer"),
            ("Team 2", "proposal writer"),
        ]

        cursor.execute(
            "SELECT user_id, reason FROM legacy_access_assignment_ambiguities "
            "WHERE user_id IN (%s, %s) ORDER BY user_id",
            (user_ids["multi"], user_ids["zero"]),
        )
        ambiguity_users = {user_id for user_id, _reason in cursor.fetchall()}
        assert ambiguity_users == {user_ids["multi"], user_ids["zero"]}

        cursor.execute("SELECT COUNT(*) FROM user_roles")
        assert cursor.fetchone()[0] == 0
        cursor.execute("SELECT COUNT(*) FROM legacy_team_role_ambiguities")
        assert cursor.fetchone()[0] == 1
        cursor.execute("SELECT team_id, user_id FROM team_member_roles WHERE role_key = 'TEAM_LEADER'")
        assert cursor.fetchall() == [(team_ids[3], user_ids["leader"])]

        cursor.execute(
            "SELECT attnotnull FROM pg_attribute " "WHERE attrelid = 'team_roles'::regclass AND attname = 'role_key'"
        )
        assert cursor.fetchone()[0] is True
        cursor.execute(
            "SELECT COUNT(*) FROM pg_constraint "
            "WHERE conrelid = 'team_roles'::regclass "
            "AND conname = 'team_roles_role_identity_fkey' AND contype = 'f'"
        )
        assert cursor.fetchone()[0] == 1

        with pytest.raises(dbapi_error, match="active membership"):
            cursor.execute(
                "INSERT INTO team_member_roles (team_id, user_id, role_key, assigned_by) "
                "VALUES (%s, %s, 'TEAM_LEADER', %s)",
                (team_ids[1], user_ids["pending"], user_ids["leader"]),
            )

        cursor.execute(
            "UPDATE team_members SET status = 'REJECTED' WHERE team_id = %s AND user_id = %s",
            (team_ids[3], user_ids["leader"]),
        )
        cursor.execute(
            "SELECT COUNT(*) FROM team_member_roles WHERE team_id = %s AND user_id = %s",
            (team_ids[3], user_ids["leader"]),
        )
        assert cursor.fetchone()[0] == 0
    finally:
        try:
            cursor.execute("SET search_path TO public")
            cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        finally:
            cursor.close()
            raw_connection.close()
            engine.dispose()
