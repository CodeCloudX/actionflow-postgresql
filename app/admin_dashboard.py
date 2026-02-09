from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, timezone
from model import db, User, Organization, Complaint, Admin, Resolver
from services.decorators import admin_required
from config import Config
from services.email_service import send_complaint_resolved_email
from services.common_utils import save_uploaded_file, format_datetime

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    org_id = session.get('org_id')
    organization = Organization.query.get_or_404(org_id)

    recent_users = User.query.filter_by(org_id=org_id).order_by(User.created_at.desc()).limit(4).all()
    recent_complaints = Complaint.query.filter_by(org_id=org_id).order_by(Complaint.created_at.desc()).limit(5).all()

    total_complaints = Complaint.query.filter_by(org_id=org_id).count()
    pending_complaints = Complaint.query.filter_by(org_id=org_id, status='pending').count()
    inprogress_complaints = Complaint.query.filter_by(org_id=org_id, status='in_progress').count()
    high_priority_complaints = Complaint.query.filter(
        Complaint.org_id == org_id,
        Complaint.priority == 'high',
        Complaint.status.in_(['pending', 'in_progress'])
    ).count()
    resolved_complaints = Complaint.query.filter(Complaint.org_id == org_id, Complaint.status.in_(['resolved', 'closed'])).count()

    return render_template('admin/dashboard.html',
                           organization=organization,
                           recent_users=recent_users,
                           recent_complaints=recent_complaints,
                           total_complaints=total_complaints,
                           pending_complaints=pending_complaints,
                           inprogress_complaints=inprogress_complaints,
                           high_priority_complaints=high_priority_complaints,
                           resolved_complaints=resolved_complaints)

@admin_bp.route('/complaints')
@admin_required
def complaints():
    org_id = session.get('org_id')
    organization = Organization.query.get_or_404(org_id)

    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    category_filter = request.args.get('category', '')

    query = Complaint.query.filter_by(org_id=org_id)

    if status_filter:
        status = status_filter.strip().lower()
        if status == 'resolved':
            query = query.filter(Complaint.status.in_(['resolved', 'closed']))
        else:
            query = query.filter(Complaint.status == status)

    if priority_filter:
        priority_filter = priority_filter.strip().lower()
        query = query.filter(Complaint.priority == priority_filter)

    if category_filter:
        query = query.filter_by(category=category_filter)

    categories = db.session.query(Complaint.category) \
        .filter_by(org_id=org_id) \
        .distinct() \
        .order_by(Complaint.category) \
        .all()
    categories = [c[0] for c in categories]

    complaints_list = query.order_by(Complaint.created_at.desc()).all()

    return render_template('admin/complaints.html',
                           complaints=complaints_list,
                           organization=organization,
                           status_filter=status_filter,
                           priority_filter=priority_filter,
                           category_filter=category_filter,
                           categories=categories)

@admin_bp.route('/complaint/<int:complaint_id>/details')
@admin_required
def complaint_details(complaint_id):
    """Get complaint details for view modal."""
    complaint = Complaint.query.get_or_404(complaint_id)

    if complaint.org_id != session.get('org_id'):
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
            'complaint_id': complaint.complaint_id,
            'category': complaint.category,
            'description': complaint.description,
            'priority': complaint.priority,
            'status': complaint.status,
            'user_name': complaint.user.full_name if complaint.user else None,
            'user_email': complaint.user.email if complaint.user else None,
            'resolver_name': complaint.resolver.name if complaint.resolver else None,
            'created_date': format_datetime(complaint.created_at),
            'updated_date': format_datetime(complaint.updated_at),
            'complaint_image': complaint_image_url,
            'proof_image': proof_image_url,
            'resolution_note': complaint.resolution_note
        }
    })

@admin_bp.route('/complaint/<int:complaint_id>/info')
@admin_required
def complaint_info(complaint_id):
    """Get basic complaint info for assign modal."""
    complaint = Complaint.query.get_or_404(complaint_id)

    if complaint.org_id != session.get('org_id'):
        return jsonify({'success': False, 'message': 'Not authorized'}), 403

    return jsonify({
        'success': True,
        'complaint': {
            'complaint_id': complaint.complaint_id,
            'category': complaint.category,
            'priority': complaint.priority,
            'status': complaint.status,
            'user_name': complaint.user.full_name if complaint.user else None
        }
    })

