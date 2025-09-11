from flask import render_template_string
# Celery task for monthly activity report
@celery.task(name='jobs.send_monthly_activity_report')
def send_monthly_activity_report():
    """
    Celery scheduled task: Sends a monthly HTML activity report to each user via email.
    """
    from app import create_app
    app = create_app()
    with app.app_context():
        from models.user import User
        from models.reservation import Reservation
        from models.parking_lot import ParkingLot
        from sqlalchemy import extract, func
        import calendar
        now = datetime.now()
        year = now.year
        month = now.month - 1 if now.month > 1 else 12
        year = year if now.month > 1 else year - 1
        month_name = calendar.month_name[month]
        users = User.query.all()
        for user in users:
            # Get all completed reservations for this user in the previous month
            reservations = Reservation.query.filter(
                Reservation.user_id == user.id,
                Reservation.status == 'C',
                extract('year', Reservation.parking_time) == year,
                extract('month', Reservation.parking_time) == month
            ).all()
            total_bookings = len(reservations)
            total_spent = sum(r.cost or 0 for r in reservations)
            # Most used lot
            lot_counts = {}
            for r in reservations:
                lot = r.spot_id and r.spot and r.spot.parking_lot
                lot_name = lot.prime_location_name if lot else 'Unknown'
                lot_counts[lot_name] = lot_counts.get(lot_name, 0) + 1
            most_used_lot = max(lot_counts, key=lot_counts.get) if lot_counts else 'N/A'
            # HTML report
            html = render_template_string('''
                <h2>Monthly Parking Activity Report - {{ month_name }} {{ year }}</h2>
                <p>Hello {{ user.username }},</p>
                <p>Here is your parking activity summary for <b>{{ month_name }} {{ year }}</b>:</p>
                <ul>
                    <li><b>Total Bookings:</b> {{ total_bookings }}</li>
                    <li><b>Most Used Parking Lot:</b> {{ most_used_lot }}</li>
                    <li><b>Total Amount Spent:</b> ₹{{ '%.2f' % total_spent }}</li>
                </ul>
                {% if reservations %}
                <h4>Booking Details:</h4>
                <table border="1" cellpadding="5" cellspacing="0">
                    <tr><th>Date</th><th>Lot</th><th>Spot</th><th>Cost</th></tr>
                    {% for r in reservations %}
                    <tr>
                        <td>{{ r.parking_time.strftime('%d-%m-%Y') if r.parking_time else '-' }}</td>
                        <td>{{ r.spot.parking_lot.prime_location_name if r.spot and r.spot.parking_lot else 'Unknown' }}</td>
                        <td>{{ r.spot.spot_no if r.spot else '-' }}</td>
                        <td>₹{{ '%.2f' % (r.cost or 0) }}</td>
                    </tr>
                    {% endfor %}
                </table>
                {% else %}
                <p>No bookings found for this month.</p>
                {% endif %}
                <p>Thank you for using Vehicle Parking App!</p>
            ''', user=user, month_name=month_name, year=year, total_bookings=total_bookings, most_used_lot=most_used_lot, total_spent=total_spent, reservations=reservations)
            send_email(user.email, f"Your {month_name} {year} Parking Activity Report", html, html=True)
from datetime import datetime, timedelta
from flask_mail import Message
from twilio.rest import Client
import requests
import os
from models.user import User
from models.reservation import Reservation 
from extensions import db, mail

from extensions import celery


# Celery task for sending notifications
@celery.task(name='jobs.send_notifications')
def send_notifications():
    """
    Celery task: Sends notifications to users who haven't booked a parking spot recently.
    """
    from app import create_app
    app = create_app()
    with app.app_context():
        users = User.query.filter(User.notification_preference.isnot(None)).all()
        for user in users:
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_reservations = Reservation.query.filter(
                Reservation.user_id == user.id,
                Reservation.start_time > seven_days_ago
            ).count()
            if recent_reservations == 0:
                if user.last_notified is None or user.last_notified < datetime.now() - timedelta(hours=24):
                    if user.notification_preference == 'email':
                        send_email(user.email, 'Parking Reminder', 'You have not booked a parking spot recently. Please book one if you need it.')
                    elif user.notification_preference == 'sms':
                        send_sms(user.notification_contact, 'Parking Reminder: You have not booked a parking spot recently. Please book one if you need it.')
                    elif user.notification_preference == 'gchat':
                        send_gchat(user.notification_contact, 'Parking Reminder: You have not booked a parking spot recently. Please book one if you need it.')
                    user.last_notified = datetime.now()
                    db.session.commit()

def send_email(to, subject, body, html=False):
    """
    Sends an email. If html=True, sends as HTML email.
    """
    msg = Message(subject, recipients=[to], html=body if html else None, body=None if html else body)
    mail.send(msg)

def send_sms(to, body):
    """
    Sends an SMS.
    """
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM_NUMBER')
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=body,
        from_=from_number,
        to=to
    )

def send_gchat(webhook_url, message):
    """
    Sends a message to a Google Chat webhook.
    """
    requests.post(webhook_url, json={'text': message})

