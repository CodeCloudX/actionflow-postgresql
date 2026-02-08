// Modal elements
const modal = document.getElementById('complaintModal');
const feedbackModal = document.getElementById('feedbackModal');
const closeModalBtn = document.getElementById('closeModal');
const closeBtn = document.getElementById('closeBtn');
const complaintDetails = document.getElementById('complaintDetails');
const loadingOverlay = document.getElementById('loadingOverlay');
const feedbackBtn = document.getElementById('feedbackBtn');
const modalTitle = document.getElementById('modalTitle');

const closeFeedbackModalBtn = document.getElementById('closeFeedbackModal');
const cancelFeedbackBtn = document.getElementById('cancelFeedbackBtn');
const feedbackForm = document.getElementById('feedbackForm');
const ratingStars = document.getElementById('ratingStars');
const ratingValueInput = document.getElementById('ratingValue');
const submitFeedbackBtn = document.getElementById('submitFeedbackBtn');
const feedbackComplaintInfo = document.getElementById('feedbackComplaintInfo');

let currentComplaintId = null;
let currentComplaintData = null;
let selectedRating = 0;

// Open modal with complaint details
function openComplaintModal(complaintId) {
    currentComplaintId = complaintId;
    loadingOverlay.style.display = 'flex';
    complaintDetails.innerHTML = '';
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    // Fetch complaint details
    fetch(`/user/complaint/${complaintId}/details`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentComplaintData = data.complaint;
                renderComplaintDetails(data.complaint);

                // Show/hide feedback button based on status and if not already rated
                const isResolved = data.complaint.status.toLowerCase() === 'resolved';
                const hasRating = data.complaint.rating !== null && data.complaint.rating !== undefined;

                if (isResolved && !hasRating) {
                    feedbackBtn.style.display = 'inline-block';
                } else {
                    feedbackBtn.style.display = 'none';
                }
            } else {
                complaintDetails.innerHTML = `<div style="color: #e74c3c; text-align: center; padding: 20px;">${data.message || 'Failed to load details'}</div>`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            complaintDetails.innerHTML = '<div style="color: #e74c3c; text-align: center; padding: 20px;">Failed to load complaint details</div>';
        })
        .finally(() => {
            loadingOverlay.style.display = 'none';
        });
}

// Open feedback modal
function openFeedbackModal() {
    if (!currentComplaintData) return;

    // Set complaint info in feedback modal
    feedbackComplaintInfo.innerHTML = `
        <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
            <h4 style="margin: 0 0 10px 0; color: #2c3e50;">Complaint: ${currentComplaintData.complaint_id}</h4>
            <div style="font-size: 0.9rem; color: #7f8c8d;">
                <div>Category: ${currentComplaintData.category}</div>
                <div>Resolver: ${currentComplaintData.resolver_name || 'Not specified'}</div>
            </div>
        </div>
    `;

    // Reset rating
    selectedRating = 0;
    ratingValueInput.value = '';
    ratingStars.querySelectorAll('.rating-star').forEach(star => {
        star.classList.remove('active');
        star.textContent = '☆';
    });

    // Open modal
    feedbackModal.style.display = 'flex';
    modal.style.display = 'none';
}

// Render complaint details in modal
function renderComplaintDetails(complaint) {
    let html = `
        <div class="complaint-details-grid">
            <div class="detail-item">
                <span class="detail-label">Complaint ID</span>
                <span class="detail-value">${complaint.complaint_id}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Category</span>
                <span class="detail-value">${complaint.category}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Priority</span>
                <span class="detail-value">${complaint.priority}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Status</span>
                <span class="detail-value">${complaint.status}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Date Filed</span>
                <span class="detail-value">${complaint.created_date}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Last Updated</span>
                <span class="detail-value">${complaint.updated_date || 'N/A'}</span>
            </div>
            ${complaint.resolver_name ? `
            <div class="detail-item">
                <span class="detail-label">Assigned To</span>
                <span class="detail-value">${complaint.resolver_name}</span>
            </div>
            ` : ''}
            ${complaint.rating ? `
            <div class="detail-item">
                <span class="detail-label">Your Rating</span>
                <span class="detail-value">${complaint.rating}/5 ⭐</span>
            </div>
            ` : ''}
            <div class="description-box">
                <span class="detail-label">Description</span>
                <div class="detail-value">${complaint.description || 'No description provided'}</div>
            </div>
        </div>

        <div class="image-container">
    `;

    // Add complaint image if exists
    if (complaint.complaint_image) {
        html += `
            <div class="image-section">
                <h4>Complaint Image</h4>
                <img src="${complaint.complaint_image}" alt="Complaint Image" class="complaint-image" onerror="this.style.display='none';">
            </div>
        `;
    }

    // Add proof image if exists
    if (complaint.proof_image) {
        html += `
            <div class="image-section">
                <h4>Resolution Proof</h4>
                <img src="${complaint.proof_image}" alt="Proof Image" class="proof-image" onerror="this.style.display='none';">
            </div>
        `;
    }

    // Add resolution notes if exists
    if (complaint.resolution_note) {
        html += `
            <div class="description-box">
                <span class="detail-label">Resolution Note</span>
                <div class="detail-value">${complaint.resolution_note}</div>
            </div>
        `;
    }

    html += `</div>`;
    complaintDetails.innerHTML = html;
}

