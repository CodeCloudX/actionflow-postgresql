from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from model import db, Complaint

def init_scheduler(app):
    """Initializes and starts the background scheduler for auto-closing complaints."""

    def auto_close_job():
        """The actual job that runs on a schedule."""
        with app.app_context():
            auto_close_delta = app.config.get('AUTO_CLOSE_RESOLVED_COMPLAINTS_AFTER')
            if not auto_close_delta:
                app.logger.warning("Scheduler: AUTO_CLOSE_RESOLVED_COMPLAINTS_AFTER not set.")
                return

            cutoff_date = datetime.now(timezone.utc) - auto_close_delta
            complaints_to_close = Complaint.query.filter(
                Complaint.status == 'resolved',
                Complaint.updated_at <= cutoff_date
            ).all()

            if complaints_to_close:
                for complaint in complaints_to_close:
                    complaint.status = 'closed'
                    complaint.updated_at = datetime.now(timezone.utc)
                db.session.commit()
                app.logger.info(f"Scheduler: Auto-closed {len(complaints_to_close)} complaints.")
            else:
                app.logger.info("Scheduler: No complaints to auto-close.")

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(auto_close_job, 'interval', days=1)
    scheduler.start()
