from flask import Blueprint, render_template, request, flash, redirect, url_for
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
def calendar():
    if request.method == 'POST':
        if 'start_period' in request.form:
            start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            end_date = None  # You can handle the end_date logic similarly
            period = Period(start_date=start_date, end_date=end_date)
            db.session.add(period)
            db.session.commit()
            return redirect(url_for('auth.calendar'))
    elif 'end_period' in request.form:
            period_id = int(request.form['period_id'])
            end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            period = Period.query.get(period_id)
            period.end_date = end_date
            db.session.commit()
            return redirect(url_for('auth.calendar'))

    periods = Period.query.all()
    current_date = datetime.now().date()
    predicted_next_period_start = calculate_predicted_next_period(periods)
    days_until_next_period = calculate_days_until_next_period(predicted_next_period_start)

    return render_template('calendar.html', periods=periods, current_date=current_date,
                           predicted_next_period_start=predicted_next_period_start,
                           days_until_next_period=days_until_next_period)

def calculate_days_until_next_period(predicted_next_period_start):
    if predicted_next_period_start:
        current_date = datetime.now().date()
        days_until_next_period = (predicted_next_period_start - current_date).days
        return max(0, days_until_next_period)
    return None

def calculate_predicted_next_period(periods):
    if len(periods) >= 2:
        total_days = sum((periods[i + 1].start_date - periods[i].start_date).days for i in range(len(periods) - 1))
        average_cycle_length = total_days / (len(periods) - 1)
        predicted_next_period_start = periods[-1].start_date + timedelta(days=round(average_cycle_length))
    else:
        predicted_next_period_start = datetime.now().date() + timedelta(days=27)

    return predicted_next_period_start

#@auth.route('/delete_period', methods=['POST'])
#def delete_period():
#    if request.method == 'POST':
 #       period_id = int(request.form['period_id'])
  #      period = Period.query.get(period_id)
        
   #     if period:
    #        db.session.delete(period)
     #       db.session.commit()

    #return redirect(url_for('auth.calendar'))

@auth.route('/add_symptom', methods=['POST'])
def add_symptom():
    if request.method == 'POST':
        period_id = int(request.form['period_id'])
        period = Period.query.get(period_id)

        if period:
            symptom_text = request.form['auth.symptom']
            symptom = Symptoms(symptom=symptom_text, period_id=period.id)
            db.session.add(symptom)
            db.session.commit()

    return redirect(url_for('auth.calendar'))