from jobs import export_user_parking_csv
from flask import Blueprint, redirect, url_for, flash, request, render_template, send_file, jsonify
from flask_security import auth_required, current_user
from extensions import db, cache
user = Blueprint('user', __name__)
from models.parking_lot import ParkingLot
from models.reservation import Reservation
from models.parking_spot import ParkingSpot
from models.lot_bookings import LotBooking
from datetime import datetime, date
from math import ceil
import plotly.graph_objs as plt
import plotly.io as pltio


# this is the main user page, the dashboard
@user.route('//dashboard')
@auth_required()
def user_dashboard():
    #import plotly.graph_objs as plt
    #import plotly.io as pltio
    # get the user's id from the session
    user_id = current_user.id
    now = datetime.now()
    # get all the reservations for this user
    all_reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.parking_time.asc()).all()
    # sort the reservations into different lists based on their status
    upcoming, active, completed, cancelled = [], [], [], []
    # get ready to make some charts
    # For chart data
    lot_status_counts = {}  # {lot_name: {status: count}}
    lot_spent = {}  # {lot_name: total_spent}
    # go through each reservation and get the info i need
    for r in all_reservations:
        spot = ParkingSpot.query.get(r.spot_id)
        lot = ParkingLot.query.get(spot.lot_id) if spot else None
        if not lot or not spot:
            continue
        lot_name = lot.prime_location_name
        # count how many reservations of each status there are for each lot
        if lot_name not in lot_status_counts:
            lot_status_counts[lot_name] = {'Completed': 0, 'Cancelled': 0, 'Upcoming': 0, 'Active': 0}
        # count how much money was spent at each lot
        if lot_name not in lot_spent:
            lot_spent[lot_name] = 0.0
        # make the times look nice for the html page
        timein = r.parking_time.strftime('%d-%m-%Y %H:%M') if r.parking_time else "-"
        timeout = r.leaving_time.strftime('%d-%m-%Y %H:%M') if r.leaving_time else "-"
        vehicle_number = r.vehicle_number if hasattr(r, 'vehicle_number') else "-"
        # if the reservation is completed, calculate the cost
        if r.status == 'C':
            # Completed
            if r.parking_time and r.leaving_time:
                delta = r.leaving_time - r.parking_time
                hrs = max(delta.total_seconds() / 3600, 0)
                hrs_ceiled = max(ceil(hrs), 1) if hrs > 0 else 1
                cost = r.cost if isinstance(r.cost, (int, float)) and r.cost > 0 else round(hrs_ceiled * lot.price_per_hr, 2)
                duration = f"{hrs:.2f} (ceiled to {hrs_ceiled}) hrs"
                lot_spent[lot_name] += cost
            else:
                duration = "-"
                cost = 0.0
            # add the reservation to the completed list
            completed.append({
                'id': r.id,
                'lot_name': lot_name,
                'spot_number': spot.spot_no,
                'vehicle_number': vehicle_number,
                'status': r.status,
                'timein': timein,
                'timeout': timeout,
                'duration': duration,
                'cost': f"₹{cost:.2f}" if isinstance(cost, (int, float)) else '-',
            })
            lot_status_counts[lot_name]['Completed'] += 1
        # if the reservation is upcoming, add it to the upcoming list
        elif r.status == 'U':
            # Upcoming
            upcoming.append({
                'id': r.id,
                'lot_name': lot_name,
                'spot_number': spot.spot_no,
                'vehicle_number': vehicle_number,
                'status': r.status,
                'timein': timein,
                'timeout': timeout,
                'duration': '-',
                'cost': '-',  # Only for display, not stored in DB
            })
            lot_status_counts[lot_name]['Upcoming'] += 1
        # if the reservation is active, add it to the active list
        elif r.status == 'A':
            # Active
            if r.leaving_time:
                delta = r.leaving_time - r.parking_time
                hrs = max(delta.total_seconds() / 3600, 0)
                hrs_ceiled = max(ceil(hrs), 1) if hrs > 0 else 1
                cost = r.cost if isinstance(r.cost, (int, float)) and r.cost is not None else round(hrs_ceiled * lot.price_per_hr, 2)
                duration = f"{hrs_ceiled} hrs"
            else:
                duration = "-"
                cost = None
            active.append({
                'id': r.id,
                'lot_name': lot_name,
                'spot_number': spot.spot_no,
                'vehicle_number': vehicle_number,
                'status': r.status,
                'timein': timein,
                'timeout': timeout,
                'duration': duration,
                'cost': f"₹{cost:.2f}" if isinstance(cost, (int, float)) else '-',
            })
            lot_status_counts[lot_name]['Active'] += 1
        # if the reservation is cancelled, add it to the cancelled list
        elif r.status == 'X':
            # Cancelled
            cancelled.append({
                'id': r.id,
                'lot_name': lot_name,
                'spot_number': spot.spot_no,
                'vehicle_number': vehicle_number,
                'status': r.status,
                'date': r.parking_time.strftime('%d-%m-%Y') if r.parking_time else '-',
                'duration': '-',
                'cost': '-',  # Only for display, not stored in DB
            })
            lot_status_counts[lot_name]['Cancelled'] += 1
    # count the total number of bookings and how much money was spent
    total_bookings_count = len(all_reservations)
    sum_spent = sum(float(r['cost'].replace('₹','')) for r in completed if r['cost'] and r['cost'] != '-')

    # this is where i make the pretty stacked bar chart
    # --- Plotly Stacked Bar Chart: Bookings by Status per Lot ---
    lot_names = list(lot_status_counts.keys())
    status_types = ['Completed', 'Cancelled', 'Upcoming', 'Active']
    data = []
    colors = {'Completed': '#4CAF50', 'Cancelled': '#B4413C', 'Upcoming': '#FFC107', 'Active': '#1FB8CD'}
    for status in status_types:
        data.append(plt.Bar(
            x=lot_names,
            y=[lot_status_counts[lot].get(status, 0) for lot in lot_names],
            name=status,
            marker_color=colors[status]
        ))
    stacked_layout = plt.Layout(
        barmode='stack',
        title='Bookings by Status per Lot',
        yaxis=dict(title='Count'),
        xaxis=dict(title='Parking Lot'),
        height=350,
        margin=dict(t=40, b=40, l=40, r=10)
    )
    stacked_fig = plt.Figure(data=data, layout=stacked_layout)
    stacked_plotly = pltio.to_html(stacked_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False})

    # and this is where i make the pretty bar chart for the money
    # --- Plotly Bar Chart: Total Spent per Lot ---
    spent_lot_names = list(lot_spent.keys())
    spent_values = [round(lot_spent[lot], 2) for lot in spent_lot_names]
    spent_fig = plt.Figure(data=[plt.Bar(
        x=spent_lot_names,
        y=spent_values,
        marker_color='#FFC185',
        name='Total Spent (₹)'
    )])
    spent_fig.update_layout(
        yaxis=dict(title='Total Spent (₹)', rangemode='tozero'),
        xaxis=dict(title='Parking Lot'),
        margin=dict(t=40, b=40, l=40, r=10),
        height=350
    )
    spent_plotly = pltio.to_html(spent_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False})

    # count how many active reservations there are
    A_reservation_count = len(active)
    # send all the data to the html page
    return render_template('user_dashboard.html',
        upcoming_reservations=upcoming,
        active_reservations=active,
        completed_reservations=completed,
        cancelled_reservations=cancelled,
        total_bookings_count=total_bookings_count,
        sum_spent=sum_spent,
        total_spent=sum_spent,
        stacked_plotly=stacked_plotly,
        spent_plotly=spent_plotly,
        A_reservation_count=A_reservation_count
    )

