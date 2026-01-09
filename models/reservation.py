# my database helper
from extensions import db
# for time stuff


# this is the data model for a reservation
class Reservation(db.Model):  # type: ignore
    # the unique id for each reservation, don't touch it
    # id is just the pk, nothing special, don't touch
    id = db.Column(db.Integer, primary_key=True)
    # which spot this reservation is for
    # spot_id links to parking_spot, but i always forget which table name to use, flask figures it out
    spot_id = db.Column(db.Integer, db.ForeignKey("parking_spot.id"), nullable=False)
    # which user made this reservation
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    # when the user wants to park
    # parking_time is the requested booking start datetime (user-selected)
    parking_time = db.Column(db.DateTime, nullable=False)
    # when the user actually parked
    # checkin_time is when user actually marks as parked
    checkin_time = db.Column(db.DateTime, nullable=True)
    # when the user left
    # leaving_time is when user actually leaves (set when released)
    leaving_time = db.Column(db.DateTime, nullable=True)
    # how much the reservation cost
    cost = db.Column(db.Float, nullable=True)
    # the license plate of the car
    vehicle_number = db.Column(db.String(20), nullable=False)
    # the status of the reservation
    # status: U = upcoming, A = active, C = completed, X = cancelled
    status = db.Column(db.String(1), default="U", nullable=False)
    # removed  'time' field;  parking_time for booking slot
