import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from threading import Thread
from flask import current_app
from config import Config

# -----------------------------
# Core background email task
# -----------------------------
def _send_email_task(app, msg):
    """Send email in background thread with Flask app context."""
    with app.app_context():
        try:
            # SMTP server setup
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.starttls()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.send_message(msg)
            app.logger.info(f"Background email sent successfully to {msg['To']}")
        except Exception as e:
            app.logger.error(f"Background email sending failed: {e}")

# -----------------------------
# Main send_email function
# -----------------------------
def send_email(to_email, subject, message):
    """
    Prepares plain-text email and sends it asynchronously in a background thread.
    """
    app = current_app._get_current_object()

    # Create email message
    msg = MIMEMultipart()
    msg["From"] = formataddr(("ActionFlow", Config.MAIL_USERNAME))  # Brand as sender
    msg["To"] = to_email
    msg["Subject"] = subject

    # Attach plain text
    msg.attach(MIMEText(message, "plain"))

    # Start background thread
    Thread(target=_send_email_task, args=(app, msg)).start()

# -----------------------------
# Helper email functions
# -----------------------------

def send_org_registration_email(admin_email, org_name, org_unique_id):
    subject = "Organization Registered Successfully"
    message = f"""
Hello,

Your organization "{org_name}" has been successfully registered.

Organization Unique ID: {org_unique_id}

Please keep this ID safe. Users can join your organization using this ID.

Regards,
ActionFlow Support Team
"""
    send_email(admin_email, subject, message)

def send_auto_assign_notification(admin_email, complaint_id, resolver_name, category):
    subject = f"High-Priority Complaint Auto-Assigned: {complaint_id}"
    message = f"""
Hello Admin,

A new HIGH-PRIORITY complaint in the '{category}' category has been automatically assigned.

- Complaint ID: {complaint_id}
- Assigned To: {resolver_name}

This assignment was made automatically based on the complaint category. Please review it at your convenience.

Regards,
ActionFlow Support Team
"""
    send_email(admin_email, subject, message)

def send_forgot_password_email(user_email, reset_link):
    subject = "Password Reset Request"
    message = f"""
Hello,

We received a request to reset your password.

Click the link below to reset your password:
{reset_link}

If you did not request this, please ignore this email.

Regards,
ActionFlow Support Team
"""
    send_email(user_email, subject, message)

def send_complaint_resolved_email(user_email, complaint_id, admin_name):
    subject = f"Update on Your Complaint: {complaint_id}"
    message = f"""
Hello,

Good news! Your complaint with ID {complaint_id} has been marked as resolved by {admin_name}.

Please log in to your dashboard to view the details and provide feedback if you wish.

If you are satisfied, you may confirm and close the complaint.
Providing feedback is optional and helps us improve our service.

If no action is taken within 3 days, the complaint will be automatically closed by the system.

Thank you for your patience and cooperation.

Regards,
ActionFlow Support Team
"""
    send_email(user_email, subject, message)