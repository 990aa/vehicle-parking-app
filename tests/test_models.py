from models.user import User, Role
from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot
from flask_security import hash_password
import uuid

def test_user_creation(db):
    user = User(
        username='testuser',
        email='test@example.com',
        password=hash_password('password'),
        active=True,
        fs_uniquifier=str(uuid.uuid4())
    )
    db.session.add(user)
    db.session.commit()

    retrieved_user = User.query.filter_by(email='test@example.com').first()
    assert retrieved_user is not None
    assert retrieved_user.username == 'testuser'

def test_user_role_assignment(db):
    role = Role(name='admin', description='Administrator')
    db.session.add(role)
    db.session.commit()

    user = User(
        username='adminuser',
        email='admin@example.com',
        password='password',
        active=True,
        fs_uniquifier=str(uuid.uuid4())
    )
    user.roles.append(role)
    db.session.add(user)
    db.session.commit()

    retrieved_user = User.query.filter_by(email='admin@example.com').first()
    assert len(retrieved_user.roles) == 1
    assert retrieved_user.roles[0].name == 'admin'

def test_parking_lot_creation(db):
    lot = ParkingLot(
        prime_location_name="Test Lot",
        price_per_hr=10.0,
        address="123 Test St",
        pin_code="12345",
        max_spots=100
    )
    db.session.add(lot)
    db.session.commit()

    assert lot.id is not None
    assert lot.prime_location_name == "Test Lot"

def test_parking_spot_creation(db):
    lot = ParkingLot(
        prime_location_name="Spot Lot",
        price_per_hr=5.0,
        address="456 Spot Ave",
        pin_code="67890",
        max_spots=50
    )
    db.session.add(lot)
    db.session.commit()

    spot = ParkingSpot(
        lot_id=lot.id,
        spot_no=1,
        status='A'
    )
    db.session.add(spot)
    db.session.commit()

    assert spot.id is not None
    assert spot.lot_id == lot.id
    assert spot.spot_no == 1