# this page is for booking a new spot
@user.route('//booking')
@auth_required()
@cache.cached(timeout=50)
def user_booking():
    from datetime import date
    lots = []
    today = date.today().strftime('%Y-%m-%d')
    # for the date picker
    selected_date = request.args.get('date')
    if not selected_date:
        selected_date = today
    # for the search bar
    lot_query = request.args.get('q', '').strip().lower()
    lot_field = request.args.get('field', 'all')
    selected_dt = None
    try:
        selected_dt = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except Exception:
        selected_dt = date.today()
    if selected_dt < date.today():
        selected_dt = date.today()
        selected_date = today
    for lot in ParkingLot.query.all():
        total_spots = ParkingSpot.query.filter_by(lot_id=lot.id).count()
        lot_booking = LotBooking.query.filter_by(lot_id=lot.id, booking_date=selected_dt).first()
        spots_booked = lot_booking.spots_booked if lot_booking else 0
        # calculate how many spots are available
        avl_spots = total_spots - spots_booked
        # put all the lot info into a dictionary
        lot_dict = {
            'id': lot.id,
            'prime_location_name': lot.prime_location_name,
            'address': lot.address,
            'pin_code': lot.pin_code,
            'max_spots': lot.max_spots,
            'avl_spots': avl_spots,
            'price_per_hr': lot.price_per_hr
        }
        # if i'm searching, only show the lots that match
        match = True
        if lot_query:
            match = False
            if lot_field == 'name':
                match = lot.prime_location_name and lot_query in lot.prime_location_name.lower()
            elif lot_field == 'address':
                match = lot.address and lot_query in lot.address.lower()
            elif lot_field == 'pin_code':
                match = str(lot.pin_code) and lot_query in str(lot.pin_code).lower()
            else:  # all
                match = (
                    lot_query in lot.prime_location_name.lower()
                    or lot_query in lot.address.lower()
                    or lot_query in str(lot.pin_code).lower()
                )
        if match:
            lots.append(lot_dict)
    # send the lots to the html page
    return render_template('user_booking.html', lots=lots, lot_search_query=lot_query, lot_search_field=lot_field, selected_date=selected_date, today=today)

