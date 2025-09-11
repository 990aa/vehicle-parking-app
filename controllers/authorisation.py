
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_jwt_extended import create_access_token
from flask_security import auth_required, roles_required, current_user
from security import user_datastore

authorisation = Blueprint('authorisation', __name__)

@authorisation.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json.get('email', None)
        password = request.json.get('password', None)
    else:
        email = request.form.get('email', None)
        password = request.form.get('password', None)

    user = user_datastore.find_user(email=email)

    if user and user.password == password:
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token)
    
    return jsonify({"msg": "Bad email or password"}), 401

@authorisation.route('/register', methods=['POST'])
def register():
    if request.is_json:
        email = request.json.get('email', None)
        password = request.json.get('password', None)
    else:
        email = request.form.get('email', None)
        password = request.form.get('password', None)

    if user_datastore.find_user(email=email):
        return jsonify({"msg": "Email already exists"}), 400

    user_datastore.create_user(email=email, password=password, roles=['user'])
    db.session.commit()
    return jsonify({"msg": "User created successfully"}), 201

@authorisation.route('/logout')
@auth_required('token')
def logout():
    # In a token-based auth, the client just needs to discard the token.
    # This endpoint can be used for token invalidation if using a blacklist.
    return jsonify({"msg": "Successfully logged out"}), 200

@authorisation.route('/profile')
@auth_required('token')
def profile():
    return jsonify(email=current_user.email, roles=[role.name for role in current_user.roles])

@authorisation.route('/admin')
@auth_required('token')
@roles_required('admin')
def admin_dashboard():
    return jsonify(message="Welcome Admin!")

@authorisation.route('/user')
@auth_required('token')
@roles_required('user')
def user_dashboard():
    return jsonify(message="Welcome User!")


