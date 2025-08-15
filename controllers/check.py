# things i need for this file
from flask import Blueprint, request, jsonify
# the user data model
from models.user import User

# this is a small controller to check for duplicate usernames and emails
check = Blueprint('check', __name__)

# this is the route that the javascript on the registration page calls
@check.route('/check_duplicate', methods=['POST'])
def check_duplicate():
    # get the username and email from the javascript
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    # check if the username or email already exist in the database
    exists = {'username': False, 'email': False}
    if username:
        
        exists['username'] = User.query.filter_by(username=username).first() is not None
    if email:
        exists['email'] = User.query.filter_by(email=email).first() is not None
    # send back a json response to the javascript
    return jsonify(exists)
