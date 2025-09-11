from datetime import datetime, timedelta
from flask_mail import Message
from twilio.rest import Client
import requests
import os
from models.user import User
from models.reservation import Reservation 
from extensions import db, mail
from apscheduler.schedulers.background import BackgroundScheduler

def send_notifications(app):
    """
    Sends notifications to users who haven't booked a parking spot recently.
    """
    with app.app_context():
        users = User.query.filter(User.notification_preference.isnot(None)).all()
        for user in users:
            # Check if the user has any reservations in the last 7 days
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_reservations = Reservation.query.filter(
                Reservation.user_id == user.id,
                Reservation.start_time > seven_days_ago
            ).count()

            if recent_reservations == 0:
                # Check if a notification has been sent in the last 24 hours
                if user.last_notified is None or user.last_notified < datetime.now() - timedelta(hours=24):
                    if user.notification_preference == 'email':
                        send_email(user.email, 'Parking Reminder', 'You have not booked a parking spot recently. Please book one if you need it.')
                    elif user.notification_preference == 'sms':
                        send_sms(user.notification_contact, 'Parking Reminder: You have not booked a parking spot recently. Please book one if you need it.')
                    elif user.notification_preference == 'gchat':
                        send_gchat(user.notification_contact, 'Parking Reminder: You have not booked a parking spot recently. Please book one if you need it.')
                    
                    user.last_notified = datetime.now()
                    db.session.commit()

def send_email(to, subject, body):
    """
    Sends an email.
    """
    msg = Message(subject, recipients=[to], body=body)
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

def schedule_jobs(app):
    """
    Initializes and starts the scheduler.
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=send_notifications, args=[app], trigger="cron", hour=8)
    scheduler.start()