from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import User, Period, Symptoms
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
 

auth = Blueprint('auth', __name__)
periods_data = []

@auth.route('/login' , methods=['GET' , 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist', category='error')

    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up' , methods=['GET' , 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        if len(email) < 4:
            flash('Email must be greater than 4 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif len(last_name) < 2:
            flash('Last name must be greater than 1 character.', category='error')    
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least than 7 characters.', category='error')
        else:
            new_user = User(email=email, first_name=first_name, last_name=last_name, password=generate_password_hash(password1, method='pbkdf2:sha256:6000'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", user=current_user)

#@auth.route('/calendar')
#def calendar():
#    return render_template("calendar.html", user=current_user)

@auth.route('/calendar', methods=['GET', 'POST'])
@login_required
def calendar():
    if request.method == 'POST':
        if 'start_period' in request.form:
            start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()

            # Check if a period with the same start date already exists
            existing_period = Period.query.filter_by(start_date=start_date, user_id=current_user.id).first()
            if existing_period:
                flash('A period entry for this date already exists.', category='error')
            else:
                end_date = None  
                period = Period(start_date=start_date, end_date=end_date, user_id=current_user.id)
                db.session.add(period)
                db.session.commit()
                return redirect(url_for('auth.calendar'))


        elif 'end_period' in request.form:
            period_id = request.form.get('period_id')

            if period_id is not None:
                try:
                    period_id = int(period_id)
                except ValueError:
                    flash('Invalid period_id. Must be an integer.', category='error')
                    return redirect(url_for('auth.calendar'))

                end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
                period = Period.query.get(period_id)

                if period and period.user_id == current_user.id:
                    period.end_date = end_date
                    db.session.commit()
                else:
                    flash('Invalid period_id or unauthorized access.', category='error')

            else:
                flash('Missing period_id in form data.', category='error')

            return redirect(url_for('auth.calendar'))

    periods = Period.query.filter_by(user_id=current_user.id).all()
    
    current_date = datetime.now().date()
    predicted_next_period_start = calculate_predicted_next_period(periods)
    days_until_next_period = calculate_days_until_next_period(predicted_next_period_start)
    symptom_options = ['Cramps','Bloating', 'Acne', 'Bodyaches', 'Nausea', 'Spotting']

    return render_template('calendar.html', symptom_options=symptom_options, periods=periods, current_date=current_date,
                           predicted_next_period_start=predicted_next_period_start,
                           days_until_next_period=days_until_next_period)

def calculate_days_until_next_period(predicted_next_period_start):
    if predicted_next_period_start:
        current_date = datetime.now().date()
        days_until_next_period = (predicted_next_period_start - current_date).days
        return max(0, days_until_next_period)
    return None

def calculate_predicted_next_period(periods):
    # Order periods by start date in ascending order
    ordered_periods = sorted(periods, key=lambda period: period.start_date)

    if len(ordered_periods) >= 1:
        latest_period_start = ordered_periods[-1].start_date

        # Calculate the cycle length based on the latest period
        if len(ordered_periods) >= 2:
            previous_period_start = ordered_periods[-2].start_date
            cycle_length = (latest_period_start - previous_period_start).days
        else:
            # Use a default cycle length of 27 days if there's only one period entry
            cycle_length = 27

        # Project the next period start date based on the latest period
        predicted_next_period_start = latest_period_start + timedelta(days=cycle_length)
    else:
        # Use a default projected start date if there are no period entries
        predicted_next_period_start = datetime.now().date() + timedelta(days=27)

    return predicted_next_period_start

@auth.route('/add_symptom', methods=['POST'])
def add_symptom():
    if request.method == 'POST':
        period_id = request.form.get('period_id')
        symptoms = request.form.getlist('symptoms[]')

        if period_id and symptoms:
            period = Period.query.get(period_id)

            if period:
                existing_symptoms = Symptoms.query.filter(Symptoms.period_id == period.id, Symptoms.symptom.in_(symptoms)).all()

                for symptom in symptoms:
                    if symptom not in [existing.symptom for existing in existing_symptoms]:
                        new_symptom = Symptoms(symptom=symptom, period=period)
                        db.session.add(new_symptom)

                db.session.commit()
                flash('Symptoms added successfully!', 'success')
            else:
                flash('Invalid period ID!', 'error')
        else:
            flash('Invalid request parameters!', 'error')

    return redirect(url_for('auth.calendar'))
