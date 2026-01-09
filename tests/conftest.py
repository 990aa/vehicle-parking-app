import pytest
import sys
import os

# Add the project root to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db as _db
from security import user_datastore

@pytest.fixture
def app():
    # Helper to check if we can run redis dependent tests
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'CACHE_TYPE': 'NullCache',
        'CELERY_BROKER_URL': 'memory://',
        'CELERY_RESULT_BACKEND': 'cache+memory://',
        'MAIL_SUPPRESS_SEND': True,
        'JWT_SECRET_KEY': 'test-secret',
        'SECRET_KEY': 'test-secret'
    }
    app = create_app(test_config=test_config)

    with app.app_context():
        _db.create_all()
        # Seed roles
        if not user_datastore.find_role('user'):
            user_datastore.create_role(name='user', description='User')
        if not user_datastore.find_role('admin'):
            user_datastore.create_role(name='admin', description='Administrator')
        _db.session.commit()
        
        yield app
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def db(app):
    with app.app_context():
        yield _db
