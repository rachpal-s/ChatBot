from flask import Blueprint, render_template, request, flash, redirect, url_for, session
import requests
from urllib.parse import urlencode
import secrets
from flask import current_app
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   ##means from __init__.py import db
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['action'] == 'Login':
            email = request.form.get('email')
            password = request.form.get('password')

            user = User.query.filter_by(email=email).first()
            if user:
                if check_password_hash(user.password, password):
                    flash('Logged in successfully!', category='success')
                    login_user(user, remember=True)
                    return redirect(url_for('views.home'))
                else:
                    flash('Incorrect password, try again.', category='error')            
            else:
                flash('Email does not exist.', category='error')
        elif request.form['action'] == 'Login with Google':
            provider_data = current_app.config['OAUTH2_PROVIDERS'].get('google')
            if provider_data is None:
                flash('Missing Provider, try again.', category='error')
                return render_template("login.html")
            
            # generate a random string for the state parameter
            session['oauth2_state'] = "jassalsafe1642" #secrets.token_urlsafe(16)
            # create a query string with all the OAuth2 parameters
            qs = urlencode({
                'client_id': provider_data['client_id'],
                'redirect_uri': current_app.config['GOOGLE_REDIRECT_URI'],
                'response_type': 'code',
                'scope': ' '.join(provider_data['scopes']),
                'state': session['oauth2_state'],
             })

            # redirect the user to the OAuth2 provider authorization URL
            return redirect(provider_data['authorize_url'] + '?' + qs)    
           
    # Get requests
    # picking the provider again as this is the redirect request from provider with the details
    provider_data = current_app.config['OAUTH2_PROVIDERS'].get('google')
    if (len(request.args)) <= 1:
        return render_template("login.html", user=current_user)
    else:
        if not request.args:
            print('Redirecting, due to intended action')
            return render_template("login.html")
        print(request.args['code'])
        # exchange the authorization code for an access token
        response = requests.post(provider_data['token_url'], data={
            'client_id': provider_data['client_id'],
            'client_secret': provider_data['client_secret'],
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': current_app.config['GOOGLE_REDIRECT_URI'],
        }, headers={'Accept': 'application/json'})
        
        if response.status_code != 200:
            print('Exiting out, due to error')
            return redirect(provider_data['redirect_uri'])  
        
        oauth2_token = response.json().get('access_token')

        if not oauth2_token:
            print('Exiting out, due to error')
            return redirect(provider_data['redirect_uri'])  

        # use the access token to get the user's email address
        response = requests.get(provider_data['userinfo']['url'], headers={
            'Authorization': 'Bearer ' + oauth2_token,
            'Accept': 'application/json',
        })

        email = provider_data['userinfo']['email'](response.json())

        # find or create the user in the database
        user = db.session.scalar(db.select(User).where(User.email == email))
        if user is None:
            user = User(email=email, first_name=email.split('@')[0])
            db.session.add(user)
            db.session.commit()

        # log the user in
        login_user(user)
        return redirect(url_for('views.home'))


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))    #auth.login


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, first_name=first_name, password=generate_password_hash(
                password1, method='scrypt'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", user=current_user)