# this is for when a user clicks the "book" button
@user.route('//book_spot/<int:lot_id>', methods=['POST'])
@auth_required()
def book_spot(lot_id):
    # get the user's id and the date they want to book
    user_id = current_user.id
    date_str = request.form.get('date')
    if not date_str:
        flash("Date is required.", 'error')
        return redirect(url_for('user.user_booking'))
    try:
        booking_date = datetime.strptime(date_str, '%Y-%m-%d')
    except Exception:
        flash("Invalid date format.", 'error')
        return redirect(url_for('user.user_booking'))
    # i don't want people booking in the past
    # Only allow today or future dates
    if booking_date.date() < date.today():
        flash("Cannot book for a past date.", 'error')
        return redirect(url_for('user.user_booking'))
    # check if there are any spots available on that date
    # Use LotBooking to check and update spots booked
    total_spots = ParkingSpot.query.filter_by(lot_id=lot_id).count()
    lot_booking = LotBooking.query.filter_by(lot_id=lot_id, booking_date=booking_date.date()).first()
    spots_booked = lot_booking.spots_booked if lot_booking else 0
    if spots_booked >= total_spots:
        flash("No spots available in this lot for the selected date.", "error")
        return redirect(url_for('user.user_booking'))
    # find an available spot that's not already reserved for that date
    # Find an available spot not already reserved for that date
    all_spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
    # Get all reservations for this lot and date (status A or U for that date)
    reserved_spot_ids = [r.spot_id for r in Reservation.query.filter(
        Reservation.spot_id.in_([s.id for s in all_spots]),
        db.func.date(Reservation.parking_time)==booking_date.date(),
        Reservation.status.in_(['A','U'])
    ).all()]
    available_spots = [s for s in all_spots if s.id not in reserved_spot_ids]
    if not available_spots:
        flash("No spots available in this lot for the selected date.", "error")
        return redirect(url_for('user.user_booking'))
    # get the first available spot
    avl_spot = available_spots[0]
    try:
        # get the vehicle number from the form
        vehicle_number = request.form.get('vehicle_number', '').strip()
        if not vehicle_number:
            flash("Vehicle number is required.", 'error')
            return redirect(url_for('user.user_booking'))
        # create a new reservation
        # Set parking_time to selected date at midnight (upcoming). Status 'U' for upcoming.
        parking_time = datetime.combine(booking_date.date(), datetime.min.time())
        reservation = Reservation(user_id=user_id, spot_id=avl_spot.id, status='U', vehicle_number=vehicle_number, parking_time=parking_time, cost=None)
        db.session.add(reservation)
        # update the number of booked spots for that day
        # Update or create LotBooking
        if lot_booking:
            lot_booking.spots_booked += 1
        else:
            lot_booking = LotBooking(lot_id=lot_id, booking_date=booking_date.date(), spots_booked=1)
            db.session.add(lot_booking)
        # save the changes to the database
        db.session.commit()
        flash("Spot booked successfully for the selected date!", 'success')
    except Exception as e:
        # if something goes wrong, undo the changes and show an error
        db.session.rollback()
        flash(f"Error in booking spot \n{str(e)}", "error")
    # go back to the user's dashboard
    return redirect(url_for('user.user_dashboard'))

