import os
from datetime import timedelta
from flask import Flask, jsonify
from flask_security import SQLAlchemyUserDatastore, Security, current_user
from dotenv import load_dotenv
from extensions import db, cache
from models.user import User, Role
from controllers.user import user
from controllers.admin import admin
from controllers.authorisation import authorisation
from controllers.check import check
from security import user_datastore, security, jwt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback_secret_key')
app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT', 'fallback_salt')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'fallback_jwt_secret')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300

db.init_app(app)
security.init_app(app, user_datastore)
jwt.init_app(app)
cache.init_app(app)

app.register_blueprint(user)
app.register_blueprint(admin)
app.register_blueprint(authorisation)
app.register_blueprint(check)

@app.before_request
def before_first_request():
    if not hasattr(app, 'already_ran_before_first_request'):
        with app.app_context():
            db.create_all()
            if not Role.query.filter_by(name='admin').first():
                user_datastore.create_role(name='admin', description='Administrator')
            if not Role.query.filter_by(name='user').first():
                user_datastore.create_role(name='user', description='User')
            if not User.query.filter_by(email='admin@test.com').first():
                user_datastore.create_user(email='admin@test.com', password='password', roles=['admin'])
            db.session.commit()
        app.already_ran_before_first_request = True

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.has_role('admin'):
            return jsonify({"message": "Welcome admin"})
        return jsonify({"message": "Welcome user"})
    return jsonify({"message": "Welcome guest"})

@app.route('/api/token', methods=['POST'])
def create_token():
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    user = user_datastore.find_user(email=email)
    if user and user.password == password:
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token)
    return jsonify({"msg": "Bad email or password"}), 401

@app.route('/api/user', methods=['GET'])
@jwt_required()
def get_user():
    current_user_id = get_jwt_identity()
    user = user_datastore.find_user(id=current_user_id)
    return jsonify(logged_in_as=user.email), 200

if __name__ == '__main__':
    app.run(debug=True)
