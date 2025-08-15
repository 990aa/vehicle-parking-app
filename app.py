import os
# bring in, flask and stuff
from flask import Flask, redirect, url_for, session
from extensions import db
# for the secret key, dont want that on github
from dotenv import load_dotenv

# make the app, standard stuff
app = Flask(__name__)

load_dotenv()  # load environment variables from .env file
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'  # sqlite for dev, will break if i ever scale this
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # docs said to turn this off, so i did
# gotta have a secret key for sessions, this is a good one i think
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db.init_app(app)  # i always forget this line and then nothing works

# bring in all my data models, need these to talk to the db
from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot
from models.user import User
from models.reservation import Reservation
from models.lot_bookings import LotBooking

# and my controllers, where all the action happens
from controllers.user import user
from controllers.admin import admin
from controllers.authorisation import authorisation
from controllers.check import check


# tell flask about my controllers, so it knows what urls to listen for
# i keep forgetting to register blueprints, then flask can't find my routes

app.register_blueprint(user)
app.register_blueprint(admin)
app.register_blueprint(authorisation)
app.register_blueprint(check)

# this part runs when the app starts up
with app.app_context():
    # create the database tables if they dont exist
    db.create_all()
    # make sure there's always an admin user, so i can log in
    # Create admin user if not exist
    if not User.query.filter_by(username='admin').first():
        
        admin_user = User(username='admin', email='admin@vehiclepark.com', password='adm123', role='admin')
        db.session.add(admin_user)
        db.session.commit()

# this is the first page everyone sees
@app.route('/')

def index():
    # if you're logged in, go to your dashboard
    # If user is logged in, send them to the right dashboard, otherwise login
    if 'user_id' in session:
        # admins go to the admin page
        if session.get('role') == 'admin':
            return redirect(url_for('admin.admin_dashboard'))
        # regular users go to their page
        else:
            return redirect(url_for('user.user_dashboard'))
    # if you're not logged in, you gotta log in
    return redirect(url_for('authorisation.login'))

# if i run this file directly, start the server
if __name__ == '__main__':
    # turn on debug mode, so i can see errors
    # debug true for now, but don't forget to turn off in prod, 
    app.run(debug=True)
# should i add error handlers? probably
# also, sometimes sqlite locks up if i ctrl+c too fast, not sure why, maybe a windows thing