# this is for when a user arrives at the parking lot and marks their car as parked
@user.route('//mark_parked/<int:reservation_id>', methods=['GET', 'POST'])
@auth_required()
def mark_parked(reservation_id):
    # find the reservation
    reservation = Reservation.query.filter_by(id=reservation_id, user_id=current_user.id).first()
    now = datetime.now()
    # make sure the reservation is upcoming or active
    if reservation and reservation.status in ['U', 'A']:
        try:
            # if it's upcoming, change it to active and set the parking time to now
            # Only move to active if reservation is upcoming (status 'U')
            if reservation.status == 'U':
                reservation.parking_time = now
                reservation.status = 'A'
            # mark the spot as occupied
            spot = ParkingSpot.query.get(reservation.spot_id)
            if spot:
                spot.status = 'O'
            # save the changes
            db.session.commit()
            flash("Marked as parked.", 'success')
        except Exception as e:
            # if something goes wrong, undo the changes and show an error
            db.session.rollback()
            flash(f"Error marking reservation as parked.\n{str(e)}", 'error')
    else:
        # if the reservation is not upcoming or active, show an error
        flash("Cannot mark as parked. Reservation is not upcoming or already active.", 'error')
    # go back to the user's dashboard
    return redirect(url_for('user.user_dashboard'))

# this is for when a user leaves the parking lot and releases their spot
@user.route('//release_spot/<int:reservation_id>', methods = ['GET', 'POST'])
@auth_required()
def release_spot(reservation_id):
    # find the reservation
    reservation = Reservation.query.filter_by(id=reservation_id, user_id=current_user.id).first()
    # make sure the car is actually parked
    # only release if status is A and already parked, otherwise weird stuff happens
    if reservation.status == 'A' and reservation.parking_time:
        # get the spot and lot info
        spot = ParkingSpot.query.get(reservation.spot_id)
        lot = ParkingLot.query.get(spot.lot_id) if spot else None
        if not lot or not spot:
            flash("Spot or lot not found for this reservation", 'error')
            return redirect(url_for('user.user_dashboard'))

        try:
            # set the leaving time to now
            reservation.leaving_time = datetime.now()
            # calculate how long the car was parked
            hrs = max((reservation.leaving_time - reservation.parking_time).total_seconds() / 3600, 0)
            hrs_ceiled = ceil(hrs) if hrs > 0 else 1
            # change the status to completed
            reservation.status = 'C'
            # calculate the cost and save it to the reservation
            # Save cost to reservation.cost for history
            if reservation.parking_time and reservation.leaving_time:
                reservation.cost = round(hrs_ceiled * lot.price_per_hr, 2)
            # mark the spot as available again
            spot.status = 'A'
            # Update LotBooking for the lot and date
            booking_date = reservation.parking_time.date()
            lot_booking = LotBooking.query.filter_by(lot_id=spot.lot_id, booking_date=booking_date).first()
            if lot_booking and lot_booking.spots_booked > 0:
                lot_booking.spots_booked -= 1
            # save the changes
            db.session.commit()
            flash(f"Spot released. Total cost: ₹{reservation.cost:.2f}", 'success')
        except Exception as e:
            # if something goes wrong, undo the changes and show an error
            db.session.rollback()
            # i googled this error once, didn't help, so just show it to user
            flash(f"Error in releasing spot\n{str(e)}", 'error')
    else:
        # if the car is not parked, show an error
        # not sure if this message is clear, but whatever
        flash("Cannot release spot that is not parked or already released.", 'error')
    # go back to the user's dashboard
    return redirect(url_for('user.user_dashboard'))

