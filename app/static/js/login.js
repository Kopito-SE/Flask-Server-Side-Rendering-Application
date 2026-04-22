// Login page specific JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const email = document.getElementById('email');
    const rememberCheckbox = document.querySelector('input[name="remember"]');

    // Check for saved email (fallback to old username key for backward compatibility)
    const savedEmail = localStorage.getItem('rememberedEmail') || localStorage.getItem('rememberedUsername');
    if (savedEmail && email) {
        email.value = savedEmail;
        if (rememberCheckbox) {
            rememberCheckbox.checked = true;
        }
    }

    // Form submission
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Clear previous errors
            utils.clearErrors(loginForm);
            
            // Validate fields
            let isValid = true;
            
            if (!email.value.trim()) {
                utils.showError(email, 'Email is required');
                isValid = false;
            }
            
            const password = document.getElementById('password');
            if (!password.value) {
                utils.showError(password, 'Password is required');
                isValid = false;
            }
            
            if (isValid) {
                const submitBtn = loginForm.querySelector('button[type="submit"]');
                utils.showLoading(submitBtn);
                
                // Handle "remember me"
                if (rememberCheckbox && rememberCheckbox.checked) {
                    localStorage.setItem('rememberedEmail', email.value);
                } else {
                    localStorage.removeItem('rememberedEmail');
                    localStorage.removeItem('rememberedUsername');
                }
                
                try {
                    // Form will submit normally
                    loginForm.submit();
                } catch (error) {
                    utils.hideLoading(submitBtn);
                    console.error('Login error:', error);
                    
                    // Show error message
                    const flashContainer = document.querySelector('.flash-container');
                    if (flashContainer) {
                        const errorDiv = document.createElement('div');
                        errorDiv.className = 'flash-message flash-error';
                        errorDiv.innerHTML = `
                            Connection error. Please try again.
                            <button class="flash-close" onclick="this.parentElement.remove()">&times;</button>
                        `;
                        flashContainer.appendChild(errorDiv);
                    }
                }
            }
        });
    }

    // Add password visibility toggle
    const togglePassword = document.createElement('button');
    togglePassword.type = 'button';
    togglePassword.className = 'btn-toggle-password';
    togglePassword.innerHTML = '👁️';
    togglePassword.style.cssText = `
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        background: none;
        border: none;
        cursor: pointer;
        opacity: 0.6;
    `;

    const passwordField = document.getElementById('password');
    if (passwordField) {
        passwordField.style.paddingRight = '40px';
        const wrapper = document.createElement('div');
        wrapper.style.position = 'relative';
        wrapper.style.width = '100%';
        
        passwordField.parentNode.insertBefore(wrapper, passwordField);
        wrapper.appendChild(passwordField);
        wrapper.appendChild(togglePassword);
        
        togglePassword.addEventListener('click', function() {
            const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordField.setAttribute('type', type);
            this.innerHTML = type === 'password' ? '👁️' : '👁️‍🗨️';
        });
    }
});
