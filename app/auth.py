from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from model import db, Admin, User, Organization
from services.decorators import login_required, guest_required
from services.email_service import send_org_registration_email, send_forgot_password_email
from services.common_utils import is_password_valid, is_email_valid, generate_organization_id, set_password_reset_token, clear_password_reset_token
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
@guest_required
def index():
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
@guest_required
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')

        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.check_password(password):
            session['user_id'] = admin.id
            session['role'] = 'admin'
            session['org_id'] = admin.org_id
            session['full_name'] = admin.full_name
            if remember:
                session.permanent = True
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin.dashboard'))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if user.status != 'active':
                flash('Your account is inactive. Please contact your organization\'s administrator.', 'danger')
                return redirect(url_for('auth.login'))

            session['user_id'] = user.id
            session['role'] = 'user'
            session['org_id'] = user.org_id
            session['full_name'] = user.full_name
            if remember:
                session.permanent = True
            flash('Login successful!', 'success')
            return redirect(url_for('user.dashboard'))

        flash('Invalid email or password.', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('auth/login.html')

@auth_bp.route('/register/admin', methods=['GET', 'POST'])
@guest_required
def admin_register():
    if request.method == 'POST':
        form_data = request.form
        org_name = form_data.get('org_name')
        org_category = form_data.get('org_category')
        org_website = form_data.get('org_website')
        org_email = form_data.get('org_email')
        org_phone = form_data.get('org_phone')
        org_address = form_data.get('org_address')
        full_name = form_data.get('full_name')
        email = form_data.get('email')
        password = form_data.get('password')

        if not is_email_valid(email) or not is_email_valid(org_email):
            flash('Invalid email address format.', 'danger')
            return render_template('auth/org_register.html', form_data=form_data)

        is_valid, message = is_password_valid(password)
        if not is_valid:
            flash(message, 'danger')
            return render_template('auth/org_register.html', form_data=form_data)

        if Admin.query.filter_by(email=email).first() or User.query.filter_by(email=email).first():
            flash('This email address is already in use. Please choose a different one.', 'danger')
            return render_template('auth/org_register.html', form_data=form_data)

        org_unique_id = generate_organization_id()
        organization = Organization(
            org_name=org_name,
            category=org_category,
            website=org_website,
            contact_email=org_email,
            phone=org_phone,
            address=org_address,
            org_unique_id=org_unique_id
        )
        db.session.add(organization)
        db.session.flush()
        admin = Admin(
            full_name=full_name,
            email=email,
            org_id=organization.id
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        send_org_registration_email(email, org_name, org_unique_id)
        flash(f'Organization registered successfully! Your Org ID is {org_unique_id}', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/org_register.html', form_data={})

@auth_bp.route('/register/user', methods=['GET', 'POST'])
@guest_required
def user_register():
    if request.method == 'POST':
        form_data = request.form
        full_name = form_data.get('full_name')
        email = form_data.get('email')
        password = form_data.get('password')
        org_unique_id = form_data.get('org_unique_id')

        if not is_email_valid(email):
            flash('Invalid email address format.', 'danger')
            return render_template('auth/join_org.html', form_data=form_data)

        organization = Organization.query.filter_by(org_unique_id=org_unique_id).first()
        if not organization:
            flash('Invalid Organization ID', 'danger')
            return render_template('auth/join_org.html', form_data=form_data)

        is_valid, message = is_password_valid(password)
        if not is_valid:
            flash(message, 'danger')
            return render_template('auth/join_org.html', form_data=form_data)

        if User.query.filter_by(email=email).first() or Admin.query.filter_by(email=email).first():
            flash('This email address is already in use. Please choose a different one.', 'danger')
            return render_template('auth/join_org.html', form_data=form_data)

        user = User(
            full_name=full_name,
            email=email,
            org_id=organization.id
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('You have registered successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/join_org.html', form_data={})

@auth_bp.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = Admin.query.filter_by(email=email).first() or User.query.filter_by(email=email).first()

        if user:
            token = set_password_reset_token(user)
            db.session.commit()

            reset_link = url_for('auth.reset_password', token=token, _external=True)
            send_forgot_password_email(email, reset_link)

        flash('If your email is registered, you will receive a password reset link shortly.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = Admin.query.filter_by(reset_token=token).first() or User.query.filter_by(reset_token=token).first()

    if not user or user.reset_token_expiration < datetime.utcnow():
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.reset_password', token=token))

        is_valid, message = is_password_valid(password)
        if not is_valid:
            flash(message, 'danger')
            return redirect(url_for('auth.reset_password', token=token))

        user.set_password(password)
        clear_password_reset_token(user)
        db.session.commit()

        flash('Your password has been successfully reset. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)
