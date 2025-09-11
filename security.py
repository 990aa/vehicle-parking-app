from flask_security import Security, SQLAlchemyUserDatastore
from flask_jwt_extended import JWTManager
from models.user import User, Role
from extensions import db

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security()
jwt = JWTManager()
