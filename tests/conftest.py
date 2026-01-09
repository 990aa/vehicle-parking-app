import pytest
from app import create_app
from extensions import db as _db

@pytest.fixture
def app():
    # Helper to check if we can run redis dependent tests
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'CACHE_TYPE': 'NullCache',  # Disable redis cache for basic tests
        'CELERY_BROKER_URL': 'memory://',
        'CELERY_RESULT_BACKEND': 'cache+memory://',
        'MAIL_SUPPRESS_SEND': True
    }
    app = create_app(test_config=test_config)

    with app.app_context():
        _db.create_all()
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
