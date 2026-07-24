def _routes(app):
    return {(method.upper(), path) for path, operations in app.openapi()["paths"].items() for method in operations}


def test_frontend_team_membership_routes_are_registered(client):
    routes = _routes(client.app)
    expected = {
        ("POST", "/api/teams/{team_id}/join"),
        ("GET", "/api/teams/{team_id}/requests"),
        ("POST", "/api/teams/{team_id}/approve/{user_id}"),
        ("POST", "/api/teams/{team_id}/reject/{user_id}"),
        ("GET", "/api/teams/{team_id}/roles"),
        ("POST", "/api/teams/{team_id}/roles"),
        ("DELETE", "/api/teams/{team_id}/roles/{role_id}"),
    }

    assert expected <= routes


def test_frontend_interaction_analytics_route_is_registered(client):
    assert ("GET", "/api/interactions/analytics/") in _routes(client.app)


def test_incompatible_duplicate_template_api_is_not_exposed(client):
    assert ("GET", "/api/admin/templates") not in _routes(client.app)


def test_frontend_resource_access_routes_are_registered(client):
    routes = _routes(client.app)
    expected = {
        ("GET", "/api/admin/{resource}/{resource_id}/access"),
        ("POST", "/api/admin/{resource}/{resource_id}/access"),
        ("DELETE", "/api/admin/{resource}/{resource_id}/access"),
        ("POST", "/api/admin/{resource}/{resource_id}/access/test"),
        ("POST", "/api/admin/{resource}/{resource_id}/owner"),
        ("POST", "/api/admin/templates/{resource_id}/visibility"),
    }
    assert expected <= routes
