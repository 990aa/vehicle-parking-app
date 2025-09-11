import csv
import io
from extensions import celery
@celery.task(name='jobs.export_user_parking_csv')
def export_user_parking_csv(user_id, user_email):
    """
    Celery task: Exports all parking spot usage for a user as CSV and emails a download link or file.
    """
    from app import create_app
    app = create_app()
    with app.app_context():
        from models.reservation import Reservation
        from models.parking_spot import ParkingSpot
        from models.parking_lot import ParkingLot
        user_reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.parking_time.asc()).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Reservation ID', 'Lot Name', 'Spot No', 'Parking Time', 'Leaving Time', 'Vehicle Number', 'Cost', 'Status'])
        for r in user_reservations:
            lot_name = r.spot.parking_lot.prime_location_name if r.spot and r.spot.parking_lot else '-'
            spot_no = r.spot.spot_no if r.spot else '-'
            writer.writerow([
                r.id,
                lot_name,
                spot_no,
                r.parking_time.strftime('%Y-%m-%d %H:%M') if r.parking_time else '-',
                r.leaving_time.strftime('%Y-%m-%d %H:%M') if r.leaving_time else '-',
                r.vehicle_number,
                r.cost if r.cost is not None else '-',
                r.status
            ])
        csv_data = output.getvalue()
        output.close()
        # Email the CSV as an attachment
        msg = Message('Your Parking Spot Usage Export', recipients=[user_email])
        msg.body = 'Attached is your parking spot usage export as requested.'
        msg.attach('parking_spots_export.csv', 'text/csv', csv_data)
        mail.send(msg)
from flask import render_template_string
# Celery task for monthly activity report
@celery.task(name='jobs.send_monthly_activity_report')
def send_monthly_activity_report():
    """
    Celery scheduled task: Sends a monthly HTML activity report to each user via email.
    """
    from app import create_app
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    import io
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

            # Generate PDF report
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            title = Paragraph(f"<b>Monthly Parking Activity Report - {month_name} {year}</b>", styles['Title'])
            elements.append(title)
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Hello {user.username},", styles['Normal']))
            elements.append(Paragraph(f"Here is your parking activity summary for <b>{month_name} {year}</b>:", styles['Normal']))
            elements.append(Spacer(1, 12))
            summary_data = [
                ["Total Bookings", total_bookings],
                ["Most Used Parking Lot", most_used_lot],
                ["Total Amount Spent", f"₹{total_spent:.2f}"]
            ]
            summary_table = Table(summary_data, hAlign='LEFT')
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 18))
            if reservations:
                elements.append(Paragraph("<b>Booking Details:</b>", styles['Heading4']))
                data = [["Date", "Lot", "Spot", "Cost"]]
                for r in reservations:
                    data.append([
                        r.parking_time.strftime('%d-%m-%Y') if r.parking_time else '-',
                        r.spot.parking_lot.prime_location_name if r.spot and r.spot.parking_lot else 'Unknown',
                        r.spot.spot_no if r.spot else '-',
                        f"₹{(r.cost or 0):.2f}"
                    ])
                table = Table(data, hAlign='LEFT')
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                elements.append(table)
            else:
                elements.append(Paragraph("No bookings found for this month.", styles['Normal']))
            elements.append(Spacer(1, 18))
            elements.append(Paragraph("Thank you for using Vehicle Parking App!", styles['Normal']))
            doc.build(elements)
            pdf = buffer.getvalue()
            buffer.close()

            # Email with PDF attachment
            html = f"""
                <h2>Monthly Parking Activity Report - {month_name} {year}</h2>
                <p>Hello {user.username},</p>
                <p>Your monthly activity report is attached as a PDF.</p>
                <p>Thank you for using Vehicle Parking App!</p>
            """
            msg = Message(f"Your {month_name} {year} Parking Activity Report", recipients=[user.email])
            msg.body = f"Dear {user.username},\n\nYour monthly activity report is attached as a PDF.\n\nThank you for using Vehicle Parking App!"
            msg.html = html
            msg.attach(f"Parking_Report_{month_name}_{year}.pdf", "application/pdf", pdf)
            mail.send(msg)
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

