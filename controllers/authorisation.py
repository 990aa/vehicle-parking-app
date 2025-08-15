
# all the things i need for this file to work
from flask import render_template, flash, redirect, url_for, request, Blueprint, session
# my database helper
from extensions import db
# the user data model
from models.user import User

# this is the authorisation controller, for logging in, out, and registering
authorisation = Blueprint('authorisation', __name__)

# this is for logging out
@authorisation.route('/logout')
def logout():
    # clear the session, so the user is no longer logged in
    session.clear()
    # show a message that they logged out
    flash('You have been logged out.', 'info')
    # send them to the login page
    return redirect(url_for('authorisation.login'))

# this is for creating a new account
@authorisation.route('/register', methods=['GET', 'POST'])
def register():
    # if the form is submitted, try to create the account
    if request.method == 'POST':
        # get the username, email, and password from the form
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        # make sure they typed the password correctly twice
        password_re = request.form.get('reconfirm_password')
        if password_re is not None and password != password_re:
            flash('Passwords do not match', 'error')
            return render_template('register.html', error='Passwords mismatch')
        # check if the username or email is already taken
        if User.query.filter_by(username=username).first() is not None:
            flash('Username already exists', 'error')
        elif User.query.filter_by(email=email).first() is not None:
            flash('Email already exists', 'error')
        else:
            # if everything is good, create the new user
            
            user = User(role='user', username=username, email=email, password=password)
            db.session.add(user)
            db.session.commit()
            # show a success message and send them to the login page
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('authorisation.login'))
    # if it's not a post request, just show the registration form
    return render_template('register.html')

# this is for logging in
@authorisation.route('/login', methods=['GET', 'POST'])
def login():
    # if the form is submitted, try to log them in
    if request.method == 'POST':
        # get the username and password from the form
        username = request.form['username']
        password = request.form['password']
        # check if the username and password are correct
        user = User.query.filter_by(username=username, password=password).first()
        if user is not None:
            # if they are, save their info in the session
            session['user_id'] = user.id
            session['role'] = user.role
            flash(f'Logged in as {user.username}', 'success')
            # if they're an admin, send them to the admin dashboard
            if user.role == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            # otherwise, send them to the user dashboard
            else:
                return redirect(url_for('user.user_dashboard'))
        else:
            # if the username or password was wrong, show an error
            flash('Invalid username or password', 'error')
            return render_template('login.html', error='Invalid credentials')
    # if it's not a post request, just show the login form
    return render_template('login.html')


