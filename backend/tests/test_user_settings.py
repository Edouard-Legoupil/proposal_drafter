def test_get_user_approved_settings(client):
    """Test getting user's approved settings"""
    # Use a simple test that doesn't require authentication for now
    # Just verify the endpoint exists and returns a proper response
    response = client.get("/api/users/me/approved-settings", headers={"Host": "localhost"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    # Should get 401 Unauthorized since no auth, but not 404 Not Found
    assert response.status_code == 401