@admin_bp.route('/resolvers/list')
@admin_required
def resolvers_list():
    """Get list of resolvers for assign dropdown."""
    org_id = session.get('org_id')
    resolvers = Resolver.query.filter_by(org_id=org_id, status='active').all()

    return jsonify({
        'success': True,
        'resolvers': [{
            'id': resolver.id,
            'name': resolver.name,
            'email': resolver.email,
            'category': resolver.category
        } for resolver in resolvers]
    })

@admin_bp.route('/complaint/<int:complaint_id>/assign', methods=['POST'])
@admin_required
def assign_complaint(complaint_id):
    """Assign complaint to a resolver."""
    complaint = Complaint.query.get_or_404(complaint_id)

    if complaint.org_id != session.get('org_id'):
        return jsonify({'success': False, 'message': 'Not authorized'}), 403

    try:
        data = request.get_json()
        resolver_id = data.get('resolver_id')

        if not resolver_id:
            return jsonify({'success': False, 'message': 'Resolver ID is required'}), 400

        resolver = Resolver.query.get_or_404(resolver_id)
        if resolver.org_id != session.get('org_id'):
            return jsonify({'success': False, 'message': 'Resolver not found in your organization'}), 400

        complaint.resolver_id = resolver_id
        complaint.status = 'in_progress'
        complaint.updated_at = datetime.now(timezone.utc)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Complaint assigned to {resolver.name}'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/complaint/<int:complaint_id>/resolve', methods=['GET', 'POST'])
