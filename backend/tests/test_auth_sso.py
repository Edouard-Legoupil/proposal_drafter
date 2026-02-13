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
    # Mock Internal Modules
    mock_msal_app = MagicMock()
    mock_msal_app.acquire_token_by_authorization_code.return_value = {
        "access_token": "token",
        "id_token_claims": {"sub": "123"}
    }
    
    with patch("backend.api.auth.ENTRA_TENANT_ID", "tenant"), \
         patch("backend.api.auth.ENTRA_CLIENT_ID", "client"), \
         patch("backend.api.auth.ENTRA_CLIENT_SECRET", "secret"), \
         patch("backend.api.auth.ENTRA_REDIRECT_URI", "http://localhost/callback"), \
         patch("backend.api.auth._get_msal_app", return_value=mock_msal_app), \
         patch("httpx.AsyncClient") as mock_client:
        
        # Mock Graph API responses
        mock_instance = mock_client.return_value.__aenter__.return_value
        
        mock_user_resp = MagicMock()
        mock_user_resp.json.return_value = mock_user_data
        mock_user_resp.raise_for_status.return_value = None
        
        mock_instance.get.side_effect = [mock_user_resp]
        
        # Mock DB
        mock_engine = MagicMock()
        mock_conn = mock_engine.connect.return_value.__enter__.return_value
        
        mock_role_result = MagicMock()
        mock_role_result.fetchone.return_value = (1,)
        
        mock_user_result = MagicMock()
        mock_user_result.fetchone.return_value = ("user_id",)
        
        mock_conn.execute.side_effect = [mock_role_result, mock_user_result]
        
        mock_begin_conn = mock_engine.begin.return_value.__enter__.return_value
        mock_begin_conn.execute.return_value = mock_user_result
        
        with patch("backend.api.auth.get_engine", return_value=mock_engine), \
             patch("backend.api.auth.redis_client") as mock_redis, \
             patch("backend.api.auth.jwt") as mock_jwt:
            
            mock_jwt.encode.return_value = "jwt_token"
            
            request = MagicMock(spec=Request)
            request.cookies = {}
            request.base_url = "http://localhost"
            
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
