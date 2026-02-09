document.addEventListener('DOMContentLoaded', function() {
        const loginForm = document.getElementById('loginForm');
        const loginBtn = document.getElementById('loginBtn');
        const emailInput = document.getElementById('email');
        const passwordInput = document.getElementById('password');

        loginBtn.addEventListener('click', function() {
            const email = emailInput.value.trim();
            const password = passwordInput.value.trim();

            if (!email) {
                alert('Please enter your email address');
                emailInput.focus();
                return;
            }

            if (!password) {
                alert('Please enter your password');
                passwordInput.focus();
                return;
            }

            if (!email.includes('@') || !email.includes('.')) {
                alert('Please enter a valid email address');
                emailInput.focus();
                return;
            }

            loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Authenticating...';
            loginBtn.disabled = true;
            loginForm.submit();
        });

        passwordInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                loginBtn.click();
            }
        });
    });