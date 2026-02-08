document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('resolverModal');
    const openModalBtn = document.getElementById('openModalBtn');
    const closeModalBtns = document.querySelectorAll('.close-modal, .btn-cancel');
    const form = document.getElementById('resolverForm');
    const modalTitle = document.getElementById('modalTitle');
    const resolverIdInput = document.getElementById('resolverId');

    if (!modal || !openModalBtn) return;

    const addResolverUrl = openModalBtn.dataset.addUrl;
    const editResolverUrl = openModalBtn.dataset.editUrl;

    const openModal = () => modal.classList.add('show');
    const closeModal = () => modal.classList.remove('show');

    // Open modal for adding new resolver
    openModalBtn.addEventListener('click', () => {
        modalTitle.textContent = 'Add New Resolver';
        form.reset();
        resolverIdInput.value = '';
        form.action = addResolverUrl;
        openModal();
    });

    // Open modal for editing resolver
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            modalTitle.textContent = 'Edit Resolver';

            resolverIdInput.value = btn.dataset.id;
            document.getElementById('name').value = btn.dataset.name;
            document.getElementById('email').value = btn.dataset.email;
            document.getElementById('category').value = btn.dataset.category;

            form.action = editResolverUrl.replace('0', btn.dataset.id);

            openModal();
        });
    });

    // Close modal
    closeModalBtns.forEach(btn => {
        btn.addEventListener('click', closeModal);
    });

    // Close modal when clicking outside
    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });

    // Handle form submission
    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        const formData = new FormData(form);
        const submitBtn = form.querySelector('.btn-submit');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Saving...';

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: new URLSearchParams(formData)
            });

            const result = await response.json();

            if (result.success) {
                window.location.reload();
            } else {
                alert(result.message || 'An error occurred');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while saving the resolver');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Save Resolver';
        }
    });
});
