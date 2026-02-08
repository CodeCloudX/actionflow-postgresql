import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # =========================
    # Basic App Config
    # =========================
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # =========================
    # Database Configuration (PostgreSQL)
    # =========================
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # Session Config
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

    # =========================
    # Upload Configuration
    # =========================
    BASE_UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
    COMPLAINT_UPLOAD_SUBFOLDER = 'complaint'
    PROOF_UPLOAD_SUBFOLDER = 'proof'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max upload size
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}

    # =========================
    # Email Configuration (Flask-Mail)
    # =========================
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')

    # =========================
    # App Complaint Settings
    # =========================
    AUTO_CLOSE_RESOLVED_COMPLAINTS_AFTER = timedelta(days=3)