// Close modals
function closeModal() {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    currentComplaintId = null;
    currentComplaintData = null;
    feedbackBtn.style.display = 'none';
}

function closeFeedbackModal() {
    feedbackModal.style.display = 'none';
    document.body.style.overflow = 'auto';
}

// Set up event listeners
document.addEventListener('DOMContentLoaded', function() {
    // View details buttons
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const complaintId = this.getAttribute('data-complaint-id');
            openComplaintModal(complaintId);
        });
    });

    // Feedback buttons in table
    document.querySelectorAll('.feedback-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const complaintId = this.getAttribute('data-complaint-id');
            // Fetch complaint data and open feedback modal
            fetch(`/user/complaint/${complaintId}/details`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        currentComplaintId = complaintId;
                        currentComplaintData = data.complaint;
                        openFeedbackModal();
                    }
                });
        });
    });

    // Modal close buttons
    closeModalBtn.addEventListener('click', closeModal);
    closeBtn.addEventListener('click', closeModal);
    closeFeedbackModalBtn.addEventListener('click', closeFeedbackModal);
    cancelFeedbackBtn.addEventListener('click', closeFeedbackModal);

    // Close modal when clicking outside
    [modal, feedbackModal].forEach(modalEl => {
        modalEl.addEventListener('click', function(e) {
            if (e.target === modalEl) {
                if (modalEl.id === 'complaintModal') closeModal();
                if (modalEl.id === 'feedbackModal') closeFeedbackModal();
            }
        });
    });

    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (modal.style.display === 'flex') closeModal();
            if (feedbackModal.style.display === 'flex') closeFeedbackModal();
        }
    });

    // Feedback button in details modal
    feedbackBtn.addEventListener('click', openFeedbackModal);

    // Rating stars interaction
    ratingStars.querySelectorAll('.rating-star').forEach(star => {
        star.addEventListener('click', function() {
            selectedRating = parseInt(this.getAttribute('data-value'));
            ratingValueInput.value = selectedRating;

            // Update star display
            ratingStars.querySelectorAll('.rating-star').forEach((s, index) => {
                if (index < selectedRating) {
                    s.classList.add('active');
                    s.textContent = '★';
                } else {
                    s.classList.remove('active');
                    s.textContent = '☆';
                }
            });
        });

        // Hover effects
        star.addEventListener('mouseover', function() {
            const hoverValue = parseInt(this.getAttribute('data-value'));
            ratingStars.querySelectorAll('.rating-star').forEach((s, index) => {
                s.style.color = index < hoverValue ? '#f1c40f' : '#ddd';
            });
        });

        star.addEventListener('mouseout', function() {
            ratingStars.querySelectorAll('.rating-star').forEach((s, index) => {
                s.style.color = index < selectedRating ? '#f1c40f' : '#ddd';
            });
        });
    });

    // Feedback form submission
    feedbackForm.addEventListener('submit', function(e) {
        e.preventDefault();

        if (!selectedRating) {
            alert('Please select a rating');
            return;
        }

        const formData = new FormData(this);
        const submitBtn = submitFeedbackBtn;
        const originalText = submitBtn.textContent;

        // Show loading state
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;

        fetch(`/user/complaint/${currentComplaintId}/feedback`, {
            method: 'POST',
            body: JSON.stringify({
                rating: selectedRating,
                comments: formData.get('comments')
            }),
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Thank you for your feedback! The complaint has been closed.');
                closeFeedbackModal();
                closeModal();
                window.location.reload();
            } else {
                alert(data.message || 'Failed to submit feedback');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to submit feedback. Please try again.');
        })
        .finally(() => {
            submitBtn.classList.remove('loading');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        });
    });
});
