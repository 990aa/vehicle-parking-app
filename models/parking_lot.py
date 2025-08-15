# my database helper
from extensions import db
# for time stuff
from datetime import datetime

# this is the data model for a parking lot
class ParkingLot(db.Model):
    # the unique id for each parking lot, simple enough
    # ok so id is just the primary key, nothing fancy here
    id = db.Column(db.Integer, primary_key=True)
    # the name of the parking lot, like "downtown parking"
    # i keep forgetting if this should be unique, but for now just not null
    prime_location_name = db.Column(db.String(100), nullable=False)
    # how much it costs to park here for an hour
    price_per_hr = db.Column(db.Float, nullable=False)  # should this be decimal? float is easier, but maybe rounding issues
    # the address of the parking lot
    address = db.Column(db.String(100), nullable=False)
    # the pin code for the address
    pin_code = db.Column(db.String(10), nullable=False)  # i think 10 is enough, but what if someone has a weird pin
    # when the parking lot was created
    # i used datetime.now instead of utcnow, hope that's fine, but maybe timezone bugs later
    time = db.Column(db.DateTime, default = datetime.now, nullable=False)
    # how many spots are in this lot
    max_spots = db.Column(db.Integer, nullable=False)  # i had a bug where this was 0, so now always check in forms
    # this connects this table to the parking spot table, so i can get all the spots for a lot
    # this relationship thing, i copied from stackoverflow, not sure if cascade is right, but seems to work
    spots = db.relationship('ParkingSpot', backref='parking_lot', cascade="all, delete-orphan")
    # i tried lazy='dynamic' once but then broke my queries, so just leave it default
    