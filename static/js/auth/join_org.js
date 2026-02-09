document.addEventListener('DOMContentLoaded', function() {
        const joinForm = document.getElementById('joinForm');
        const joinBtn = document.getElementById('joinBtn');

        function clearAllErrors() {
            document.querySelectorAll('.field-error').forEach(error => {
                error.classList.remove('show');
            });
            document.querySelectorAll('input').forEach(field => {
                field.classList.remove('error-field');
            });
        }

        joinBtn.addEventListener('click', function() {
            clearAllErrors();

            if (validateForm()) {
                joinBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Joining...';
                joinBtn.disabled = true;
                joinForm.submit();
            }
        });

        function validateForm() {
            let isValid = true;

            const fullName = document.getElementById('fullName');
            const email = document.getElementById('email');
            const password = document.getElementById('password');
            const confirmPassword = document.getElementById('confirmPassword');
            const orgId = document.getElementById('orgId');

            if (!fullName.value.trim()) {
                document.getElementById('fullNameError').classList.add('show');
                fullName.classList.add('error-field');
                isValid = false;
            }

            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!email.value.trim() || !emailRegex.test(email.value)) {
                document.getElementById('emailError').textContent = 'Please enter a valid email.';
                document.getElementById('emailError').classList.add('show');
                email.classList.add('error-field');
                isValid = false;
            }

            if (password.value.length < 8) {
                document.getElementById('passwordError').textContent = 'Password must be at least 8 characters long.';
                document.getElementById('passwordError').classList.add('show');
                password.classList.add('error-field');
                isValid = false;
            }

            if (password.value !== confirmPassword.value) {
                document.getElementById('confirmPasswordError').textContent = 'Passwords do not match.';
                document.getElementById('confirmPasswordError').classList.add('show');
                confirmPassword.classList.add('error-field');
                isValid = false;
            }

            if (!orgId.value.trim()) {
                document.getElementById('orgIdError').classList.add('show');
                orgId.classList.add('error-field');
                isValid = false;
            }

            return isValid;
        }

        document.querySelectorAll('input').forEach(input => {
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    joinBtn.click();
                }
            });
        });
    });