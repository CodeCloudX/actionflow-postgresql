document.addEventListener('DOMContentLoaded', function() {
    // Category change handler
    const categorySelect = document.getElementById('category');
    const otherCategoryInput = document.getElementById('otherCategoryInput');
    const otherCategoryField = document.getElementById('otherCategory');

    if (categorySelect) {
        categorySelect.addEventListener('change', function() {
            if (this.value === 'other') {
                otherCategoryInput.style.display = 'block';
                otherCategoryField.required = true;
            } else {
                otherCategoryInput.style.display = 'none';
                otherCategoryField.required = false;
            }
        });
    }
});
