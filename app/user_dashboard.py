from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from model import db, Complaint, User, Organization, Admin, Resolver
from datetime import datetime, timezone
from config import Config
from services.decorators import user_required
from services.email_service import send_auto_assign_notification
from services.common_utils import generate_complaint_id, save_uploaded_file, format_datetime
from sqlalchemy import func

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@user_required
def dashboard():
    user_id = session.get('user_id')

    user = User.query.get(user_id)
    organization = user.organization

    total_complaints = Complaint.query.filter_by(user_id=user_id).count()
    pending_complaints = Complaint.query.filter_by(user_id=user_id, status='pending').count()
    inprogress_complaints = Complaint.query.filter_by(user_id=user_id, status='in_progress').count()
    resolved_complaints = Complaint.query.filter_by(user_id=user_id, status='resolved').count()
    closed_complaints = Complaint.query.filter_by(user_id=user_id, status='closed').count()

    recent_complaints = Complaint.query.filter_by(user_id=user_id).order_by(func.coalesce(Complaint.updated_at, Complaint.created_at).desc()).limit(4).all()

    return render_template('user/dashboard.html',
                           organization=organization,
                           total_complaints=total_complaints,
                           pending_complaints=pending_complaints,
                           inprogress_complaints=inprogress_complaints,
                           resolved_complaints=resolved_complaints,
                           closed_complaints=closed_complaints,
                           recent_complaints=recent_complaints)

@user_bp.route('/complaints/new', methods=['GET', 'POST'])
@user_required
def file_complaint():
    org_id = session.get('org_id')
    organization = Organization.query.get_or_404(org_id)

    if request.method == 'POST':
        user_id = session.get('user_id')
        category = request.form.get('category')
        description = request.form.get('description')
        priority = request.form.get('priority', 'medium')
        other_category_text = request.form.get('other_category')
        complaint_image_file = request.files.get('complaint_image')

        if category == 'other' and other_category_text:
            category = other_category_text

        priority = priority.strip().lower()

        image_filename, message = save_uploaded_file(complaint_image_file, organization.org_unique_id, Config.COMPLAINT_UPLOAD_SUBFOLDER)
        if not image_filename:
            flash(message, 'danger')
            return redirect(url_for('user.file_complaint'))

        complaint_id = generate_complaint_id(organization.org_unique_id)

        new_complaint = Complaint(
            user_id=user_id,
            org_id=org_id,
            category=category,
            description=description,
            priority=priority,
            complaint_image=image_filename,
            complaint_id=complaint_id,
            status='pending',
            created_at=datetime.now(timezone.utc)
        )

        if new_complaint.priority == 'high':
            resolvers = Resolver.query.filter_by(org_id=org_id, category=category, status='active').all()

            if resolvers:
                q = db.session.query(Complaint.resolver_id, func.count(Complaint.id)).filter(
                    Complaint.resolver_id.in_([r.id for r in resolvers]),
                    Complaint.status.in_(['pending', 'in_progress'])
                ).group_by(Complaint.resolver_id).all()

                complaint_counts = {resolver_id: count for resolver_id, count in q}

                min_complaints = float('inf')
                best_resolver = None
                for resolver in resolvers:
                    count = complaint_counts.get(resolver.id, 0)
                    if count < min_complaints:
                        min_complaints = count
                        best_resolver = resolver

                if best_resolver:
                    new_complaint.resolver_id = best_resolver.id
                    new_complaint.status = 'in_progress'
                    primary_admin = Admin.query.filter_by(org_id=org_id).order_by(Admin.created_at.asc()).first()
                    if primary_admin:
                        send_auto_assign_notification(primary_admin.email, new_complaint.complaint_id, best_resolver.name, new_complaint.category)

        db.session.add(new_complaint)
        db.session.commit()

        flash(f'Your complaint has been filed successfully. Your Complaint ID is {complaint_id}', 'success')
        return redirect(url_for('user.my_complaints'))

    return render_template('user/file_complaint.html', organization=organization)

