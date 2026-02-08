   // Make sure all functions are defined in the global scope
    window.applyFilters = function(baseUrl) {
        const status = document.getElementById('statusFilter').value;
        const priority = document.getElementById('priorityFilter').value;
        const category = document.getElementById('categoryFilter').value;

        const params = new URLSearchParams();

        if (status) {
            params.set('status', status);
        }
        if (priority) {
            params.set('priority', priority);
        }
        if (category) {
            params.set('category', category);
        }

        window.location.href = `${baseUrl}?${params.toString()}`;
    };

    // Modal functions
    let currentComplaintId = null;
    let currentComplaintcomplaint_id = null;

    window.viewComplaint = function(complaintId) {
        currentComplaintId = complaintId;
        const modal = document.getElementById('viewModal');
        const loading = document.getElementById('viewLoading');
        const detailsDiv = document.getElementById('complaintDetails');

        loading.style.display = 'flex';
        detailsDiv.innerHTML = '';
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';

        fetch(`/admin/complaint/${complaintId}/details`)
            .then(r => {
                if (!r.ok) throw new Error('Network response was not ok');
                return r.json();
            })
            .then(data => {
                if (data.success) {
                    renderComplaintDetails(data.complaint);
                } else {
                    detailsDiv.innerHTML = `<div class="alert alert-danger">${data.message || 'Failed to load details'}</div>`;
                }
            })
            .catch(e => {
                console.error('Error:', e);
                detailsDiv.innerHTML = '<div class="alert alert-danger">Failed to load details. Please try again.</div>';
            })
            .finally(() => loading.style.display = 'none');
    };

    function renderComplaintDetails(complaint) {
        const detailsDiv = document.getElementById('complaintDetails');
        let html = `
            <div class="complaint-details">
                <div class="detail-item"><span class="detail-label">Complaint ID</span><span class="detail-value">${complaint.complaint_id}</span></div>
                <div class="detail-item"><span class="detail-label">Category</span><span class="detail-value">${complaint.category}</span></div>
                <div class="detail-item"><span class="detail-label">Complainant</span><span class="detail-value">${complaint.user_name || 'Unknown'}</span></div>
                <div class="detail-item"><span class="detail-label">Email</span><span class="detail-value">${complaint.user_email || 'N/A'}</span></div>
                <div class="detail-item"><span class="detail-label">Priority</span><span class="detail-value"><span class="priority-badge priority-${complaint.priority.toLowerCase()}">${complaint.priority}</span></span></div>
                <div class="detail-item"><span class="detail-label">Status</span><span class="detail-value"><span class="status-badge status-${complaint.status}">${complaint.status.replace('_', ' ').toUpperCase()}</span></span></div>
                <div class="detail-item"><span class="detail-label">Assigned To</span><span class="detail-value">${complaint.resolver_name || 'Not assigned'}</span></div>
                <div class="detail-item"><span class="detail-label">Created</span><span class="detail-value">${complaint.created_date}</span></div>
                <div class="detail-item"><span class="detail-label">Updated</span><span class="detail-value">${complaint.updated_date || 'N/A'}</span></div>
                <div class="description-box"><span class="detail-label">Description</span><div class="detail-value">${complaint.description || 'No description'}</div></div>
                `;

        if (complaint.complaint_image) {
            html += `<div class="detail-item" style="grid-column: span 2;">
                        <span class="detail-label">Complaint Image</span><br>
                        <img src="${complaint.complaint_image}" alt="Complaint Image" style="max-width: 100%; max-height: 300px; border-radius: 4px;">
                    </div>`;
        }

        if (complaint.proof_image) {
            html += `<div class="detail-item" style="grid-column: span 2;">
                        <span class="detail-label">Proof Image</span><br>
                        <img src="${complaint.proof_image}" alt="Proof Image" style="max-width: 100%; max-height: 300px; border-radius: 4px;">
                    </div>`;
        }

        if (complaint.resolution_note) {
            html += `<div class="description-box" style="grid-column: span 2;">
                        <span class="detail-label">Resolution Note</span>
                        <div class="detail-value">${complaint.resolution_note}</div>
                    </div>`;
        }

        html += `</div>`;
        detailsDiv.innerHTML = html;
    }

    window.closeViewModal = function() {
        document.getElementById('viewModal').style.display = 'none';
        document.body.style.overflow = 'auto';
        currentComplaintId = null;
    };

    window.assignComplaint = function(complaintId) {
        currentComplaintId = complaintId;
        const modal = document.getElementById('assignModal');
        const loading = document.getElementById('assignLoading');
        const infoDiv = document.getElementById('assignComplaintInfo');
        const resolverSelect = document.getElementById('resolverSelect');

        loading.style.display = 'flex';
        infoDiv.innerHTML = '';
        resolverSelect.innerHTML = '<option value="">-- Select a resolver --</option>';
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';

        Promise.all([
            fetch(`/admin/complaint/${complaintId}/info`).then(r => r.json()),
            fetch(`/admin/resolvers/list`).then(r => r.json())
        ])
        .then(([complaintData, resolversData]) => {
            if (complaintData.success) {
                currentComplaintcomplaint_id = complaintData.complaint.complaint_id;
                infoDiv.innerHTML = `
                    <div style="margin-bottom:20px; padding:15px; background:#f8f9fa; border-radius:6px;">
                        <h4 style="margin-bottom:10px; color:#2c3e50;">Complaint: ${complaintData.complaint.complaint_id}</h4>
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; font-size:0.9rem;">
                            <div><strong>Category:</strong> ${complaintData.complaint.category}</div>
                            <div><strong>Priority:</strong> <span class="priority-badge priority-${complaintData.complaint.priority.toLowerCase()}">${complaintData.complaint.priority}</span></div>
                            <div><strong>Status:</strong> <span class="status-badge status-${complaintData.complaint.status}">${complaintData.complaint.status.replace('_', ' ').toUpperCase()}</span></div>
                            <div><strong>Complainant:</strong> ${complaintData.complaint.user_name || 'Unknown'}</div>
                        </div>
                    </div>
                `;
            }

            if (resolversData.success && resolversData.resolvers) {
                resolversData.resolvers.forEach(r => {
                    const option = document.createElement('option');
                    option.value = r.id;
                    option.textContent = `${r.name} - ${r.category} (${r.email})`;
                    resolverSelect.appendChild(option);
                });
            }
        })
        .catch(e => console.error('Error:', e))
        .finally(() => loading.style.display = 'none');
    };

    window.closeAssignModal = function() {
        document.getElementById('assignModal').style.display = 'none';
        document.body.style.overflow = 'auto';
        currentComplaintId = null;
        currentComplaintcomplaint_id = null;
        document.getElementById('assignForm').reset();
    };

    // Initialize when page loads
    document.addEventListener('DOMContentLoaded', function() {
        // Set up filter event listeners
        const complaintsUrl = document.getElementById('complaintsContainer').dataset.url;
        document.getElementById('statusFilter').addEventListener('change', () => applyFilters(complaintsUrl));
        document.getElementById('priorityFilter').addEventListener('change', () => applyFilters(complaintsUrl));
        document.getElementById('categoryFilter').addEventListener('change', () => applyFilters(complaintsUrl));

        // Set up modal close buttons
        document.getElementById('closeViewModal').addEventListener('click', closeViewModal);
        document.getElementById('closeViewBtn').addEventListener('click', closeViewModal);
        document.getElementById('closeAssignModal').addEventListener('click', closeAssignModal);
        document.getElementById('cancelAssignBtn').addEventListener('click', closeAssignModal);

        // Set up action button event listeners
        document.querySelectorAll('.btn-view').forEach(button => {
            button.addEventListener('click', function() {
                const complaintId = this.getAttribute('data-complaint-id');
                viewComplaint(complaintId);
            });
        });

        document.querySelectorAll('.btn-assign').forEach(button => {
            button.addEventListener('click', function() {
                const complaintId = this.getAttribute('data-complaint-id');
                assignComplaint(complaintId);
            });
        });

        // Set up assign form submission
        document.getElementById('assignForm').addEventListener('submit', function(e) {
            e.preventDefault();
            if (!currentComplaintId) {
                alert('No complaint selected');
                return;
            }

            const resolverId = document.getElementById('resolverSelect').value;
            const notes = document.getElementById('assignNotes').value;

            if (!resolverId) {
                alert('Please select a resolver');
                return;
            }

            const loading = document.getElementById('assignLoading');
            loading.style.display = 'flex';

            fetch(`/admin/complaint/${currentComplaintId}/assign`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({resolver_id: resolverId, notes: notes})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    alert(`Complaint ${currentComplaintcomplaint_id} assigned successfully!`);
                    closeAssignModal();
                    window.location.reload();
                } else {
                    alert(data.message || 'Failed to assign complaint');
                }
            })
            .catch(e => {
                console.error('Error:', e);
                alert('Failed to assign complaint. Please try again.');
            })
            .finally(() => loading.style.display = 'none');
        });

        // Close modals when clicking outside
        document.querySelectorAll('.modal-overlay').forEach(modal => {
            modal.addEventListener('click', function(e) {
                if (e.target === this) {
                    if (this.id === 'viewModal') closeViewModal();
                    if (this.id === 'assignModal') closeAssignModal();
                }
            });
        });

        // Close modals with Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeViewModal();
                closeAssignModal();
            }
        });

        // Auto-hide alerts
        document.querySelectorAll('.alert').forEach(alert => {
            setTimeout(() => {
                if (alert.parentElement) {
                    alert.remove();
                }
            }, 5000);
        });
    });