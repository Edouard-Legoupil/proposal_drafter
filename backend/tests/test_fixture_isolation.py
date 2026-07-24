from sqlalchemy import inspect, text


def test_test_engines_are_isolated_and_match_membership_schema(test_engine_factory):
    first_engine = test_engine_factory()
    with first_engine.begin() as connection:
        connection.execute(text("INSERT INTO roles (id, name) VALUES (42, 'fixture sentinel')"))
    first_engine.dispose()

    second_engine = test_engine_factory()
    try:
        with second_engine.connect() as connection:
            role_count = connection.execute(
                text("SELECT COUNT(*) FROM roles WHERE name = 'fixture sentinel'")
            ).scalar_one()
        team_member_columns = {column["name"] for column in inspect(second_engine).get_columns("team_members")}

        assert role_count == 0
        assert "status" in team_member_columns
    finally:
        second_engine.dispose()
