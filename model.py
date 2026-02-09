from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# =========================
# Organization Model
# =========================
class Organization(db.Model):
    __tablename__ = 'organizations'

    id = db.Column(db.Integer, primary_key=True)
    org_unique_id = db.Column(db.String(20), unique=True, nullable=False)
    org_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    website = db.Column(db.String(150))
    contact_email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  # active / inactive
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    admins = db.relationship('Admin', backref='organization', lazy=True)
    users = db.relationship('User', backref='organization', lazy=True)
    complaints = db.relationship('Complaint', backref='organization', lazy=True)

    @property
    def website_url(self):
        if not self.website:
            return None
        if self.website.startswith('http'):
            return self.website
        return f'https://{self.website}'


# =========================
# Admin Model
# =========================
class Admin(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # Fields for password reset
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiration = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# =========================
# User Model
# =========================
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='active')  # active / blocked
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # Fields for password reset
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiration = db.Column(db.DateTime, nullable=True)

    complaints = db.relationship('Complaint', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# =========================
# Resolver Model (No Login)
# =========================
class Resolver(db.Model):
    __tablename__ = 'resolvers'

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    category = db.Column(db.String(50))  # Infrastructure, Security, etc
    status = db.Column(db.String(20), default='active')  # active / blocked
    rating = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    complaints = db.relationship('Complaint', backref='resolver', lazy=True)


# =========================
# Complaint Model
# =========================
class Complaint(db.Model):
    __tablename__ = 'complaints'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.String(30), unique=True, nullable=False)

    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resolver_id = db.Column(db.Integer, db.ForeignKey('resolvers.id'))

    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)

    priority = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(30), default='pending')

    complaint_image = db.Column(db.String(255))
    proof_image = db.Column(db.String(255))
    resolution_note = db.Column(db.Text, nullable=True)

    feedback = db.Column(db.Text)
    rating = db.Column(db.Integer)  # 1 to 5

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))