@admin_required
def resolve_complaint(complaint_id):
    """Resolve a complaint."""
    complaint = Complaint.query.get_or_404(complaint_id)
    org_id = session.get('org_id')
    organization = Organization.query.get_or_404(org_id)

    if complaint.org_id != org_id:
        flash('You are not authorized to resolve this complaint.', 'danger')
        return redirect(url_for('admin.complaints'))

    if complaint.status != 'in_progress':
        flash(f'Complaint {complaint.complaint_id} is not in a state that can be resolved.', 'warning')
        return redirect(url_for('admin.complaints'))

    if request.method == 'POST':
        resolution_note = request.form.get('resolution_note')
        proof_image_file = request.files.get('proof_image')

        if not resolution_note:
            flash('Resolution notes are required.', 'danger')
            return redirect(url_for('admin.resolve_complaint', complaint_id=complaint_id))

        image_filename, message = save_uploaded_file(proof_image_file, organization.org_unique_id, Config.PROOF_UPLOAD_SUBFOLDER)
        if not image_filename:
            flash(message, 'danger')
            return redirect(url_for('admin.resolve_complaint', complaint_id=complaint_id))

        try:
            complaint.status = 'resolved'
            complaint.resolution_note = resolution_note
            complaint.updated_at = datetime.now(timezone.utc)

            if image_filename:
                complaint.proof_image = image_filename

            send_complaint_resolved_email(complaint.user.email, complaint.complaint_id, session.get('full_name'))

            db.session.commit()

            flash(f'Complaint {complaint.complaint_id} has been marked as resolved.', 'success')
            return redirect(url_for('admin.complaints'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('admin.resolve_complaint', complaint_id=complaint_id))

    if complaint.complaint_image:
        complaint.complaint_image = complaint.complaint_image.replace('\\', '/')

    return render_template('admin/resolve_complaint.html',
                           complaint=complaint,
                           organization=organization)

@admin_bp.route('/resolvers')
@admin_required
def manage_resolvers():
    """Render the resolvers management page."""
    org_id = session.get('org_id')
    organization = Organization.query.get_or_404(org_id)
    resolvers = Resolver.query.filter_by(org_id=org_id).order_by(Resolver.name).all()
    return render_template('admin/resolvers.html', resolvers=resolvers, organization=organization)

@admin_bp.route('/resolver/add', methods=['POST'])
@admin_required
def add_resolver():
    """Add a new resolver via modal form."""
    try:
        org_id = session.get('org_id')

        name = request.form.get('name')
        email = request.form.get('email')
        category = request.form.get('category')

        if not name or not email or not category:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400

        email = email.lower().strip()

        existing_resolver = Resolver.query.filter_by(
            org_id=org_id,
            email=email
        ).first()

        if existing_resolver:
            return jsonify({'success': False, 'message': 'A resolver with this email already exists'}), 400

        existing_user = User.query.filter_by(
            org_id=org_id,
            email=email
        ).first()

        if existing_user:
            return jsonify({
                'success': False,
                'message': 'This email is already in use.'
            }), 400

        existing_admin = Admin.query.filter_by(
            org_id=org_id,
            email=email
        ).first()

        if existing_admin:
            return jsonify({
                'success': False,
                'message': 'This email is already in use.'
            }), 400

        new_resolver = Resolver(
            org_id=org_id,
            name=name,
            email=email,
            category=category,
            status='active'
        )

        db.session.add(new_resolver)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Resolver "{name}" has been added successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/resolver/edit/<int:resolver_id>', methods=['POST'])
@admin_required
def edit_resolver(resolver_id):
    """Edit resolver details via modal form."""
    try:
        resolver = Resolver.query.get_or_404(resolver_id)
        org_id = session.get('org_id')

        if resolver.org_id != org_id:
            return jsonify({'success': False, 'message': 'Not authorized'}), 403

        name = request.form.get('name')
        email = request.form.get('email')
        category = request.form.get('category')

        if not name or not email or not category:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400

        email = email.lower().strip()

        if email != resolver.email.lower():
            existing_resolver = Resolver.query.filter(
                Resolver.org_id == org_id,
                Resolver.email == email,
                Resolver.id != resolver_id
            ).first()

            if existing_resolver:
                return jsonify({
                    'success': False,
                    'message': 'Another resolver with this email already exists'
                }), 400

            existing_user = User.query.filter_by(
                org_id=org_id,
                email=email
            ).first()

            if existing_user:
                return jsonify({
                    'success': False,
                    'message': 'This email is already in use.'
                }), 400

            existing_admin = Admin.query.filter_by(
                org_id=org_id,
                email=email
            ).first()

            if existing_admin:
                return jsonify({
                    'success': False,
                    'message': 'This email is already in use.'
                }), 400

        resolver.name = name
        resolver.email = email
        resolver.category = category

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Resolver "{name}" has been updated successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/resolver/activate/<int:resolver_id>', methods=['POST'])
@admin_required
def activate_resolver(resolver_id):
    """Activate a resolver."""
    resolver = Resolver.query.get_or_404(resolver_id)

    if resolver.org_id != session.get('org_id'):
        flash('You are not authorized to modify this resolver.', 'danger')
        return redirect(url_for('admin.manage_resolvers'))

    resolver.status = 'active'
    db.session.commit()
    flash(f'Resolver "{resolver.name}" has been activated.', 'success')
    return redirect(url_for('admin.manage_resolvers'))

@admin_bp.route('/resolver/deactivate/<int:resolver_id>', methods=['POST'])
@admin_required
def deactivate_resolver(resolver_id):
    """Deactivate a resolver."""
    resolver = Resolver.query.get_or_404(resolver_id)

    if resolver.org_id != session.get('org_id'):
        flash('You are not authorized to modify this resolver.', 'danger')
        return redirect(url_for('admin.manage_resolvers'))

    resolver.status = 'inactive'
    db.session.commit()
    flash(f'Resolver "{resolver.name}" has been deactivated.', 'success')
    return redirect(url_for('admin.manage_resolvers'))

@admin_bp.route('/users')
@admin_required
def list_users():
    """List all users in the organization."""
    org_id = session.get('org_id')
    organization = Organization.query.get_or_404(org_id)
    users = User.query.filter_by(org_id=org_id).order_by(User.created_at.desc()).all()

    return render_template('admin/users.html',
                           users=users,
                           organization=organization)

@admin_bp.route('/user/status/<int:user_id>', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """Toggle user status between active and inactive."""
    user = User.query.get_or_404(user_id)

    if user.org_id != session.get('org_id'):
        flash('You are not authorized to modify this user.', 'danger')
        return redirect(url_for('admin.list_users'))

    if user.status == 'active':
        user.status = 'inactive'
        message = f"User '{user.full_name}' has been deactivated."
    else:
        user.status = 'active'
        message = f"User '{user.full_name}' has been activated."

    db.session.commit()
    flash(message, 'success')
    return redirect(url_for('admin.list_users'))

@admin_bp.route('/organization-info')
@admin_required
def organization_info():
    org_id = session.get('org_id')
    organization = Organization.query.get_or_404(org_id)

    user_count = User.query.filter_by(org_id=org_id).count()
    resolver_count = Resolver.query.filter_by(org_id=org_id).count()
    complaint_count = Complaint.query.filter_by(org_id=org_id).count()
    primary_admin = Admin.query.filter_by(org_id=org_id).order_by(Admin.created_at.asc()).first()

    return render_template('common/org_info.html',
                           organization=organization,
                           user_count=user_count,
                           resolver_count=resolver_count,
                           complaint_count=complaint_count,
                           primary_admin=primary_admin)
