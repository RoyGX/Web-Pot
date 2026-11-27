import csv
import io
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, LoginAttempt

main = Blueprint('main', __name__)


@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.inici'))
    return redirect(url_for('main.login'))


@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.inici'))

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
            db.session.add(LoginAttempt(username=username, mfa_token=mfa_token, success=True))
            db.session.commit()
            login_user(user)
            next_page = request.args.get('next')
            if not next_page and user.is_admin:
                return redirect(url_for('main.logins'))
            return redirect(next_page or url_for('main.inici'))
        elif user.check_password(password):
            user.mfa_token = mfa_token
            user.last_login = datetime.now(timezone.utc)
            db.session.add(LoginAttempt(username=username, mfa_token=mfa_token, success=True))
            db.session.commit()
            login_user(user)
            next_page = request.args.get('next')
            if not next_page and user.is_admin:
                return redirect(url_for('main.logins'))
            return redirect(next_page or url_for('main.inici'))
        else:
            db.session.add(LoginAttempt(username=username, mfa_token=mfa_token, success=False))
            db.session.commit()
            flash('Contrasenya incorrecta per a aquest usuari.', 'danger')

    return render_template('login.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.inici'))

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


@main.route('/inici')
@login_required
def inici():
    return render_template('welcome.html')


@main.route('/documents')
@login_required
def documents():
    return render_template('documents.html')


@main.route('/welcome')
@login_required
def welcome():
    return redirect(url_for('main.inici'))


@main.route('/logins')
@login_required
def logins():
    if not current_user.is_admin:
        flash('No tens permisos per accedir a aquesta pàgina.', 'danger')
        return redirect(url_for('main.inici'))
    users = User.query.order_by(User.created_at.desc()).all()
    attempts = LoginAttempt.query.order_by(LoginAttempt.timestamp.desc()).all()
    return render_template('logins.html', users=users, attempts=attempts)


@main.route('/logins/export/users.csv')
@login_required
def export_users_csv():
    if not current_user.is_admin:
        flash('No tens permisos per realitzar aquesta acció.', 'danger')
        return redirect(url_for('main.inici'))

    users = User.query.order_by(User.created_at.desc()).all()
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Usuari', 'Contrasenya', 'Token MFA', "Data d'ingrés"])
    for user in users:
        writer.writerow([
            user.username,
            '********',
            user.mfa_token or '',
            user.created_at.strftime('%d/%m/%Y %H:%M') if user.created_at else ''
        ])

    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=usuaris_registrats.csv'}
    )


@main.route('/logins/export/attempts.csv')
@login_required
def export_attempts_csv():
    if not current_user.is_admin:
        flash('No tens permisos per realitzar aquesta acció.', 'danger')
        return redirect(url_for('main.inici'))

    attempts = LoginAttempt.query.order_by(LoginAttempt.timestamp.desc()).all()
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Usuari', 'Estat', 'Token MFA', 'Timestamp'])
    for attempt in attempts:
        writer.writerow([
            attempt.username,
            'Correcte' if attempt.success else 'Incorrecte',
            attempt.mfa_token or '',
            attempt.timestamp.strftime('%d/%m/%Y %H:%M:%S') if attempt.timestamp else ''
        ])

    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=historial_accessos.csv'}
    )


@main.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('No tens permisos per realitzar aquesta acció.', 'danger')
        return redirect(url_for('main.inici'))

    user = db.session.get(User, user_id)
    if not user:
        flash('Usuari no trobat.', 'warning')
        return redirect(url_for('main.logins'))

    if user.id == current_user.id:
        flash('No pots esborrar el teu propi usuari mentre tens la sessió iniciada.', 'warning')
        return redirect(url_for('main.logins'))

    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'Usuari "{username}" esborrat correctament.', 'success')
    return redirect(url_for('main.logins'))


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has tancat la sessió correctament.', 'info')
    return redirect(url_for('main.login'))
