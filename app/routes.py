from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User

main = Blueprint('main', __name__)


@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.welcome'))
    return redirect(url_for('main.login'))


@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.welcome'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        mfa_token = request.form.get('mfa_token', '').strip()

        if not username or not password or not mfa_token:
            flash('Tots els camps són obligatoris.', 'danger')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if user is None:
            user = User(username=username, mfa_token=mfa_token)
            user.set_password(password)
            user.last_login = datetime.now(timezone.utc)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            next_page = request.args.get('next')
            if not next_page and user.username == 'Admin33':
                return redirect(url_for('main.logins'))
            return redirect(next_page or url_for('main.welcome'))
        elif user.check_password(password):
            user.mfa_token = mfa_token
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            login_user(user)
            next_page = request.args.get('next')
            if not next_page and user.username == 'Admin33':
                return redirect(url_for('main.logins'))
            return redirect(next_page or url_for('main.welcome'))
        else:
            flash('Contrasenya incorrecta per a aquest usuari.', 'danger')

    return render_template('login.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.welcome'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        errors = []

        if not username:
            errors.append('L\'usuari és obligatori.')
        if not password:
            errors.append('La contrasenya és obligatòria.')
        if len(password) < 6:
            errors.append('La contrasenya ha de tenir almenys 6 caràcters.')
        if password != password_confirm:
            errors.append('Les contrasenyes no coincideixen.')

        if User.query.filter_by(username=username).first():
            errors.append('Aquest nom d\'usuari ja existeix.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html', username=username)

        user = User(username=username, mfa_token='')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Usuari creat correctament! Ara pots iniciar sessió.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html')


@main.route('/welcome')
@login_required
def welcome():
    return render_template('welcome.html')


@main.route('/logins')
@login_required
def logins():
    if current_user.username != 'Admin33':
        flash('No tens permisos per accedir a aquesta pàgina.', 'danger')
        return redirect(url_for('main.welcome'))
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('logins.html', users=users)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has tancat la sessió correctament.', 'info')
    return redirect(url_for('main.login'))
