import multiprocessing

bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
loglevel = "info"
accesslog = "-"
errorlog = "-"
keepalive = 120
timeout = 120
forwarded_allow_ips = "*"

# Environment variables
raw_env = [
    "FLASK_APP=app:create_app()",
]
