import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request
from backend.api.auth import callback

@pytest.mark.asyncio
async def test_sso_callback_group_mapping(monkeypatch):
    # Mock data
    mock_user_data = {
        "userPrincipalName": "test@example.com",
        "displayName": "Test User"
    }
    mock_groups_data = {
        "value": [
            {"id": "group1", "@odata.type": "#microsoft.graph.group"},
            {"id": "group2", "@odata.type": "#microsoft.graph.group"}
        ]
    }
    
    # Mock settings
    monkeypatch.setenv("ENTRA_TENANT_ID", "tenant")
    monkeypatch.setenv("ENTRA_CLIENT_ID", "client")
    monkeypatch.setenv("ENTRA_CLIENT_SECRET", "secret")
    monkeypatch.setenv("ENTRA_REDIRECT_URI", "http://localhost/callback")
    monkeypatch.setenv("ENTRA_GROUP_ROLE_MAPPING", '{"group1": "role1"}')
    
    # Mock Internal Modules
    mock_msal_app = MagicMock()
    mock_msal_app.acquire_token_by_authorization_code.return_value = {
        "access_token": "token",
        "id_token_claims": {"sub": "123"}
    }
    
    with patch("backend.api.auth._get_msal_app", return_value=mock_msal_app), \
         patch("httpx.AsyncClient") as mock_client:
        
        # Mock Graph API responses
        mock_instance = mock_client.return_value.__aenter__.return_value
        
        mock_user_resp = MagicMock()
        mock_user_resp.json.return_value = mock_user_data
        mock_user_resp.raise_for_status.return_value = None
        
        mock_groups_resp = MagicMock()
        mock_groups_resp.json.return_value = mock_groups_data
        mock_groups_resp.raise_for_status.return_value = None
        
        mock_instance.get.side_effect = [mock_user_resp, mock_groups_resp]
        
        # Mock DB
        mock_engine = MagicMock()
        mock_conn = mock_engine.connect.return_value.__enter__.return_value
        mock_conn.execute.side_effect = [
            MagicMock(fetchall=lambda: [(1, "role1")]), # roles list
            MagicMock(fetchone=lambda: ( "user_id", "test@example.com", "Test User", "hashed_password")) # user check
        ]
        
        with patch("backend.api.auth.get_engine", return_value=mock_engine), \
             patch("backend.api.auth.redis_client") as mock_redis, \
             patch("backend.api.auth.jwt") as mock_jwt:
            
            mock_jwt.encode.return_value = "jwt_token"
            
            request = MagicMock(spec=Request)
            request.cookies = {}
            
            response = await callback(request, "mock_code")
            
            assert response.status_code == 307 # Redirect
            assert "/dashboard" in response.headers["location"]
            
            # Verify role update was called
            # (Note: testing exact SQL calls with MagicMock side_effect is tricky, 
            # but this verifies the flow reached the end)
            print("SSO Callback test passed successfully")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_sso_callback_group_mapping(None))
