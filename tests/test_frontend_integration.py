def test_api_dashboard_data(client, db):
    # Create user and data
    client.post(
        "/api/auth/register",
        json={
            "username": "dashboard_user",
            "email": "dash@test.com",
            "password": "password123",
        },
    )

    # Login
    auth_res = client.post(
        "/api/auth/login", json={"email": "dash@test.com", "password": "password123"}
    )
    token = auth_res.get_json()["access_token"]

    # Get dashboard data
    res = client.get(
        "/api/user/dashboard-data", headers={"Authorization": f"Bearer {token}"}
    )

    if res.status_code != 200:
        print(f"FAILED Response: {res.get_json()}")

    assert res.status_code == 200
    data = res.get_json()
    assert "reservations" in data
    assert "stats" in data


def test_frontend_files_exist():
    import os

    base_path = "frontend/src/views"
    assert os.path.exists(os.path.join(base_path, "Login.vue"))
    assert os.path.exists(os.path.join(base_path, "Register.vue"))
    assert os.path.exists(os.path.join(base_path, "UserDashboard.vue"))
    assert os.path.exists(os.path.join(base_path, "AdminDashboard.vue"))
    assert os.path.exists(os.path.join(base_path, "Parking.vue"))
