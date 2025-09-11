import os
from datetime import timedelta
from flask import Flask, jsonify, request
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
from flask_restx import Api, Resource, Namespace, fields

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

# Flask-RESTX API setup
api = Api(app, version='1.0', title='Vehicle Parking API',
          description='API documentation for Vehicle Parking App',
          doc='/api/docs')

# Namespaces for API endpoints
auth_ns = Namespace('auth', description='Authentication operations')
user_ns = Namespace('user', description='User operations')
admin_ns = Namespace('admin', description='Admin operations')

# Models for API documentation
login_model = auth_ns.model('Login', {
    'email': fields.String(required=True),
    'password': fields.String(required=True)
})

token_model = auth_ns.model('Token', {
    'access_token': fields.String()
})

# API Endpoints using Flask-RESTX
@auth_ns.route('/token')
class TokenResource(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.response(200, 'Success', token_model)
    @auth_ns.response(401, 'Bad email or password')
    def post(self):
        """Create JWT token"""
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        user = user_datastore.find_user(email=email)
        if user and user.password == password:
            access_token = create_access_token(identity=user.id)
            return {'access_token': access_token}, 200
        return {'msg': 'Bad email or password'}, 401

@user_ns.route('/')
class UserResource(Resource):
    @jwt_required()
    def get(self):
        """Get current user info"""
        current_user_id = get_jwt_identity()
        user = user_datastore.find_user(id=current_user_id)
        return {'logged_in_as': user.email}, 200

api.add_namespace(auth_ns, path='/api/auth')
api.add_namespace(user_ns, path='/api/user')
api.add_namespace(admin_ns, path='/api/admin')

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


# Optionally, you can add a root endpoint for health check or landing
@app.route('/')
def index():
    return jsonify({"message": "Vehicle Parking App API"})


if __name__ == '__main__':
    app.run(debug=True)
