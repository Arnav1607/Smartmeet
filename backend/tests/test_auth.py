import pytest, json
from app import create_app, db

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_register_and_login(client):
    res = client.post('/api/auth/register', json={'email': 'test@test.com', 'password': 'secret123', 'name': 'Test'})
    assert res.status_code == 201
    data = json.loads(res.data)
    assert 'token' in data

def test_login_wrong_password(client):
    client.post('/api/auth/register', json={'email': 'a@b.com', 'password': 'right', 'name': 'A'})
    res = client.post('/api/auth/login', json={'email': 'a@b.com', 'password': 'wrong'})
    assert res.status_code == 401
