from backend.api import auth


def test_invalid_credentials_response_does_not_reveal_account_state():
    assert hasattr(auth, "invalid_credentials_response")
    response = auth.invalid_credentials_response()

    assert response.status_code == 401
    assert response.body == b'{"error":"Invalid credentials."}'
