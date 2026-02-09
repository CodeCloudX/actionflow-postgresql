document.addEventListener('DOMContentLoaded', function() {
        const registrationForm = document.getElementById('registrationForm');
        const step1 = document.getElementById('step1');
        const step2 = document.getElementById('step2');
        const nextBtn = document.getElementById('nextBtn');
        const backBtn = document.getElementById('backBtn');
        const registerBtn = document.getElementById('registerBtn');

        function clearAllErrors() {
            document.querySelectorAll('.error-message').forEach(error => error.classList.remove('show'));
            document.querySelectorAll('input, select, textarea').forEach(field => field.classList.remove('error-field'));
        }

        nextBtn.addEventListener('click', function() {
            clearAllErrors();
            if (validateStep1()) {
                step1.classList.remove('active');
                step2.classList.add('active');
            }
        });

        backBtn.addEventListener('click', function() {
            clearAllErrors();
            step2.classList.remove('active');
            step1.classList.add('active');
        });

        registerBtn.addEventListener('click', function() {
            clearAllErrors();
            if (validateStep1() && validateStep2()) {
                registerBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Registering...';
                registerBtn.disabled = true;
                registrationForm.submit();
            } else if (!validateStep1()) {
                // If step 1 is invalid, go back to it
                step2.classList.remove('active');
                step1.classList.add('active');
            }
        });

        function validateStep(fields) {
            let isValid = true;
            for (const field of fields) {
                const element = document.getElementById(field.id);
                const errorElement = document.getElementById(field.id + 'Error');

                element.classList.remove('error-field');
                errorElement.classList.remove('show');

                if (!element.value.trim() || (element.tagName === 'SELECT' && element.value === '')) {
                    errorElement.textContent = field.message;
                    errorElement.classList.add('show');
                    element.classList.add('error-field');
                    isValid = false;
                } else if (field.id === 'contactEmail' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(element.value.trim())) {
                    errorElement.textContent = 'Please enter a valid email address.';
                    errorElement.classList.add('show');
                    element.classList.add('error-field');
                    isValid = false;
                } else if (field.id === 'adminEmail' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(element.value.trim())) {
                    errorElement.textContent = 'Please enter a valid email address.';
                    errorElement.classList.add('show');
                    element.classList.add('error-field');
                    isValid = false;
                } else if (field.id === 'phone' && !/^(\+91[\-\s]?)?([6-9]\d{9}|0\d{9,10})$/.test(element.value.trim())) {
                    errorElement.textContent = 'Please enter a valid contact number (mobile or landline)';
                    errorElement.classList.add('show');
                    element.classList.add('error-field');
                    isValid = false;
                }
            }
            return isValid;
        }

        function validateStep1() {
            return validateStep([
                { id: 'orgName', message: 'Organization Name is required' },
                { id: 'orgCategory', message: 'Organization Category is required' },
                { id: 'contactEmail', message: 'Contact Email is required' },
                { id: 'phone', message: 'Contact Number is required' },
                { id: 'address', message: 'Address is required' }
            ]);
        }

        function validateStep2() {
            const password = document.getElementById('password');
            const confirmPassword = document.getElementById('confirmPassword');
            const confirmPasswordError = document.getElementById('confirmPasswordError');

            let isValid = validateStep([
                { id: 'adminName', message: 'Administrator Name is required' },
                { id: 'adminEmail', message: 'Administrator Email is required' },
                { id: 'password', message: 'Password is required' },
                { id: 'confirmPassword', message: 'Please confirm your password' }
            ]);

            if (isValid && password.value !== confirmPassword.value) {
                confirmPassword.classList.add('error-field');
                confirmPasswordError.textContent = 'Passwords do not match';
                confirmPasswordError.classList.add('show');
                isValid = false;
            }
            return isValid;
        }
    });