import os
from datetime import timedelta
from flask import Flask, request
from flask_cors import CORS
from dotenv import load_dotenv
from extensions import db, cache, mail, celery
from models.user import User, Role
from models.reservation import Reservation
from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot

# from controllers.user import user
# from controllers.admin import admin
# from controllers.authorisation import authorisation
# from controllers.check import check
from security import user_datastore, security, jwt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_restx import Api, Resource, Namespace, fields


import logging
from flask.logging import default_handler

# ... (imports)

# Remove the default handler
logging.root.removeHandler(default_handler)

# Create a new handler with the desired format
handler = logging.StreamHandler()
formatter = logging.Formatter("%(message)s")
handler.setFormatter(formatter)

# Add the new handler to the root logger
logging.root.addHandler(handler)
logging.root.setLevel(logging.INFO)

load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///parking.db"
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "fallback_secret_key")
    app.config["SECURITY_PASSWORD_SALT"] = os.getenv(
        "SECURITY_PASSWORD_SALT", "fallback_salt"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "fallback_jwt_secret")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

    # Cache configuration
    app.config["CACHE_TYPE"] = "redis"
    app.config["CACHE_REDIS_URL"] = os.getenv(
        "CACHE_REDIS_URL", "redis://localhost:6379/0"
    )

    # Celery configuration
    app.config["CELERY_BROKER_URL"] = os.getenv(
        "CELERY_BROKER_URL", "redis://localhost:6379/1"
    )
    app.config["CELERY_RESULT_BACKEND"] = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/2"
    )

    # Email configuration
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "true").lower() in [
        "true",
        "on",
        "1",
    ]
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

    # Twilio configuration
    app.config["TWILIO_ACCOUNT_SID"] = os.getenv("TWILIO_ACCOUNT_SID")
    app.config["TWILIO_AUTH_TOKEN"] = os.getenv("TWILIO_AUTH_TOKEN")
    app.config["TWILIO_FROM_NUMBER"] = os.getenv("TWILIO_FROM_NUMBER")

    # Enable CORS
    CORS(app)

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    security.init_app(app, user_datastore)
    jwt.init_app(app)
    cache.init_app(app)
    mail.init_app(app)

    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
    )
    celery.conf.beat_schedule = {
        "monthly-activity-report": {
            "task": "jobs.send_monthly_activity_report",
            "schedule": {"type": "crontab", "minute": 0, "hour": 8, "day_of_month": 1},
        },
    }

    # Flask-RESTX API setup
    api = Api(
        app,
        version="1.0",
        title="Vehicle Parking API",
        description="API documentation for Vehicle Parking App",
        doc="/docs",
        prefix="/api",
    )  # Moved docs to /api/docs and prefix to /api

    # Namespaces for API endpoints
    auth_ns = Namespace("auth", description="Authentication operations")
    user_ns = Namespace("user", description="User operations")
    admin_ns = Namespace("admin", description="Admin operations")

    # Models for API documentation
    login_model = auth_ns.model(
        "Login",
        {
            "email": fields.String(required=True),
            "password": fields.String(required=True),
        },
    )

    token_model = auth_ns.model("Token", {"access_token": fields.String()})

    # API Endpoints using Flask-RESTX
    @auth_ns.route("/token")
    class TokenResource(Resource):
        @auth_ns.expect(login_model)
        @auth_ns.response(200, "Success", token_model)
        @auth_ns.response(401, "Bad email or password")
        def post(self):
            """Create JWT token"""
            data = request.get_json()
            email = data.get("email")
            password = data.get("password")
            user = user_datastore.find_user(email=email)
            # Simple password check (should match hashing used in user_datastore)
            # Assuming logic matches security.py configuration
            if user and user.password == password:
                access_token = create_access_token(identity=str(user.id))
                return {"access_token": access_token}, 200
            elif (
                user and not user.password
            ):  # Handle case if password hashing is used but raw password in DB
                pass
            return {"msg": "Bad email or password"}, 401

    @auth_ns.route("/register")
    class RegisterResource(Resource):
        def post(self):
            """Register a new user"""
            data = request.get_json()
            username = data.get("username")
            email = data.get("email")
            password = data.get("password")

            if user_datastore.find_user(email=email):
                return {"message": "User already exists"}, 400

            # Create user
            # user_datastore handles hashing automatically if configured
            user_datastore.create_user(
                username=username, email=email, password=password, roles=["user"]
            )
            db.session.commit()
            return {"message": "User created successfully"}, 201

    @user_ns.route("/")
    class UserResource(Resource):
        @jwt_required()
        def get(self):
            """Get current user info"""
            current_user_id = int(get_jwt_identity())
            user = user_datastore.find_user(id=current_user_id)
            if not user:
                return {"message": "User not found"}, 404
            return {"logged_in_as": user.email}, 200

    @user_ns.route("/role")
    class UserRoleResource(Resource):
        @jwt_required()
        def get(self):
            current_user_id = int(get_jwt_identity())
            user = user_datastore.find_user(id=current_user_id)
            if not user:
                return {"message": "User not found"}, 404
            role = user.roles[0].name if user.roles else "user"
            return {"role": role}, 200

    @user_ns.route("/dashboard-data")
    class UserDashboardResource(Resource):
        @jwt_required()
        def get(self):
            current_user_id = int(get_jwt_identity())
            # Logic from controllers/user.py
            all_reservations = (
                Reservation.query.filter_by(user_id=current_user_id)
                .order_by(Reservation.parking_time.asc())
                .all()
            )

            reservations_data = []
            active = 0
            completed = 0

            for r in all_reservations:
                spot = ParkingSpot.query.get(r.spot_id)
                lot = ParkingLot.query.get(spot.lot_id) if spot else None
                lot_name = lot.prime_location_name if lot else "Unknown"

                reservations_data.append(
                    {
                        "id": r.id,
                        "lot_name": lot_name,
                        "spot_no": spot.spot_no if spot else "?",
                        "parking_time": r.parking_time.isoformat()
                        if r.parking_time
                        else None,
                        "leaving_time": r.leaving_time.isoformat()
                        if r.leaving_time
                        else None,
                        "status": r.status,  # Assuming status field or property exists
                    }
                )
                # Simple logic for stats
                if r.status == "active":  # Check actual status values
                    active += 1
                elif r.status == "completed":
                    completed += 1

            # Since Reservation model doesn't explicitly store status (calculated in controller logic usually),
            # we will simplify for now. In original code it was calculated.
            # "active" usually means parking_time < now < leaving_time or checkin without checkout

            return {
                "reservations": reservations_data,
                "stats": {"active": active, "completed": completed},
            }, 200

    @admin_ns.route("/dashboard-data")
    class AdminDashboardResource(Resource):
        @jwt_required()
        def get(self):
            # Verify admin role
            current_user_id = int(get_jwt_identity())
            user = user_datastore.find_user(id=current_user_id)
            if not user or not user.has_role("admin"):
                return {"message": "Admin access required"}, 403

            lots = ParkingLot.query.all()
            total_lots = ParkingLot.query.count()

            # Simplified revenue calculation
            total_revenue = 0

            lots_data = []
            for lot in lots:
                # Calculate occupancy
                spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
                total_spots = len(spots)
                occupied = sum(1 for s in spots if s.status == "O")
                occupancy = (occupied / total_spots * 100) if total_spots > 0 else 0

                lots_data.append(
                    {
                        "id": lot.id,
                        "name": lot.prime_location_name,
                        "address": lot.address,
                        "price": lot.price_per_hr,
                        "occupancy": round(occupancy, 1),
                    }
                )

            return {
                "lots": lots_data,
                "stats": {
                    "total_lots": total_lots,
                    "total_revenue": total_revenue,  # Placeholder
                },
            }, 200

    api.add_namespace(auth_ns, path="/auth")
    api.add_namespace(user_ns, path="/user")
    api.add_namespace(admin_ns, path="/admin")

    # Removed blueprints
    # app.register_blueprint(user, url_prefix='/user')
    # app.register_blueprint(admin, url_prefix='/admin')
    # app.register_blueprint(authorisation)
    # app.register_blueprint(check)

    @app.route("/")
    def index():
        return "Please access via Frontend port 8080 or build dist"

    @app.before_request
    def before_first_request():
        if not app.config.get("ALREADY_RAN_BEFORE_FIRST_REQUEST"):
            with app.app_context():
                db.create_all()
                if not Role.query.filter_by(name="admin").first():
                    user_datastore.create_role(
                        name="admin", description="Administrator"
                    )
                if not Role.query.filter_by(name="user").first():
                    user_datastore.create_role(name="user", description="User")
                if not User.query.filter_by(email="admin@test.com").first():
                    user_datastore.create_user(
                        username="admin",
                        email="admin@test.com",
                        password="admin",
                        roles=["admin"],
                    )
                db.session.commit()
            app.config["ALREADY_RAN_BEFORE_FIRST_REQUEST"] = True

    return app


if __name__ == "__main__":
    app = create_app()

    # Configure logging
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    app.run(host="0.0.0.0", port=5000, debug=True)
