from flask import render_template, redirect, request, url_for, flash, Blueprint
from flask_security import auth_required, roles_required
# for the pretty charts
import plotly.graph_objs as plt
import plotly.io as pltio
# my database helper
from extensions import db, cache
# all the data models i need to talk to
from models.user import User
from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot
from models.reservation import Reservation
from models.lot_bookings import LotBooking
# for time stuff
from datetime import datetime
# for rounding up numbers
from math import ceil

# this is the admin controller, so all the admin pages are here
admin = Blueprint('admin', __name__)

@admin.route('//dashboard')
@auth_required()
@roles_required('admin')
def admin_dashboard():
    # ok so i wanted to page this but then the chart broke, so just get all for now
    # get all the parking lots from the database
    lots = ParkingLot.query.all()
    # count how many lots, spots, and users i have
    total_lots = ParkingLot.query.count()
    total_spots = ParkingSpot.query.count()
    occupied_spots = ParkingSpot.query.filter_by(status='O').count()
    available_spots = total_spots - occupied_spots
    total_users = User.query.filter_by(role='user').count()
    # get ready to calculate how much money each lot made
    income = []
    lot_names = []
    lot_incomes = []
    total_revenue = 0
    # For sunburst chart, this is for the pretty circle chart
    sunburst_labels = []
    sunburst_parents = []
    sunburst_values = []
    # go through each lot and do some math
    for lot in lots:
        lot_income = 0
        lot_spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
        # count how many spots are full and how many are empty
        occupied = sum(1 for s in lot_spots if s.status == 'O')
        vacant = sum(1 for s in lot_spots if s.status != 'O')
        # this is all for the sunburst chart, making the labels and values
        # Sunburst Lot
        sunburst_labels.append(lot.prime_location_name)
        sunburst_parents.append("")
        sunburst_values.append(len(lot_spots))
        # Sunburst Occupied
        sunburst_labels.append(f"{lot.prime_location_name} - Occupied")
        sunburst_parents.append(lot.prime_location_name)
        sunburst_values.append(occupied)
        # Sunburst Vacant
        sunburst_labels.append(f"{lot.prime_location_name} - Vacant")
        sunburst_parents.append(lot.prime_location_name)
        sunburst_values.append(vacant)
        # now calculate the money for this lot
        # Revenue
        
        reservations = Reservation.query.join(ParkingSpot).filter(ParkingSpot.lot_id == lot.id, Reservation.status == 'C').all()
        for r in reservations:
            if r.parking_time and r.leaving_time:
                
                hrs = ceil((r.leaving_time - r.parking_time).total_seconds() / 3600)
                lot_income += hrs * lot.price_per_hr
        income.append({'lot_id': lot.id, 'prime_location_name': lot.prime_location_name, 'income': round(lot_income, 2)})
        lot_names.append(lot.prime_location_name)
        lot_incomes.append(round(lot_income, 2))
        total_revenue += lot_income

    # this is where i make the pretty circle chart
    # Plotly Sunburst Chart for Occupancy
    sunburst_fig = plt.Figure(data=[plt.Sunburst(
        labels=sunburst_labels,
        parents=sunburst_parents,
        values=sunburst_values,
        branchvalues="total",
        marker=dict(colors=["#1FB8CD" if "Vacant" not in l and "Occupied" not in l else ("#B4413C" if "Occupied" in l else "#4CAF50") for l in sunburst_labels])
    )])
    sunburst_fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=350)
    occupancy_plotly = pltio.to_html(sunburst_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False})

    # and this is where i make the pretty bar chart for the money
    # Plotly Revenue Bar Chart (with total revenue annotation)
    revenue_fig = plt.Figure(data=[plt.Bar(
        x=lot_names,
        y=lot_incomes,
        marker_color='#FFC185',
        name='Revenue (₹)'
    )])
    revenue_fig.add_annotation(
        text=f"Total Revenue: ₹{round(total_revenue,2)}",
        xref="paper", yref="paper",
        x=0.5, y=1.1, showarrow=False,
        font=dict(size=16, color="#333"),
        align="center"
    )
    revenue_fig.update_layout(
        yaxis=dict(title='Revenue (₹)', rangemode='tozero'),
        xaxis=dict(title='Lot'),
        margin=dict(t=40, b=40, l=40, r=10),
        height=350
    )
    revenue_plotly = pltio.to_html(revenue_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False})

    # get all the reservations and sort them into different lists
    # --- Reservation tables for admin ---
    # Active: status='A', Completed: status='C', Upcoming: status='U' and parking_time in future
    from sqlalchemy import and_, or_ 
    now = datetime.now()
    active_reservations = Reservation.query.filter(
        and_(Reservation.status == 'A', Reservation.parking_time <= now)
    ).order_by(Reservation.parking_time.desc()).all()
    completed_reservations = Reservation.query.filter(
        Reservation.status == 'C'
    ).order_by(Reservation.parking_time.desc()).all()
    from sqlalchemy import func
    today = now.date()
    upcoming_reservations = Reservation.query.filter(
        and_(
            Reservation.status == 'U',
            func.date(Reservation.parking_time) >= today
        )
    ).order_by(Reservation.parking_time.asc()).all()
    # Add booking_date for each upcoming reservation
    upcoming_reservations_with_date = []
    for r in upcoming_reservations:
        booking_date = r.parking_time.strftime('%d-%m-%Y') if r.parking_time else '-'
        upcoming_reservations_with_date.append({
            'reservation': r,
            'booking_date': booking_date
        })
    cancelled_reservations = Reservation.query.filter(
        Reservation.status == 'X'
    ).order_by(Reservation.parking_time.desc()).all()

    # Calculate cost for completed reservations
    for r in completed_reservations:
        cost = None
        if r.leaving_time and r.parking_time and r.parking_spot and r.parking_spot.parking_lot:
            total_seconds = (r.leaving_time - r.parking_time).total_seconds()
            hrs = int(total_seconds // 3600 + (1 if total_seconds % 3600 > 0 else 0))
            cost = hrs * r.parking_spot.parking_lot.price_per_hr
        r.cost = cost if cost is not None else None
    return render_template(
        'admin_dashboard.html',
        total_lots=total_lots,
        total_spots=total_spots,
        occupied_spots=occupied_spots,
        total_users=total_users,
        income=income,
        occupancy_plotly=occupancy_plotly,
        revenue_plotly=revenue_plotly,
        active_reservations=active_reservations,
        completed_reservations=completed_reservations,
        upcoming_reservations=upcoming_reservations_with_date,
        cancelled_reservations=cancelled_reservations
    )


# this page shows all the users
@admin.route('//users')
@auth_required()
@roles_required('admin')
@cache.cached(timeout=50)
def admin_users():
    # this is for the search bar, so i can find users
    query = request.args.get('q', '').strip().lower()
    field = request.args.get('field', 'all')
    users = []
    # get all the users from the database
    for user in User.query.order_by(User.id).all():
        # count all reservations for this user (upcoming, active, completed, cancelled)
        total_reservations = Reservation.query.filter(Reservation.user_id == user.id).count()
        # put all the user info into a dictionary
        user_dict = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'created_at': user.time.strftime('%d-%m-%Y') if hasattr(user, 'time') else '',
            'total_reservations': total_reservations
        }
        # if i'm searching for something, only show the users that match
        if query:
            match = False
            if field == 'id':
                match = query in str(user.id).lower()
            elif field == 'username':
                match = user.username and query in user.username.lower()
            elif field == 'email':
                match = user.email and query in user.email.lower()
            else:  # all
                match = (
                    query in str(user.id).lower()
                    or (user.username and query in user.username.lower())
                    or (user.email and query in user.email.lower())
                )
            if match:
                users.append(user_dict)
        else:
            # if i'm not searching, show all the users
            users.append(user_dict)
    # send the users to the html page
    return render_template('admin_users.html', users=users, search_query=query, search_field=field)

