import os
import uuid
from datetime import timedelta, datetime
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, cache, mail, celery
from models.user import User, Role
from models.reservation import Reservation
from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot
from models.lot_bookings import LotBooking

from security import user_datastore, security, jwt
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from flask_restx import Api, Resource, Namespace, fields

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__)
    
    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URI", "sqlite:///parking.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    
    # Security configuration
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
    app.config["SECURITY_PASSWORD_SALT"] = os.getenv(
        "SECURITY_PASSWORD_SALT", "dev-salt-change-in-prod"
    )
    app.config["SECURITY_PASSWORD_HASH"] = "pbkdf2_sha512"
    
    # JWT configuration
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "jwt-secret-change-in-prod")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)
    app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    app.config["JWT_HEADER_NAME"] = "Authorization"
    app.config["JWT_HEADER_TYPE"] = "Bearer"

    # Cache configuration
    app.config["CACHE_TYPE"] = os.getenv("CACHE_TYPE", "simple")
    app.config["CACHE_REDIS_URL"] = os.getenv("CACHE_REDIS_URL", "redis://localhost:6379/0")
    app.config["CACHE_DEFAULT_TIMEOUT"] = 300

    # Celery configuration
    app.config["CELERY_BROKER_URL"] = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    app.config["CELERY_RESULT_BACKEND"] = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

    # Email configuration
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "true").lower() in ["true", "on", "1"]
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

    # CORS - Allow all origins in development
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:5000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    if test_config:
        app.config.update(test_config)

    # Initialize extensions
    db.init_app(app)
    security.init_app(app, user_datastore)
    jwt.init_app(app)
    cache.init_app(app)
    mail.init_app(app)

    # Configure Celery
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
    )

    # Flask-RESTX API setup
    authorizations = {
        "Bearer Auth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Add 'Bearer <JWT>' to authorize"
        }
    }
    
    api = Api(
        app,
        version="1.0",
        title="Vehicle Parking API",
        description="Complete API for Vehicle Parking Management System",
        doc="/api/docs",
        prefix="/api",
        authorizations=authorizations,
        security="Bearer Auth"
    )

    # Namespaces
    auth_ns = Namespace("auth", description="Authentication operations")
    user_ns = Namespace("user", description="User operations")
    admin_ns = Namespace("admin", description="Admin operations")
    parking_ns = Namespace("parking", description="Parking operations")

    # API Models for documentation
    login_model = auth_ns.model("Login", {
        "email": fields.String(required=True, description="User email", example="user@example.com"),
        "password": fields.String(required=True, description="User password", example="password123"),
    })

    register_model = auth_ns.model("Register", {
        "username": fields.String(required=True, description="Username", example="johndoe"),
        "email": fields.String(required=True, description="Email address", example="john@example.com"),
        "password": fields.String(required=True, description="Password (min 6 characters)", example="password123"),
    })

    token_response = auth_ns.model("TokenResponse", {
        "access_token": fields.String(description="JWT access token"),
        "user": fields.Raw(description="User information"),
        "message": fields.String(description="Response message"),
    })

    error_response = auth_ns.model("ErrorResponse", {
        "message": fields.String(description="Error message"),
        "errors": fields.Raw(description="Detailed errors"),
    })

    # Helper function to create user with proper password hashing
    def create_user_with_hash(username, email, password, roles=None):
        """Create user with properly hashed password and fs_uniquifier"""
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        fs_uniquifier = str(uuid.uuid4())
        
        user = User(
            username=username,
            email=email,
            password=hashed_password,
            fs_uniquifier=fs_uniquifier,
            active=True
        )
        
        if roles:
            for role_name in roles:
                role = Role.query.filter_by(name=role_name).first()
                if role:
                    user.roles.append(role)
        
        db.session.add(user)
        return user

    # ========================
    # AUTH ENDPOINTS
    # ========================
    
    @auth_ns.route("/register")
    class RegisterResource(Resource):
        @auth_ns.expect(register_model)
        @auth_ns.response(201, "User created successfully", token_response)
        @auth_ns.response(400, "Validation error", error_response)
        def post(self):
            """Register a new user account"""
            try:
                data = request.get_json()
                
                if not data:
                    return {"message": "No data provided", "errors": {"general": "Request body is empty"}}, 400
                
                username = data.get("username", "").strip()
                email = data.get("email", "").strip().lower()
                password = data.get("password", "")
                
                errors = {}
                
                # Validation
                if not username:
                    errors["username"] = "Username is required"
                elif len(username) < 3:
                    errors["username"] = "Username must be at least 3 characters"
                elif len(username) > 50:
                    errors["username"] = "Username must be less than 50 characters"
                elif User.query.filter_by(username=username).first():
                    errors["username"] = "Username is already taken"
                
                if not email:
                    errors["email"] = "Email is required"
                elif "@" not in email or "." not in email:
                    errors["email"] = "Please enter a valid email address"
                elif User.query.filter_by(email=email).first():
                    errors["email"] = "An account with this email already exists"
                
                if not password:
                    errors["password"] = "Password is required"
                elif len(password) < 6:
                    errors["password"] = "Password must be at least 6 characters"
                
                if errors:
                    return {"message": "Please fix the following errors", "errors": errors}, 400
                
                # Create user
                user = create_user_with_hash(username, email, password, roles=["user"])
                db.session.commit()
                
                # Auto-login: create token
                access_token = create_access_token(identity=str(user.id))
                
                logger.info(f"New user registered: {email}")
                
                return {
                    "message": "Account created successfully! Welcome to ParkEase.",
                    "access_token": access_token,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": "user"
                    }
                }, 201
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Registration error: {str(e)}")
                return {"message": "Registration failed. Please try again.", "errors": {"general": str(e)}}, 500

    @auth_ns.route("/login")
    class LoginResource(Resource):
        @auth_ns.expect(login_model)
        @auth_ns.response(200, "Login successful", token_response)
        @auth_ns.response(401, "Invalid credentials", error_response)
        def post(self):
            """Login with email and password"""
            try:
                data = request.get_json()
                
                if not data:
                    return {"message": "No data provided", "errors": {"general": "Request body is empty"}}, 400
                
                email = data.get("email", "").strip().lower()
                password = data.get("password", "")
                
                if not email or not password:
                    return {
                        "message": "Please enter your credentials",
                        "errors": {
                            "email": "Email is required" if not email else None,
                            "password": "Password is required" if not password else None
                        }
                    }, 400
                
                user = User.query.filter_by(email=email).first()
                
                if not user:
                    return {
                        "message": "Invalid credentials",
                        "errors": {"email": "No account found with this email address"}
                    }, 401
                
                if not user.active:
                    return {
                        "message": "Account disabled",
                        "errors": {"general": "Your account has been disabled. Please contact support."}
                    }, 401
                
                if not check_password_hash(user.password, password):
                    return {
                        "message": "Invalid credentials",
                        "errors": {"password": "Incorrect password"}
                    }, 401
                
                # Create token
                access_token = create_access_token(identity=str(user.id))
                role = user.roles[0].name if user.roles else "user"
                
                logger.info(f"User logged in: {email}")
                
                return {
                    "message": f"Welcome back, {user.username}!",
                    "access_token": access_token,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": role
                    }
                }, 200
                
            except Exception as e:
                logger.error(f"Login error: {str(e)}")
                return {"message": "Login failed. Please try again.", "errors": {"general": str(e)}}, 500

    @auth_ns.route("/token")
    class TokenResource(Resource):
        @auth_ns.expect(login_model)
        @auth_ns.response(200, "Token created", token_response)
        @auth_ns.response(401, "Invalid credentials", error_response)
        def post(self):
            """Create JWT token (alias for login)"""
            return LoginResource().post()

    @auth_ns.route("/me")
    class MeResource(Resource):
        @jwt_required()
        @auth_ns.response(200, "User info retrieved")
        def get(self):
            """Get current authenticated user info"""
            try:
                user_id = int(get_jwt_identity())
                user = User.query.get(user_id)
                
                if not user:
                    return {"message": "User not found"}, 404
                
                role = user.roles[0].name if user.roles else "user"
                
                return {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": role,
                        "created_at": user.time.isoformat() if user.time else None
                    }
                }, 200
            except Exception as e:
                logger.error(f"Error fetching user: {str(e)}")
                return {"message": "Failed to fetch user info"}, 500

    # ========================
    # USER ENDPOINTS
    # ========================
    
    @user_ns.route("/")
    class UserResource(Resource):
        @jwt_required()
        def get(self):
            """Get current user info"""
            user_id = int(get_jwt_identity())
            user = User.query.get(user_id)
            if not user:
                return {"message": "User not found"}, 404
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.roles[0].name if user.roles else "user"
            }, 200

    @user_ns.route("/role")
    class UserRoleResource(Resource):
        @jwt_required()
        def get(self):
            """Get current user's role"""
            user_id = int(get_jwt_identity())
            user = User.query.get(user_id)
            if not user:
                return {"message": "User not found"}, 404
            role = user.roles[0].name if user.roles else "user"
            return {"role": role}, 200

    @user_ns.route("/dashboard-data")
    class UserDashboardResource(Resource):
        @jwt_required()
        def get(self):
            """Get user dashboard data with reservations"""
            try:
                user_id = int(get_jwt_identity())
                
                reservations = (
                    Reservation.query
                    .filter_by(user_id=user_id)
                    .order_by(Reservation.parking_time.desc())
                    .all()
                )

                reservations_data = []
                stats = {"active": 0, "completed": 0, "upcoming": 0, "cancelled": 0}
                
                now = datetime.now()

                for r in reservations:
                    spot = ParkingSpot.query.get(r.spot_id)
                    lot = ParkingLot.query.get(spot.lot_id) if spot else None
                    
                    # Determine status
                    status_map = {"U": "upcoming", "A": "active", "C": "completed", "X": "cancelled"}
                    status = status_map.get(r.status, "unknown")
                    
                    reservations_data.append({
                        "id": r.id,
                        "lot_name": lot.prime_location_name if lot else "Unknown",
                        "lot_address": lot.address if lot else "",
                        "spot_no": spot.spot_no if spot else "?",
                        "vehicle_number": r.vehicle_number,
                        "parking_time": r.parking_time.isoformat() if r.parking_time else None,
                        "leaving_time": r.leaving_time.isoformat() if r.leaving_time else None,
                        "cost": r.cost,
                        "status": status,
                    })
                    
                    if status in stats:
                        stats[status] += 1

                return {
                    "reservations": reservations_data,
                    "stats": stats
                }, 200
                
            except Exception as e:
                logger.error(f"Dashboard error: {str(e)}")
                return {"message": "Failed to load dashboard data"}, 500

    # ========================
    # PARKING ENDPOINTS
    # ========================
    
    @parking_ns.route("/lots")
    class ParkingLotsResource(Resource):
        @jwt_required()
        def get(self):
            """Get all available parking lots"""
            try:
                lots = ParkingLot.query.all()
                lots_data = []
                
                for lot in lots:
                    spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
                    available = sum(1 for s in spots if s.status == "A")
                    total = len(spots)
                    
                    lots_data.append({
                        "id": lot.id,
                        "name": lot.prime_location_name,
                        "address": lot.address,
                        "pin_code": lot.pin_code,
                        "price_per_hr": lot.price_per_hr,
                        "total_spots": total,
                        "available_spots": available,
                        "occupancy": round((total - available) / total * 100, 1) if total > 0 else 0
                    })
                
                return {"lots": lots_data}, 200
            except Exception as e:
                logger.error(f"Error fetching lots: {str(e)}")
                return {"message": "Failed to fetch parking lots"}, 500

    @parking_ns.route("/lots/<int:lot_id>/spots")
    class ParkingSpotsResource(Resource):
        @jwt_required()
        def get(self, lot_id):
            """Get available spots for a parking lot"""
            try:
                lot = ParkingLot.query.get(lot_id)
                if not lot:
                    return {"message": "Parking lot not found"}, 404
                
                spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
                spots_data = [{
                    "id": s.id,
                    "spot_no": s.spot_no,
                    "status": "available" if s.status == "A" else "occupied"
                } for s in spots]
                
                return {
                    "lot": {
                        "id": lot.id,
                        "name": lot.prime_location_name,
                        "price_per_hr": lot.price_per_hr
                    },
                    "spots": spots_data
                }, 200
            except Exception as e:
                logger.error(f"Error fetching spots: {str(e)}")
                return {"message": "Failed to fetch parking spots"}, 500

    reservation_model = parking_ns.model("Reservation", {
        "spot_id": fields.Integer(required=True, description="Parking spot ID"),
        "vehicle_number": fields.String(required=True, description="Vehicle license plate"),
        "parking_time": fields.String(required=True, description="Parking start time (ISO format)"),
        "leaving_time": fields.String(required=True, description="Expected leaving time (ISO format)"),
    })

    @parking_ns.route("/reserve")
    class ReservationResource(Resource):
        @jwt_required()
        @parking_ns.expect(reservation_model)
        def post(self):
            """Create a new parking reservation"""
            try:
                user_id = int(get_jwt_identity())
                data = request.get_json()
                
                spot_id = data.get("spot_id")
                vehicle_number = data.get("vehicle_number", "").strip().upper()
                parking_time_str = data.get("parking_time")
                leaving_time_str = data.get("leaving_time")
                
                errors = {}
                
                if not spot_id:
                    errors["spot_id"] = "Please select a parking spot"
                if not vehicle_number:
                    errors["vehicle_number"] = "Vehicle number is required"
                if not parking_time_str:
                    errors["parking_time"] = "Parking time is required"
                if not leaving_time_str:
                    errors["leaving_time"] = "Leaving time is required"
                
                if errors:
                    return {"message": "Please fix the errors", "errors": errors}, 400
                
                # Parse times
                try:
                    parking_time = datetime.fromisoformat(parking_time_str.replace("Z", "+00:00"))
                    leaving_time = datetime.fromisoformat(leaving_time_str.replace("Z", "+00:00"))
                except ValueError:
                    return {"message": "Invalid date format", "errors": {"general": "Use ISO format for dates"}}, 400
                
                # Check spot availability
                spot = ParkingSpot.query.get(spot_id)
                if not spot:
                    return {"message": "Parking spot not found"}, 404
                if spot.status != "A":
                    return {"message": "This spot is no longer available", "errors": {"spot_id": "Spot is occupied"}}, 400
                
                lot = ParkingLot.query.get(spot.lot_id)
                
                # Calculate cost
                duration_hours = (leaving_time - parking_time).total_seconds() / 3600
                cost = round(duration_hours * lot.price_per_hr, 2)
                
                # Create reservation
                reservation = Reservation(
                    spot_id=spot_id,
                    user_id=user_id,
                    vehicle_number=vehicle_number,
                    parking_time=parking_time,
                    leaving_time=leaving_time,
                    cost=cost,
                    status="U"  # Upcoming
                )
                
                # Mark spot as occupied
                spot.status = "O"
                
                db.session.add(reservation)
                db.session.commit()
                
                logger.info(f"Reservation created: {reservation.id} for user {user_id}")
                
                return {
                    "message": "Reservation confirmed!",
                    "reservation": {
                        "id": reservation.id,
                        "lot_name": lot.prime_location_name,
                        "spot_no": spot.spot_no,
                        "vehicle_number": vehicle_number,
                        "parking_time": parking_time.isoformat(),
                        "leaving_time": leaving_time.isoformat(),
                        "estimated_cost": cost
                    }
                }, 201
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Reservation error: {str(e)}")
                return {"message": "Failed to create reservation", "errors": {"general": str(e)}}, 500

    @parking_ns.route("/reservations/<int:reservation_id>/cancel")
    class CancelReservationResource(Resource):
        @jwt_required()
        def post(self, reservation_id):
            """Cancel a reservation"""
            try:
                user_id = int(get_jwt_identity())
                reservation = Reservation.query.get(reservation_id)
                
                if not reservation:
                    return {"message": "Reservation not found"}, 404
                if reservation.user_id != user_id:
                    return {"message": "Unauthorized"}, 403
                if reservation.status not in ["U", "A"]:
                    return {"message": "Cannot cancel this reservation"}, 400
                
                # Free up the spot
                spot = ParkingSpot.query.get(reservation.spot_id)
                if spot:
                    spot.status = "A"
                
                reservation.status = "X"  # Cancelled
                db.session.commit()
                
                return {"message": "Reservation cancelled successfully"}, 200
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Cancel error: {str(e)}")
                return {"message": "Failed to cancel reservation"}, 500

    # ========================
    # ADMIN ENDPOINTS
    # ========================
    
    def admin_required(f):
        """Decorator to check admin role"""
        @wraps(f)
        def decorated(*args, **kwargs):
            user_id = int(get_jwt_identity())
            user = User.query.get(user_id)
            if not user or not any(r.name == "admin" for r in user.roles):
                return {"message": "Admin access required"}, 403
            return f(*args, **kwargs)
        return decorated

    @admin_ns.route("/dashboard-data")
    class AdminDashboardResource(Resource):
        @jwt_required()
        def get(self):
            """Get admin dashboard data"""
            try:
                user_id = int(get_jwt_identity())
                user = User.query.get(user_id)
                
                if not user or not any(r.name == "admin" for r in user.roles):
                    return {"message": "Admin access required"}, 403

                lots = ParkingLot.query.all()
                total_users = User.query.count()
                total_reservations = Reservation.query.count()
                
                # Calculate revenue
                completed_reservations = Reservation.query.filter_by(status="C").all()
                total_revenue = sum(r.cost or 0 for r in completed_reservations)

                lots_data = []
                total_spots = 0
                total_occupied = 0
                
                for lot in lots:
                    spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
                    lot_total = len(spots)
                    occupied = sum(1 for s in spots if s.status == "O")
                    total_spots += lot_total
                    total_occupied += occupied
                    
                    lots_data.append({
                        "id": lot.id,
                        "name": lot.prime_location_name,
                        "address": lot.address,
                        "price_per_hr": lot.price_per_hr,
                        "total_spots": lot_total,
                        "occupied": occupied,
                        "available": lot_total - occupied,
                        "occupancy": round(occupied / lot_total * 100, 1) if lot_total > 0 else 0
                    })

                return {
                    "lots": lots_data,
                    "stats": {
                        "total_lots": len(lots),
                        "total_spots": total_spots,
                        "total_occupied": total_occupied,
                        "total_available": total_spots - total_occupied,
                        "total_users": total_users,
                        "total_reservations": total_reservations,
                        "total_revenue": round(total_revenue, 2),
                        "occupancy_rate": round(total_occupied / total_spots * 100, 1) if total_spots > 0 else 0
                    }
                }, 200
                
            except Exception as e:
                logger.error(f"Admin dashboard error: {str(e)}")
                return {"message": "Failed to load admin dashboard"}, 500

    @admin_ns.route("/users")
    class AdminUsersResource(Resource):
        @jwt_required()
        def get(self):
            """Get all users (admin only)"""
            try:
                user_id = int(get_jwt_identity())
                user = User.query.get(user_id)
                
                if not user or not any(r.name == "admin" for r in user.roles):
                    return {"message": "Admin access required"}, 403
                
                users = User.query.all()
                users_data = [{
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "role": u.roles[0].name if u.roles else "user",
                    "active": u.active,
                    "created_at": u.time.isoformat() if u.time else None
                } for u in users]
                
                return {"users": users_data}, 200
            except Exception as e:
                logger.error(f"Error fetching users: {str(e)}")
                return {"message": "Failed to fetch users"}, 500

    @admin_ns.route("/reservations")
    class AdminReservationsResource(Resource):
        @jwt_required()
        def get(self):
            """Get all reservations (admin only)"""
            try:
                user_id = int(get_jwt_identity())
                user = User.query.get(user_id)
                
                if not user or not any(r.name == "admin" for r in user.roles):
                    return {"message": "Admin access required"}, 403
                
                reservations = Reservation.query.order_by(Reservation.parking_time.desc()).limit(100).all()
                status_map = {"U": "upcoming", "A": "active", "C": "completed", "X": "cancelled"}
                
                data = []
                for r in reservations:
                    res_user = User.query.get(r.user_id)
                    spot = ParkingSpot.query.get(r.spot_id)
                    lot = ParkingLot.query.get(spot.lot_id) if spot else None
                    
                    data.append({
                        "id": r.id,
                        "user": res_user.username if res_user else "Unknown",
                        "user_email": res_user.email if res_user else "",
                        "lot_name": lot.prime_location_name if lot else "Unknown",
                        "spot_no": spot.spot_no if spot else "?",
                        "vehicle_number": r.vehicle_number,
                        "parking_time": r.parking_time.isoformat() if r.parking_time else None,
                        "leaving_time": r.leaving_time.isoformat() if r.leaving_time else None,
                        "cost": r.cost,
                        "status": status_map.get(r.status, "unknown")
                    })
                
                return {"reservations": data}, 200
            except Exception as e:
                logger.error(f"Error fetching reservations: {str(e)}")
                return {"message": "Failed to fetch reservations"}, 500

    lot_model = admin_ns.model("ParkingLot", {
        "name": fields.String(required=True, description="Parking lot name"),
        "address": fields.String(required=True, description="Address"),
        "pin_code": fields.String(required=True, description="PIN code"),
        "price_per_hr": fields.Float(required=True, description="Price per hour"),
        "max_spots": fields.Integer(required=True, description="Number of spots"),
    })

    @admin_ns.route("/lots")
    class AdminLotsResource(Resource):
        @jwt_required()
        def get(self):
            """Get all parking lots (admin)"""
            user_id = int(get_jwt_identity())
            user = User.query.get(user_id)
            if not user or not any(r.name == "admin" for r in user.roles):
                return {"message": "Admin access required"}, 403
            
            lots = ParkingLot.query.all()
            return {"lots": [{
                "id": l.id,
                "name": l.prime_location_name,
                "address": l.address,
                "pin_code": l.pin_code,
                "price_per_hr": l.price_per_hr,
                "max_spots": l.max_spots
            } for l in lots]}, 200
        
        @jwt_required()
        @admin_ns.expect(lot_model)
        def post(self):
            """Create a new parking lot (admin only)"""
            try:
                user_id = int(get_jwt_identity())
                user = User.query.get(user_id)
                
                if not user or not any(r.name == "admin" for r in user.roles):
                    return {"message": "Admin access required"}, 403
                
                data = request.get_json()
                
                lot = ParkingLot(
                    prime_location_name=data.get("name"),
                    address=data.get("address"),
                    pin_code=data.get("pin_code"),
                    price_per_hr=data.get("price_per_hr"),
                    max_spots=data.get("max_spots")
                )
                db.session.add(lot)
                db.session.flush()  # Get lot.id
                
                # Create parking spots
                for i in range(1, lot.max_spots + 1):
                    spot = ParkingSpot(lot_id=lot.id, spot_no=i, status="A")
                    db.session.add(spot)
                
                db.session.commit()
                
                return {"message": f"Parking lot '{lot.prime_location_name}' created with {lot.max_spots} spots"}, 201
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error creating lot: {str(e)}")
                return {"message": "Failed to create parking lot"}, 500

    # Register namespaces
    api.add_namespace(auth_ns, path="/auth")
    api.add_namespace(user_ns, path="/user")
    api.add_namespace(admin_ns, path="/admin")
    api.add_namespace(parking_ns, path="/parking")

    # Health check endpoint
    @app.route("/api/health")
    def health_check():
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}, 200

    @app.route("/")
    def index():
        return """
        <html>
        <head><title>ParkEase API</title></head>
        <body style="font-family: Arial; padding: 50px; text-align: center;">
            <h1>🚗 ParkEase API Server</h1>
            <p>API is running. Access frontend at <a href="http://localhost:8080">http://localhost:8080</a></p>
            <p>API Documentation: <a href="/api/docs">/api/docs</a></p>
        </body>
        </html>
        """

    # Database initialization
    with app.app_context():
        db.create_all()
        
        # Create default roles
        if not Role.query.filter_by(name="admin").first():
            admin_role = Role(name="admin", description="Administrator")
            db.session.add(admin_role)
            logger.info("Created admin role")
        
        if not Role.query.filter_by(name="user").first():
            user_role = Role(name="user", description="Regular User")
            db.session.add(user_role)
            logger.info("Created user role")
        
        db.session.commit()
        
        # Create default admin user
        if not User.query.filter_by(email="admin@parkease.com").first():
            create_user_with_hash(
                username="admin",
                email="admin@parkease.com",
                password="admin123",
                roles=["admin"]
            )
            db.session.commit()
            logger.info("Created default admin user: admin@parkease.com / admin123")
        
        # Create sample parking lots if none exist
        if ParkingLot.query.count() == 0:
            sample_lots = [
                {"name": "Downtown Central Parking", "address": "123 Main Street", "pin_code": "10001", "price": 5.0, "spots": 50},
                {"name": "Airport Long Term", "address": "Airport Road Terminal 1", "pin_code": "10002", "price": 8.0, "spots": 100},
                {"name": "Mall Underground Parking", "address": "456 Shopping Center Blvd", "pin_code": "10003", "price": 3.0, "spots": 200},
            ]
            
            for lot_data in sample_lots:
                lot = ParkingLot(
                    prime_location_name=lot_data["name"],
                    address=lot_data["address"],
                    pin_code=lot_data["pin_code"],
                    price_per_hr=lot_data["price"],
                    max_spots=lot_data["spots"]
                )
                db.session.add(lot)
                db.session.flush()
                
                for i in range(1, lot_data["spots"] + 1):
                    spot = ParkingSpot(lot_id=lot.id, spot_no=i, status="A")
                    db.session.add(spot)
            
            db.session.commit()
            logger.info("Created sample parking lots")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
