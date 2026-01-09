def test_api_root_message(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Please access via Frontend" in response.data

def test_token_auth_flow(client, db):
    # Register first
    client.post('/api/auth/register', json={
        'username': 'apitest',
        'email': 'api@test.com',
        'password': 'password'
    })
    
    response = client.post('/api/auth/token', json={
        'email': 'api@test.com',
        'password': 'password'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data
