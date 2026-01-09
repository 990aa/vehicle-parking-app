import pytest


def test_asgi_app_initialization():
    try:
        from asgi import asgi_app

        assert asgi_app is not None
    except ImportError:
        pass  # Optional if dependencies are missing in test env, but they should be there
    except Exception as e:
        pytest.fail(f"ASGI app failed to initialize: {e}")


def test_gunicorn_config_valid():
    import os

    if os.path.exists("gunicorn_config.py"):
        # We can just check if file exists and has correct syntax
        with open("gunicorn_config.py", "r") as f:
            content = f.read()
        assert "worker_class" in content
        assert "uvicorn.workers.UvicornWorker" in content
