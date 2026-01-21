def test_api_root_message(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"parkapp API" in response.data or b"API is running" in response.data


def test_token_auth_flow(client, db):
    # Register first
    client.post(
        "/api/auth/register",
        json={"username": "apitest", "email": "api@test.com", "password": "password123"},
    )

    response = client.post(
        "/api/auth/login", json={"email": "api@test.com", "password": "password123"}
    )

    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data