# this page shows all the parking history for one user
# Admin: View user activity/history
@admin.route('//user/<int:user_id>/activity')
@auth_required()
@roles_required('admin')
def admin_user_activity(user_id):
    # find the user in the database
    user = User.query.get(user_id)
    # if the user doesn't exist, show an error
    if not user:
        flash("User not found.", 'error')
        return redirect(url_for('admin.admin_users'))
    
    # get all the reservations for this user
    from datetime import datetime
    reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.parking_time.desc()).all()
    now = datetime.now()
    # Calculate cost for each reservation
    for r in reservations:
        cost = None
        if r.leaving_time and r.parking_time and r.parking_spot and r.parking_spot.parking_lot:
            total_seconds = (r.leaving_time - r.parking_time).total_seconds()
            hrs = int(total_seconds // 3600 + (1 if total_seconds % 3600 > 0 else 0))
            cost = hrs * r.parking_spot.parking_lot.price_per_hr
        r.cost = cost if cost is not None else None
    # Calculate total cost earned from this user (completed only)
    total_earned = sum(r.cost for r in reservations if isinstance(r.cost, (int, float)) and r.status == 'C')
    # send the data to the html page
    return render_template('admin_user_activity.html', user=user, reservations=reservations, now=now, total_earned=total_earned)

# this is for deleting a user
@admin.route('//users/delete/<int:user_id>', methods=['POST'])
@auth_required()
@roles_required('admin')
def delete_user(user_id):
    # find the user to delete
    user = User.query.get(user_id)
    # i don't want to delete other admins, so i check for that
    # Don't allow deleting admins (for now). Could add a confirmation step.
    if user.role != 'user':
        return redirect(url_for('admin.admin_dashboard'))
    # delete the reservations associated with the user
    reservations = Reservation.query.filter_by(user_id=user_id).all()
    for reservation in reservations:
        db.session.delete(reservation)
    # delete the user from the database
    db.session.delete(user)
    db.session.commit()
    # go back to the main admin page
    return redirect(url_for('admin.admin_dashboard'))

# this page is for creating a new parking lot
@admin.route('//lots/create', methods=['GET', 'POST'])
@auth_required()
@roles_required('admin')
def create_lot():
    # if the form is submitted, create the lot
    if request.method == 'POST':
        try:
            # get all the info from the form
            new_lot = ParkingLot(
                prime_location_name=request.form['prime_location_name'],
                address=request.form['address'],
                pin_code=request.form['pin_code'],
                price_per_hr=float(request.form['price_per_hr']),
                max_spots=int(request.form['max_spots'])
            )
            # add the new lot to the database
            db.session.add(new_lot)
            db.session.flush()
            # create all the parking spots for the new lot
            for i in range(1, new_lot.max_spots + 1):
                spot = ParkingSpot(lot_id=new_lot.id, spot_no=i, status='A')
                db.session.add(spot)
            db.session.commit()
            # show a success message
            flash("New parking lot created successfully!", 'success')
            # go to the list of all lots
            return redirect(url_for('admin.lots'))
        except Exception as e:
            # if something goes wrong, undo the changes and show an error
            db.session.rollback()
            flash(f"Error in creating new parking lot \n{str(e)}", 'error')
            return render_template('manage_lot.html')
    # if it's not a post request, just show the form
    return render_template('manage_lot.html')


# this page shows all the parking lots
@admin.route('//lots')
@auth_required()
@roles_required('admin')
@cache.cached(timeout=50)
def lots():
    # for the search bar
    query = request.args.get('q', '').strip().lower()
    field = request.args.get('field', 'all')
    # for the date picker
    selected_date = request.args.get('date')
    from datetime import date, datetime
    today = date.today().strftime('%Y-%m-%d')
    if not selected_date:
        selected_date = today
    try:
        selected_dt = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except Exception:
        selected_dt = date.today()
    lots = []
    # get all the lots from the database
    for lot in ParkingLot.query.order_by(ParkingLot.id).all():
        # see how many spots are booked for the selected date
        lot_booking = LotBooking.query.filter_by(lot_id=lot.id, booking_date=selected_dt).first()
        spots_booked = lot_booking.spots_booked if lot_booking else 0
        # calculate how many spots are available
        avl_spots = lot.max_spots - spots_booked
        # put all the lot info into a dictionary
        lot_dict = {
            'id': lot.id,
            'prime_location_name': lot.prime_location_name,
            'address': lot.address,
            'pin_code': lot.pin_code,
            'price_per_hr': lot.price_per_hr,
            'max_spots': lot.max_spots,
            'avl_spots': avl_spots
        }
        # if i'm searching, only show the lots that match
        match = True
        if query:
            match = False
            if field == 'id':
                match = query in str(lot.id).lower()
            elif field == 'name':
                match = lot.prime_location_name and query in lot.prime_location_name.lower()
            elif field == 'address':
                match = lot.address and query in lot.address.lower()
            elif field == 'pincode':
                match = str(lot.pin_code) and query in str(lot.pin_code).lower()
            else:  # all
                match = (
                    query in str(lot.id).lower()
                    or (lot.prime_location_name and query in lot.prime_location_name.lower())
                    or (lot.address and query in lot.address.lower())
                    or (str(lot.pin_code) and query in str(lot.pin_code).lower())
                )
        if match:
            lots.append(lot_dict)
    # send the lots to the html page
    return render_template('admin_lots.html', lots=lots, search_query=query, search_field=field, selected_date=selected_date, today=today)


# this is for deleting a parking lot
@admin.route('//lots/delete/<int:lot_id>', methods=['POST'])
@auth_required()
@roles_required('admin')
def delete_lot(lot_id):
    # find the lot to delete
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        flash("Parking lot not found.", 'error')
        return redirect(url_for('admin.lots'))

    # Check for any reservations for any spot in this lot
    from models.reservation import Reservation
    from models.parking_spot import ParkingSpot
    from models.lot_bookings import LotBooking

    reservations = Reservation.query.join(ParkingSpot).filter(ParkingSpot.lot_id == lot_id).all()
    if reservations:
        # Only allow deletion if all reservations are cancelled or completed
        if not all(r.status in ['C', 'X'] for r in reservations):
            flash("Lot can't be deleted if it has active or upcoming reservations.", 'error')
            return redirect(url_for('admin.lots'))

    # i don't want to delete a lot if there are cars in it, so i check for that
    spots_occupied = ParkingSpot.query.filter_by(lot_id=lot_id, status='O').count()
    if spots_occupied > 0:
        flash("Lot cannot be deleted because it contains occupied spots.", 'error')
        return redirect(url_for('admin.lots'))

    try:
        # Delete associated reservations
        for reservation in reservations:
            db.session.delete(reservation)

        # Delete associated lot bookings
        lot_bookings = LotBooking.query.filter_by(lot_id=lot_id).all()
        for booking in lot_bookings:
            db.session.delete(booking)

        # Delete associated parking spots
        parking_spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
        for spot in parking_spots:
            db.session.delete(spot)

        # Now, delete the lot itself
        db.session.delete(lot)
        
        db.session.commit()
        flash("Parking lot and all its associated data deleted successfully!", 'success')
    except Exception as e:
        # if something goes wrong, show an error
        db.session.rollback()
        flash(f"Error in deleting lot.\n{str(e)}", 'error')
    # go back to the list of lots
    return redirect(url_for('admin.lots'))


# this page is for editing a parking lot
@admin.route('//lots/edit/<int:lot_id>', methods=['GET', 'POST'])
@auth_required()
@roles_required('admin')
def edit_lot(lot_id):
    # find the lot to edit
    lot = ParkingLot.query.get(lot_id)
    # if the form is submitted, update the lot
    if request.method == 'POST':
        try:
            # get the old and new number of spots
            old_max_spots = lot.max_spots
            new_max_spots = int(request.form['max_spots'])
            # update the lot info from the form
            lot.prime_location_name = request.form['prime_location_name']
            lot.address = request.form['address']
            lot.pin_code = request.form['pin_code']
            lot.price_per_hr = float(request.form['price_per_hr'])
            lot.max_spots = new_max_spots
            # if the number of spots changed, add or remove spots
            current_spots = ParkingSpot.query.filter_by(lot_id=lot_id).count()
            if new_max_spots < current_spots:
                # if we're removing spots, make sure they're not occupied
                spots_to_remove = ParkingSpot.query.filter(ParkingSpot.lot_id == lot_id, ParkingSpot.spot_no > new_max_spots).all()
                if any(spot.status == 'O' for spot in spots_to_remove):
                    flash(f'Cannot remove spots. Spots {", ".join(str(spot.spot_no) for spot in spots_to_remove if spot.status == "O")} are occupied.', 'error')
                    db.session.rollback()
                    return redirect(url_for('admin.lots'))
                # also make sure there are no active reservations for the spots we're removing
                for spot in spots_to_remove:
                    if Reservation.query.filter_by(spot_id=spot.id, status='A').count() > 0:
                        flash(f'Cannot remove spot #{spot.spot_no} with active reservations.', 'error')
                        db.session.rollback()
                        return redirect(url_for('admin.lots'))
                    db.session.delete(spot)
            elif new_max_spots > old_max_spots:
                # if we're adding spots, create them
                for i in range(old_max_spots + 1, new_max_spots + 1):
                    new_spot = ParkingSpot(lot_id=lot.id, spot_no=i, status='A')
                    db.session.add(new_spot)
            # save the changes to the database
            db.session.commit()
            flash('Parking lot updated successfully!', 'success')
            return redirect(url_for('admin.lots'))
        except Exception as e:
            # if something goes wrong, undo the changes and show an error
            db.session.rollback()
            flash(f'Error in updating parking lot.\n{str(e)}', 'error')
            return render_template('manage_lot.html', lot=lot, edit_mode=True)
    # if it's not a post request, just show the form with the lot's info
    # GET request: render manage_lot.html with lot data
    return render_template('manage_lot.html', lot=lot, edit_mode=True)

# this is for adding a new spot to a lot
# parking spot management (moved from admin_spots.py)
@admin.route('//lot/<int:lot_id>/add_spot', methods=['POST'])
@auth_required()
@roles_required('admin')
def add_spot(lot_id):
    # find the lot to add a spot to
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        flash('Parking lot not found.', 'error')
        return redirect(url_for('admin.lots'))
    # find the highest spot number and add one to it
    # Find the max spot_no for this lot
    max_spot = db.session.query(db.func.max(ParkingSpot.spot_no)).filter_by(lot_id=lot_id).scalar() or 0
    new_spot = ParkingSpot(lot_id=lot_id, spot_no=max_spot + 1, status='A')
    # add the new spot to the database
    db.session.add(new_spot)
    lot.max_spots += 1
    db.session.commit()
    flash('New spot added successfully.', 'success')
    # go back to the list of spots for this lot
    return redirect(url_for('admin.view_spots', lot_id=lot_id))

# this page shows all the spots in a lot
@admin.route('//lot/<int:lot_id>/spots')
@auth_required()
@roles_required('admin')
def view_spots(lot_id):
    # find the lot we're looking at
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        flash('Parking lot not found.', 'error')
        return redirect(url_for('admin.lots'))
    # for the search bar and filters
    query = request.args.get('q', '').strip().lower()
    field = request.args.get('field', 'all')
    status_filter = request.args.get('status', '').lower()
    selected_date = request.args.get('date')
    from datetime import date, datetime
    today = date.today().strftime('%Y-%m-%d')
    if not selected_date:
        selected_date = today
    try:
        selected_dt = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except Exception:
        selected_dt = date.today()
    spots = []
    # get all the spots for this lot
    all_spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
    for spot in all_spots:
        # check if this spot is booked for the selected date
        # For this spot, check if it is booked on selected date
        reservation_on_date = Reservation.query.filter(
            Reservation.spot_id == spot.id,
            db.func.date(Reservation.parking_time) == selected_dt,
            Reservation.status.in_(['A', 'U'])
        ).first()
        is_occupied = reservation_on_date is not None
        vehicle_number = reservation_on_date.vehicle_number if is_occupied and hasattr(reservation_on_date, 'vehicle_number') else '-'
        # get all the dates this spot is booked
        # Get all dates this spot is occupied
        occupied_dates = [r.parking_time.strftime('%Y-%m-%d') for r in Reservation.query.filter_by(spot_id=spot.id).filter(Reservation.status.in_(['A','U','C'])).all()]
        # put all the spot info into a dictionary
        spot_dict = {
            'id': spot.id,
            'spot_no': spot.spot_no,
            'is_occupied': is_occupied,
            'vehicle_number': vehicle_number,
            'occupied_dates': occupied_dates,
            'reservations': getattr(spot, 'reservations', [])
        }
        # if i'm filtering by status, only show the spots that match
        # Status filter (available/occupied)
        if status_filter:
            if status_filter == 'available' and is_occupied:
                continue
            if status_filter == 'occupied' and not is_occupied:
                continue
        # if i'm searching, only show the spots that match
        if query:
            match = False
            if field == 'spot_no':
                match = query in str(spot.spot_no).lower()
            elif field == 'vehicle_number':
                match = vehicle_number and query in vehicle_number.lower()
            else:  # all
                match = (
                    query in str(spot.spot_no).lower()
                    or (vehicle_number and query in vehicle_number.lower())
                )
        else:
            match = True
        if match:
            spots.append(spot_dict)
    # send the spots to the html page
    return render_template('admin_spots.html', lot=lot, spots=spots, search_query=query, search_field=field, selected_date=selected_date, today=today)

# this page shows the history of a single parking spot
# Admin: View full history of a parking spot
@admin.route('//spot/<int:spot_id>')
@auth_required()
@roles_required('admin')
def spot_history(spot_id):
    # find the spot we're looking at
    spot = ParkingSpot.query.get(spot_id)
    if not spot:
        flash('Parking spot not found.', 'error')
        return redirect(url_for('admin.lots'))
    
    # get all the info we need about the spot's history
    from models.user import User
    from models.reservation import Reservation
    from datetime import datetime
    now = datetime.now()
    # Get all reservations for this spot
    reservations = Reservation.query.filter_by(spot_id=spot_id).order_by(Reservation.parking_time.desc()).all()
    # Categorize all reservations properly
    active = []
    completed = []
    upcoming = []
    cancelled = []
    for r in reservations:
        user = User.query.get(r.user_id)
        lot = ParkingLot.query.get(spot.lot_id)
        parking_time_str = r.parking_time.strftime('%d-%m-%Y %H:%M') if r.parking_time else '-'
        booking_date_str = r.parking_time.strftime('%d-%m-%Y') if r.parking_time else '-'
        leaving_time_str = r.leaving_time.strftime('%d-%m-%Y %H:%M') if r.leaving_time else '-'
        duration = '-'
        cost = '-'
        if r.parking_time and r.leaving_time and lot:
            delta = r.leaving_time - r.parking_time
            hrs = max(delta.total_seconds() / 3600, 0)
            hrs_ceiled = max(ceil(hrs), 1) if hrs > 0 else 1
            cost_val = r.cost if hasattr(r, 'cost') and r.cost else round(hrs_ceiled * lot.price_per_hr, 2)
            duration = f"{hrs_ceiled} hr{'s' if hrs_ceiled != 1 else ''}"
            cost = f"₹{cost_val:.2f}" if cost_val else '-'
        res_info = {
            'username': user.username if user else '',
            'email': user.email if user else '',
            'vehicle_number': getattr(r, 'vehicle_number', ''),
            'parking_time': parking_time_str,
            'booking_date': booking_date_str,
            'leaving_time': leaving_time_str,
            'status': r.status,
            'duration': duration,
            'cost': cost
        }
        if r.status == 'A':
            active.append(res_info)
        elif r.status == 'C':
            completed.append(res_info)
        elif r.status == 'U':
            upcoming.append(res_info)
        elif r.status == 'X':
            cancelled.append(res_info)
    # send the data to the html page
    return render_template('admin_spot_history.html', spot=spot, active=active, completed=completed, upcoming=upcoming, cancelled=cancelled)

# this is for deleting a parking spot
@admin.route('//spot/delete/<int:spot_id>', methods=['POST'])
@auth_required()
@roles_required('admin')
def delete_spot(spot_id):
    # find the spot to delete
    spot = ParkingSpot.query.get(spot_id)
    if not spot:
        flash('Parking spot not found.', 'error')
        return redirect(request.referrer or url_for('admin.lots'))
    # i can't delete a spot if it's occupied
    if spot.status != 'A':
        flash('Cannot delete spot: spot is occupied.', 'error')
        return redirect(request.referrer or url_for('admin.lots'))
    # i also can't delete a spot if it has reservations
    # Prevent deletion if any reservation references this spot
    from models.reservation import Reservation
    reservations = Reservation.query.filter_by(spot_id=spot_id).all()
    if reservations:
        flash('Cannot delete spot with reservations.', 'error')
        return redirect(request.referrer or url_for('admin.lots'))
    # get the lot and decrement max_spots
    lot = ParkingLot.query.get(spot.lot_id)
    db.session.delete(spot)
    if lot and lot.max_spots > 0:
        lot.max_spots -= 1
    db.session.commit()
    flash('Parking spot deleted successfully.', 'success')
    # go back to where i was before
    return redirect(request.referrer or url_for('admin.lots'))

# Revenue records page for admin
@admin.route('//revenue')
@auth_required()
@roles_required('admin')
def revenue():
    # Get all completed reservations (status 'C')
    completed_reservations = Reservation.query.filter_by(status='C').all()
    revenue_records = []
    total_revenue = 0
    for r in completed_reservations:
        cost = 0
        if r.parking_time and r.leaving_time and r.parking_spot and r.parking_spot.parking_lot:
            hrs = ceil((r.leaving_time - r.parking_time).total_seconds() / 3600)
            cost = hrs * r.parking_spot.parking_lot.price_per_hr
        total_revenue += cost
        revenue_records.append({
            'id': r.id,
            'user': r.user,
            'parking_spot': r.parking_spot,
            'parking_time': r.parking_time,
            'leaving_time': r.leaving_time,
            'cost': cost
        })
    return render_template('revenue.html', revenue_records=revenue_records, total_revenue=total_revenue)
