from unittest.mock import MagicMock, patch

import pytest
from fastapi import Request

from backend.api.auth import callback, sso_login


def _mock_request(*, cookies=None):
    request = MagicMock(spec=Request)
    request.cookies = cookies or {}
    request.headers = {"host": "localhost", "origin": "http://localhost:8503"}
    return request


@pytest.mark.asyncio
async def test_sso_login_sets_state_cookie_and_authorization_state():
    mock_msal_app = MagicMock()
    mock_msal_app.get_authorization_request_url.return_value = "https://login.example/authorize"

    with patch("backend.api.auth.ENTRA_TENANT_ID", "tenant"), patch(
        "backend.api.auth.ENTRA_CLIENT_ID", "client"
    ), patch("backend.api.auth.ENTRA_CLIENT_SECRET", "secret"), patch(
        "backend.api.auth.ENTRA_REDIRECT_URI", "https://app.example/api/callback"
    ), patch("backend.api.auth._get_msal_app", return_value=mock_msal_app), patch(
        "backend.api.auth.secrets.token_urlsafe", return_value="expected-state"
    ):
        response = await sso_login(_mock_request())

    assert response.status_code == 307
    assert "oauth_state=expected-state" in response.headers["set-cookie"]
    mock_msal_app.get_authorization_request_url.assert_called_once_with(
        scopes=["User.Read"],
        redirect_uri="https://app.example/api/callback",
        state="expected-state",
    )


@pytest.mark.asyncio
async def test_sso_login_requires_configured_redirect_uri():
    with patch("backend.api.auth.ENTRA_TENANT_ID", "tenant"), patch(
        "backend.api.auth.ENTRA_CLIENT_ID", "client"
    ), patch("backend.api.auth.ENTRA_CLIENT_SECRET", "secret"), patch(
        "backend.api.auth.ENTRA_REDIRECT_URI", None
    ), patch(
        "backend.api.auth._get_msal_app", return_value=MagicMock()
    ):
        response = await sso_login(_mock_request())

    assert response.status_code == 503


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("cookie_state", "query_state"),
    [(None, None), ("expected-state", "different-state")],
)
async def test_sso_callback_rejects_invalid_state(cookie_state, query_state):
    cookies = {"oauth_state": cookie_state} if cookie_state else {}

    with patch("backend.api.auth.ENTRA_TENANT_ID", "tenant"), patch(
        "backend.api.auth.ENTRA_CLIENT_ID", "client"
    ), patch("backend.api.auth.ENTRA_CLIENT_SECRET", "secret"), patch(
        "backend.api.auth.ENTRA_REDIRECT_URI", "https://app.example/api/callback"
    ):
        response = await callback(_mock_request(cookies=cookies), "mock_code", state=query_state)

    assert response.status_code == 400
    assert any(
        "oauth_state=" in header for header in response.headers.getlist("set-cookie")
    )


@pytest.mark.asyncio
async def test_sso_callback_group_mapping():
    mock_user_data = {
        "userPrincipalName": "test@example.com",
        "displayName": "Test User",
    }
    mock_msal_app = MagicMock()
    mock_msal_app.acquire_token_by_authorization_code.return_value = {
        "access_token": "token",
        "id_token_claims": {"sub": "123"},
    }

    with patch("backend.api.auth.ENTRA_TENANT_ID", "tenant"), patch(
        "backend.api.auth.ENTRA_CLIENT_ID", "client"
    ), patch("backend.api.auth.ENTRA_CLIENT_SECRET", "secret"), patch(
        "backend.api.auth.ENTRA_REDIRECT_URI", "https://app.example/api/callback"
    ), patch("backend.api.auth._get_msal_app", return_value=mock_msal_app), patch(
        "httpx.AsyncClient"
    ) as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_user_response = MagicMock()
        mock_user_response.json.return_value = mock_user_data
        mock_user_response.raise_for_status.return_value = None
        mock_instance.get.return_value = mock_user_response

        mock_engine = MagicMock()
        mock_role_connection = mock_engine.connect.return_value.__enter__.return_value
        mock_role_result = MagicMock()
        mock_role_result.fetchone.return_value = (1,)
        mock_role_connection.execute.return_value = mock_role_result

        mock_user_connection = mock_engine.begin.return_value.__enter__.return_value
        mock_user_result = MagicMock()
        mock_user_result.fetchone.return_value = ("user_id",)
        mock_user_connection.execute.return_value = mock_user_result

        with patch("backend.api.auth.get_engine", return_value=mock_engine), patch(
            "backend.api.auth.redis_client"
        ), patch("backend.api.auth.jwt") as mock_jwt:
            mock_jwt.encode.return_value = "jwt_token"
            request = _mock_request(cookies={"oauth_state": "expected-state"})

            response = await callback(request, "mock_code", state="expected-state")

    assert response.status_code == 307
    assert "/dashboard" in response.headers["location"]
    assert any(
        "oauth_state=" in header for header in response.headers.getlist("set-cookie")
    )
    mock_msal_app.acquire_token_by_authorization_code.assert_called_once_with(
        "mock_code",
        scopes=["User.Read"],
        redirect_uri="https://app.example/api/callback",
    )