# this is for when a user cancels a reservation
@user.route('//cancel_reservation/<int:reservation_id>', methods=['POST'])
@auth_required()
def cancel_reservation(reservation_id):
    # find the reservation
    res = Reservation.query.filter_by(id=reservation_id, user_id=current_user.id).first()
    # make sure the reservation is upcoming or active
    if res.status in ['U', 'A']:
        try:
            # change the status to cancelled
            res.status = 'X'
            res.cost = None  # Ensure cost is not set to '-'
            # make the spot available
            spot = ParkingSpot.query.get(res.spot_id)
            if spot:
                spot.status = 'A'
            # update LotBooking for the lot and date
            booking_date = res.parking_time.date()
            lot_booking = LotBooking.query.filter_by(lot_id=spot.lot_id, booking_date=booking_date).first() if spot else None
            if lot_booking and lot_booking.spots_booked > 0:
                lot_booking.spots_booked -= 1
            db.session.commit()
            flash("Reservation cancelled.", 'success')
        except Exception as e:
            # if something goes wrong, undo the changes and show an error
            db.session.rollback()
            flash(f"Error in cancelling reservation\n{str(e)}", 'error')
    else:
        # if the reservation has already started, show an error
        flash("Cannot cancel reservation that is already started or not found.", 'error')
    # go back to the user's dashboard
    return redirect(url_for('user.user_dashboard'))

