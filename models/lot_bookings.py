# my database helper
from extensions import db
# for date stuff
from datetime import date

# this table keeps track of how many spots are booked in a lot on a certain day
class LotBooking(db.Model):
    # the name of the table in the database
    __tablename__ = 'lot_bookings'
    # just a unique id for each row
    id = db.Column(db.Integer, primary_key=True)
    # which lot this booking is for
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    # which day this booking is for
    booking_date = db.Column(db.Date, nullable=False)
    # how many spots are booked on this day
    spots_booked = db.Column(db.Integer, nullable=False, default=0)
    
    # this connects this table to the parking lot table
    lot = db.relationship('ParkingLot', backref=db.backref('lot_bookings', lazy=True))
    
    # make sure that each lot can only have one row for each day
    __table_args__ = (db.UniqueConstraint('lot_id', 'booking_date', name='uix_lotid_date'),)