@user_bp.route('/complaints')
@user_required
def my_complaints():
    user_id = session.get('user_id')
    organization = Organization.query.get_or_404(session.get('org_id'))

    status_filter = request.args.get('status')

    query = Complaint.query.filter_by(user_id=user_id)

    if status_filter:
        query = query.filter(Complaint.status == status_filter)

    complaints = query.order_by(Complaint.created_at.desc()).all()

    return render_template(
        'user/my_complaints.html',
        complaints=complaints,
        organization=organization
    )

@user_bp.route('/complaint/<int:complaint_id>/details')
@user_required
def complaint_details(complaint_id):
    """Get complaint details for view modal."""
    user_id = session.get('user_id')
    complaint = Complaint.query.get_or_404(complaint_id)

    if complaint.user_id != user_id:
        return jsonify({'success': False, 'message': 'Not authorized'}), 403

    complaint_image_url = None
    if complaint.complaint_image:
        complaint_image_url = f"/static/uploads/{complaint.complaint_image.replace('\\', '/')}"

    proof_image_url = None
    if complaint.proof_image:
        proof_image_url = f"/static/uploads/{complaint.proof_image.replace('\\', '/')}"

    return jsonify({
        'success': True,
        'complaint': {
            'id': complaint.id,
            'complaint_id': complaint.complaint_id,
            'category': complaint.category,
            'description': complaint.description,
            'priority': complaint.priority,
            'status': complaint.status,
            'resolver_name': complaint.resolver.name if complaint.resolver else None,
            'created_date': format_datetime(complaint.created_at),
            'updated_date': format_datetime(complaint.updated_at),
            'complaint_image': complaint_image_url,
            'proof_image': proof_image_url,
            'resolution_note': complaint.resolution_note,
            'rating': complaint.rating,
            'feedback': complaint.feedback
        }
    })

@user_bp.route('/complaint/<int:complaint_id>/feedback', methods=['POST'])
@user_required
def submit_feedback(complaint_id):
    """Submit feedback for a resolved complaint."""
    user_id = session.get('user_id')
    complaint = Complaint.query.get_or_404(complaint_id)

    if complaint.user_id != user_id:
        return jsonify({'success': False, 'message': 'Not authorized'}), 403

    if complaint.status != 'resolved':
        return jsonify({'success': False, 'message': 'Feedback can only be provided for resolved complaints'}), 400

    if complaint.rating:
        return jsonify({'success': False, 'message': 'Feedback already provided for this complaint'}), 400

    try:
        data = request.get_json()
        rating = data.get('rating')
        comments = data.get('comments')

        if rating is None:
            return jsonify({'success': False, 'message': 'Rating is required'}), 400

        if isinstance(rating, str):
            if not rating.isdigit():
                return jsonify({'success': False, 'message': 'Valid rating is required'}), 400
            rating = int(rating)
        elif isinstance(rating, int):
            pass
        else:
            return jsonify({'success': False, 'message': 'Valid rating is required'}), 400

        if rating < 1 or rating > 5:
            return jsonify({'success': False, 'message': 'Rating must be between 1 and 5'}), 400

        complaint.rating = rating
        complaint.feedback = comments
        complaint.status = 'closed'
        complaint.updated_at = datetime.now(timezone.utc)

        if complaint.resolver:
            old_complaints = Complaint.query.filter(
                Complaint.resolver_id == complaint.resolver_id,
                Complaint.id != complaint.id,
                Complaint.rating.isnot(None)
            ).all()

            old_ratings = [c.rating for c in old_complaints]
            all_ratings = old_ratings + [rating]

            if all_ratings:
                complaint.resolver.rating = sum(all_ratings) / len(all_ratings)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Feedback submitted successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@user_bp.route('/organization-info')
@user_required
def organization_info():
    org_id = session.get('org_id')
    organization = Organization.query.get_or_404(org_id)

    return render_template('common/org_info.html',
                           organization=organization)

@user_bp.route('/profile')
@user_required
def profile():
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    organization = Organization.query.get_or_404(user.org_id)
    return render_template('user/profile.html', user=user, organization=organization)
