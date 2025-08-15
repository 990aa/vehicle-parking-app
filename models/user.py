# my database helper
from extensions import db
# for time stuff
from datetime import datetime

# this is the data model for a user
class User(db.Model):
    # the unique id for each user
    id = db.Column(db.Integer, primary_key=True)
    # the user's username, has to be unique
    username = db.Column(db.String(50), unique=True, nullable=False)
    # the user's email, also has to be unique
    email = db.Column(db.String(100), unique=True, nullable=False)
    # the user's password, i should probably hash this but i'm lazy
    password = db.Column(db.String(50), nullable=False)
    # is the user an admin or a regular user?
    role = db.Column(db.String(5), default = "user", nullable=False)
    # when the user was created
    time = db.Column(db.DateTime, default=datetime.now)
    # this connects this table to the reservation table, so i can see all of a user's reservations
    reservations = db.relationship('Reservation', backref='user')
    
