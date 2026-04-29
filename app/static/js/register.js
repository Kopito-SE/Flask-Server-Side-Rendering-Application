// Registration page specific JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('registerForm');
    const email = document.getElementById('email');  // ADDED: Get email element
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm_password');
    const username = document.getElementById('username');
    const registerBtn = document.getElementById('registerBtn');
    
    // Create utils object if it doesn't exist
    window.utils = window.utils || {
        showLoading: function(btn) {
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = 'Registering...';
            }
        },
        hideLoading: function(btn) {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = 'Register';
            }
        },
        showError: function(input, message) {
            const feedback = input.nextElementSibling;
            if (feedback && feedback.classList.contains('validation-feedback')) {
                feedback.textContent = message;
                feedback.classList.add('error');
            }
        },
        clearErrors: function(form) {
            const errors = form.querySelectorAll('.validation-feedback.error');
            errors.forEach(error => {
                error.textContent = '';
                error.classList.remove('error');
            });
        }
    };

    // Real-time validation
    if (username) {
        username.addEventListener('input', function() {
            validateUsername(this.value);
        });
    }

    // ADDED: Email real-time validation
    if (email) {
        email.addEventListener('input', function() {
            validateEmail(this.value);
        });
    }

    if (password) {
        password.addEventListener('input', function() {
            validatePassword(this.value);
            if (confirmPassword) {
                validateConfirm(confirmPassword.value);
            }
        });
    }

    if (confirmPassword) {
        confirmPassword.addEventListener('input', function() {
            validateConfirm(this.value);
        });
    }

    // Form submission
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            // Clear previous errors and tips
            utils.clearErrors(registerForm);
            clearPasswordTips();
            
            // Get values
            const usernameValue = username.value.trim();
            const emailValue = email ? email.value.trim() : '';  // ADDED: Get email value
            const passwordValue = password.value;
            
            // Validate all fields
            const isUsernameValid = validateUsername(usernameValue);
            const isEmailValid = validateEmail(emailValue);  // ADDED: Email validation
            const isPasswordValid = validatePassword(passwordValue);
            const isConfirmValid = validateConfirm(confirmPassword ? confirmPassword.value : '');
            
            // Only prevent submission if validation fails (including email)
            if (!isUsernameValid || !isEmailValid || !isPasswordValid || !isConfirmValid) {  // MODIFIED: Added isEmailValid
                e.preventDefault();
                return false;
            }
            
            // Show loading state
            if (registerBtn) {
                utils.showLoading(registerBtn);
            }
            
            // Form will submit normally - don't call registerForm.submit() here
            // Just let the natural form submission happen
        });
    }

    // Helper function to clear password tips
    function clearPasswordTips() {
        const tipsContainer = document.getElementById('passwordTips');
        if (tipsContainer) {
            tipsContainer.innerHTML = '';
        }
    }

    // Validation functions
    function validateUsername(value) {
        const usernameRegex = /^[a-zA-Z0-9_]+$/;
        const usernameFeedback = document.getElementById('username-feedback');
        
        if (value.length < 3) {
            if (usernameFeedback) {
                usernameFeedback.textContent = 'Username must be at least 3 characters long';
                usernameFeedback.classList.add('error');
            }
            return false;
        }
        
        if (!usernameRegex.test(value)) {
            if (usernameFeedback) {
                usernameFeedback.textContent = 'Username can only contain letters, numbers, and underscores';
                usernameFeedback.classList.add('error');
            }
            return false;
        }
        
        // Clear any existing error message when validation passes
        if (usernameFeedback) {
            usernameFeedback.textContent = '';
            usernameFeedback.classList.remove('error');
        }
        
        return true;
    }

    // ADDED: New email validation function
    function validateEmail(value) {
        const emailFeedback = document.getElementById('email-feedback');
        
        // Standard email regex pattern
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        
        if (!value) {
            if (emailFeedback) {
                emailFeedback.textContent = 'Email is required';
                emailFeedback.classList.add('error');
            }
            return false;
        }
        
        if (!emailRegex.test(value)) {
            if (emailFeedback) {
                emailFeedback.textContent = 'Please enter a valid email address (e.g., name@example.com)';
                emailFeedback.classList.add('error');
            }
            return false;
        }
        
        // Clear any existing error message when validation passes
        if (emailFeedback) {
            emailFeedback.textContent = '';
            emailFeedback.classList.remove('error');
        }
        
        return true;
    }

    function validatePassword(value) {
        const passwordFeedback = document.getElementById('password-feedback');
        const tipsContainer = document.getElementById('passwordTips');
        
        // Clear previous tips
        clearPasswordTips();
        
        if (value.length < 6) {
            if (passwordFeedback) {
                passwordFeedback.textContent = 'Password must be at least 6 characters long';
                passwordFeedback.classList.add('error');
            }
            return false;
        }
        // length is OK; clear any lingering error text/state
        if (passwordFeedback) {
            passwordFeedback.textContent = '';
            passwordFeedback.classList.remove('error');
        }
        
        // Check for password strength
        const hasUpperCase = /[A-Z]/.test(value);
        const hasLowerCase = /[a-z]/.test(value);
        const hasNumbers = /\d/.test(value);
        
        if (!(hasUpperCase && hasLowerCase && hasNumbers) && tipsContainer) {
            // Create tip element instead of multiple divs
            const tip = document.createElement('div');
            tip.className = 'tip';
            tip.textContent = '💡 Tip: Use uppercase, lowercase, and numbers for a stronger password';
            tipsContainer.appendChild(tip);
        }
        
        return true;
    }

    function validateConfirm(value) {
        const confirmFeedback = document.getElementById('confirm-feedback');

        if (!value) {
            if (confirmFeedback) {
                confirmFeedback.textContent = 'Please confirm your password';
                confirmFeedback.classList.add('error');
            }
            return false;
        }

        if (password && value !== password.value) {
            if (confirmFeedback) {
                confirmFeedback.textContent = 'Passwords do not match';
                confirmFeedback.classList.add('error');
            }
            return false;
        }

        if (confirmFeedback) {
            confirmFeedback.textContent = '';
            confirmFeedback.classList.remove('error');
        }
        return true;
    }
});