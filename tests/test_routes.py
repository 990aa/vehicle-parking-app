def test_home_redirect(client):
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location

def test_login_page_load(client):
    # This might fail if template not found or error in template rendering, 
    # but we want to ensure tests pass.
    # If templates rely on detailed context or missing env vars, it might error.
    # Let's see.
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data

def test_api_token_auth_endpoint(client, db):
    # The app creates an admin user on first request logic
    # We trigger it by making a request or manually
    # But since we are using a fresh DB in fixture, we rely on the app's before_request logic
    # creating the admin user 'admin@test.com' / 'admin'
    
    # Trigger first request logic
    client.get('/login') 

    # Now try to get token
    response = client.post('/api/auth/token', json={
        'email': 'admin@test.com',
        'password': 'admin'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data
