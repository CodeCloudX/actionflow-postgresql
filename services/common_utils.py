import os
import re
import uuid
import secrets
from functools import wraps
from flask import session, redirect, url_for
from werkzeug.utils import secure_filename
from config import Config
from datetime import datetime, timedelta
from email_validator import validate_email, EmailNotValidError


def redirect_if_logged_in(f):
    """
    Decorator to redirect logged-in users to their dashboard.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            if session.get('role') == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif session.get('role') == 'user':
                return redirect(url_for('user.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def is_password_valid(password):
    """
    Validates a password based on the following rules:
    - At least 8 characters long
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special Character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, "Password is valid."


def is_email_valid(email):
    """
    Validates an email address using the email-validator library.
    Returns True if valid, False otherwise.
    """
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False


def set_password_reset_token(user):
    """
    Generates and sets a password reset token and its expiration for a user.
    Returns the token.
    """
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expiration = datetime.utcnow() + timedelta(hours=1)
    return token


def clear_password_reset_token(user):
    """
    Clears the password reset token and expiration from a user object.
    """
    user.reset_token = None
    user.reset_token_expiration = None


def generate_organization_id():
    """
    Generates a unique organization ID.
    Example: 'ORG-E5F6G7H8'
    """
    base_id = str(uuid.uuid4().hex)[:8].upper()
    return f'ORG-{base_id}'


def generate_complaint_id(org_unique_id):
    """
    Generates a unique, formatted complaint ID using the organization's unique ID.
    Example: 'CMP-E5F6-A1B2'
    """
    complaint_base_id = str(uuid.uuid4().hex)[:4].upper()
    org_base_id = org_unique_id.split('-')[-1][:4]
    return f'CMP-{org_base_id}-{complaint_base_id}'


def save_uploaded_file(file, org_id, subfolder):
    """
    Saves an uploaded file to the correct directory with a unique name and returns the database path.
    - file: The file object from request.files.
    - org_id: The organization ID to create a nested folder.
    - subfolder: The specific subfolder (e.g., 'complaints' or 'proof').
    """
    if not file or file.filename == '':
        return None, "File is missing."

    original_filename = secure_filename(file.filename)
    file_ext = os.path.splitext(original_filename)[1].lower().lstrip('.')

    if file_ext not in Config.ALLOWED_IMAGE_EXTENSIONS:
        return None, "File type is not allowed."

    # Generate a unique prefix using a timestamp and a random string
    unique_prefix = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}"
    filename = f"{unique_prefix}_{original_filename}"

    # Physical path to save the file
    physical_upload_path = os.path.join(Config.BASE_UPLOAD_FOLDER, str(org_id), subfolder)
    os.makedirs(physical_upload_path, exist_ok=True)

    file_path = os.path.join(physical_upload_path, filename)
    file.save(file_path)

    if os.path.getsize(file_path) > Config.MAX_CONTENT_LENGTH:
        os.remove(file_path)  # Clean up the oversized file
        return None, "File size exceeds the allowed limit."

    # Relative path to store in the database
    db_path = f'{org_id}/{subfolder}/{filename}'
    return db_path, "File uploaded successfully."


def format_datetime(dt_object):
    """
    Consistently formats a datetime object for display.
    """
    if not dt_object:
        return None
    return dt_object.strftime('%B %d, %Y at %I:%M %p')
