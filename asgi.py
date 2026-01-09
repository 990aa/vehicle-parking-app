from asgiref.wsgi import WsgiToAsgi
from app import create_app

app = create_app()
asgi_app = WsgiToAsgi(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("asgi:asgi_app", host="0.0.0.0", port=5000, reload=True)
