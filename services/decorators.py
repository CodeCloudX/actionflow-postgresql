from flask import flash, redirect, url_for, session
from functools import wraps
from model import User, Admin

def guest_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            if session.get('role') == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif session.get('role') == 'user':
                return redirect(url_for('user.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('auth.login'))

        admin = Admin.query.get(session['user_id'])
        if not admin:
            session.clear()
            flash('Your account could not be found. Please log in again.', 'danger')
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'user':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('auth.login'))

        user = User.query.get(session['user_id'])
        if not user or user.status != 'active':
            session.clear()
            flash(
                'Your account is inactive or has been deleted. Please contact your administrator.',
                'danger'
            )
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)
    return decorated_function