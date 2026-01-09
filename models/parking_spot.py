# my database helper
from extensions import db

# for time stuff
from datetime import datetime


# this is the data model for a single parking spot
class ParkingSpot(db.Model):  # type: ignore
    # the unique id for each spot, don't mess with this
    # id is just the pk, nothing special, but don't change this or everything breaks
    id = db.Column(db.Integer, primary_key=True)
    # which parking lot this spot is in
    # ok so lot_id is a foreign key, but i set unique=True, not sure if that's right, maybe should be False?
    lot_id = db.Column(db.Integer, db.ForeignKey("parking_lot.id"), nullable=False)
    # the number of the spot, like "A1" or "23"
    # spot_no should be unique per lot, but i think this makes it global unique, hmm, might need to fix
    spot_no = db.Column(db.Integer, nullable=False)
    # this makes sure that each spot number is unique within a lot
    __table_args__ = (
        db.UniqueConstraint("lot_id", "spot_no", name="uix_lotid_spotno"),
    )
    # is the spot available or occupied?
    # status is just 'A' or 'O'
    status = db.Column(
        db.String(1), default="A", nullable=False
    )  # A = Available, O = Occupied
    # this connects this table to the reservation table, so i can see who has reserved this spot
    # reservations relationship, i copied this from flask-sqlalchemy docs, hope it's right
    reservations = db.relationship("Reservation", backref="parking_spot")
    # when the spot was created
    # i always forget to set default for time, so now just use datetime.now, but maybe should be utcnow
    time = db.Column(db.DateTime, default=datetime.now, nullable=False)
    # i had a bug where time was None, turns out i forgot default, so don't remove this