# this page shows the user's parking history
@user.route('//history')
@auth_required()
def user_history():
    # get the user's id
    user_id = current_user.id
    # i think this order_by is right, but sometimes Reservation.time is None, not sure why
    # for the search bar and filters
    # Filtering logic
    query = request.args.get('q', '').strip().lower()
    field = request.args.get('field', 'all')
    status_filter = request.args.get('status', '').lower()
    # get all the reservations for this user
    reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.parking_time.desc()).all()
    history = []
    # go through each reservation and get the info i need
    for r in reservations:
        spot = ParkingSpot.query.get(r.spot_id)
        lot = ParkingLot.query.get(spot.lot_id) if spot else None
        if not spot or not lot:
            continue
        # make the times look nice for the html page
        # Date, check-in, and check-out times
        if r.parking_time:
            date_str = r.parking_time.strftime('%d-%m-%Y')
            checkin_time = r.parking_time.strftime('%H:%M')
        else:
            date_str = '-'
            checkin_time = '-'
        if r.leaving_time:
            checkout_time = r.leaving_time.strftime('%H:%M')
        else:
            checkout_time = '-'
        vehicle_number = r.vehicle_number if hasattr(r, 'vehicle_number') else "-"
        # only show the times if the car is parked or has left
        # Only show times for active/completed
        if r.status in ['A', 'C']:
            show_times = True
        else:
            show_times = False
        # calculate the duration and cost
        if r.status == 'C' and r.parking_time and r.leaving_time:
            hrs = (r.leaving_time - r.parking_time).total_seconds() / 3600
            hrs_ceiled = max(ceil(hrs), 1) if hrs > 0 else 1
            cost_val = r.cost if hasattr(r, 'cost') and r.cost is not None else round(hrs_ceiled * lot.price_per_hr, 2)
            duration = f"{hrs:.2f} (ceiled to {hrs_ceiled}) hrs"
        elif r.parking_time and r.leaving_time and show_times:
            hrs = (r.leaving_time - r.parking_time).total_seconds() / 3600
            hrs_ceiled = max(ceil(hrs), 1) if hrs > 0 else 1
            cost_val = r.cost if hasattr(r, 'cost') and r.cost is not None else round(hrs_ceiled * lot.price_per_hr, 2)
            duration = f"{hrs_ceiled} hr{'s' if hrs_ceiled != 1 else ''}"
        else:
            cost_val = 0
            duration = "-"
        # put all the info into a dictionary
        rec = {
            'id': r.id,
            'lot_name': lot.prime_location_name,
            'spot_number': spot.spot_no,
            'vehicle_number': vehicle_number,
            'status': r.status,
            'date': date_str,
            'checkin': checkin_time if show_times else '-',
            'checkout': checkout_time if show_times else '-',
            'duration': duration,
            'cost': f"₹{cost_val:.2f}" if r.status == 'C' else (f"₹{cost_val:.2f}" if cost_val else '-')
        }
        # if i'm searching, only show the reservations that match
        # Filtering
        match = True
        if query:
            match = False
            if field == 'id':
                match = query in str(rec['id']).lower()
            elif field == 'location':
                match = rec['lot_name'] and query in rec['lot_name'].lower()
            elif field == 'spot_number':
                match = query in str(rec['spot_number']).lower()
            elif field == 'vehicle_number':
                match = rec['vehicle_number'] and query in rec['vehicle_number'].lower()
            elif field == 'date':
                match = rec['date'] and query in rec['date'].lower()
            elif field == 'checkin':
                match = rec['checkin'] and query in rec['checkin'].lower()
            elif field == 'checkout':
                match = rec['checkout'] and query in rec['checkout'].lower()
            else:  # all
                match = (
                    query in str(rec['id']).lower()
                    or (rec['lot_name'] and query in rec['lot_name'].lower())
                    or query in str(rec['spot_number']).lower()
                    or (rec['vehicle_number'] and query in rec['vehicle_number'].lower())
                    or (rec['date'] and query in rec['date'].lower())
                    or (rec['checkin'] and query in rec['checkin'].lower())
                    or (rec['checkout'] and query in rec['checkout'].lower())
                )
        # if i'm filtering by status, only show the reservations that match
        # Status tag filter
        if status_filter:
            status_map = {
                'active': 'A',
                'completed': 'C',
                'upcoming': 'U',
                'cancelled': 'X'
            }
            if status_map.get(status_filter) and rec['status'] != status_map[status_filter]:
                continue
        if match:
            history.append(rec)
    # send the history to the html page
    return render_template('user_history.html', history=history, search_query=query, search_field=field, status_filter=status_filter)


@user.route('//payment/<int:reservation_id>', methods=['GET', 'POST'])
@auth_required()
def payment(reservation_id):
    reservation = Reservation.query.filter_by(id=reservation_id, user_id=current_user.id).first()
    if not reservation:
        flash('Reservation not found.', 'error')
        return redirect(url_for('user.user_dashboard'))
    spot = ParkingSpot.query.get(reservation.spot_id)
    lot = ParkingLot.query.get(spot.lot_id) if spot else None
    lot_name = lot.prime_location_name if lot else '-'
    spot_no = spot.spot_no if spot else '-'
    amount_due = reservation.cost if reservation.cost is not None else 0
    if request.method == 'POST':
        # Dummy payment processing
        card_number = request.form.get('card_number')
        expiry = request.form.get('expiry')
        cvv = request.form.get('cvv')
        name = request.form.get('name')
        # In real app, validate and process payment here
        flash('Payment successful! Thank you.', 'success')
        return redirect(url_for('user.user_dashboard'))
    return render_template('payment_portal.html', reservation=reservation, lot_name=lot_name, spot_no=spot_no, amount_due=amount_due)



@user.route('//export_csv', methods=['POST'])
@auth_required()
def export_csv():
    export_user_parking_csv.delay(current_user.id, current_user.email)
    flash('Your export is being processed. You will receive an email when it is ready.', 'info')
    return redirect(url_for('user.user_dashboard'))