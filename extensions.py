from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_mail import Mail
from celery import Celery

db = SQLAlchemy()
cache = Cache()
mail = Mail()
celery = Celery()
