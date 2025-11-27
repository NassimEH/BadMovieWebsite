from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
from models import User
from extensions import db
from flask_login import login_user, login_required, logout_user

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login.

    If the request method is POST, it retrieves the username and password from the form.
    It checks if the user exists and, if confirmed, verifies the password.
    Upon successful login, it flashes a success message, logs in the user, and redirects to the home page.

    Returns:
        Flask response or rendered template: Redirects to the home page upon successful login
        or renders the login page.
    """

    if(request.method == 'POST'):
        _username = request.form.get("username")
        _password = request.form.get("password")

        user = User.query.filter_by(nom=_username).first()
        if user:
            if check_password_hash(user.password, _password):
                flash('Connecté', category='success')
                login_user(user, remember=True)
                return redirect(url_for('index'))
            else:
                flash('Mot de passe incorect', category='error')
        else:
            flash('Aucun compte avec ce nom existe', category='error')

    return render_template("auth/login.html")

@auth_bp.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    """Handles user registration (sign-up).

    If the request method is POST, it retrieves the username, email, and password from the form.
    It checks if the username already exists, validates the email, username, and password length.
    If all conditions are met, it creates a new user in the database,
    and redirects the user to the login page after successful registration.

    Returns:
        Flask response or rendered template: Redirects to the login page upon successful registration
        or renders the sign-up page with error messages.
    """

    if(request.method == 'POST'):
        _username = request.form.get("username")
        _email  = request.form.get("email")
        _password = request.form.get("password")

        user = User.query.filter_by(nom=_username).first()
        email = User.query.filter_by(mail=_email).first()
        if user:
            flash("Compte déjà existant", category='error')
        elif email : flash(f"email déjà attribuée au compte {email.nom}", category='error')
        elif(len(_email) < 4): flash('Email trop courte', category='error')
        elif(len(_username) < 4): flash('Nom trop court, au moins 4 caractères est nécessaire ', category='error')
        elif(len(_password) < 7): flash('Mot de passe trop court, au moins 7 caractères est nécessaire', category='error')
        
        else : 
            new_user = User(
                mail=_email, 
                nom=_username, 
                password=generate_password_hash(_password, method='pbkdf2:sha256')
            )

            db.session.add(new_user)
            db.session.commit()
            flash('Compte créé avec succès! Vous pouvez maintenant vous connecter.', category='success')
            return redirect(url_for('auth.login'))
    return render_template("auth/register.html")

@auth_bp.route('/logout')
@login_required
def logout():
    """Logs out the current user."""
    logout_user()
    flash('Déconnecté avec succès', category='info')
    return redirect(url_for('auth.login'))
