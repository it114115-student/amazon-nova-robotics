// Simple authentication without AWS SDK - server-side authentication

// Show error message
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

// Hide error message
function hideError() {
    const errorDiv = document.getElementById('error-message');
    errorDiv.style.display = 'none';
}

// Show loading state
function showLoading(show = true) {
    const loadingDiv = document.getElementById('loading');
    const loginButton = document.getElementById('login-button');

    if (show) {
        loadingDiv.style.display = 'block';
        loginButton.disabled = true;
        loginButton.textContent = 'Logging in...';
    } else {
        loadingDiv.style.display = 'none';
        loginButton.disabled = false;
        loginButton.textContent = 'Login';
    }
}

// Authenticate user via server
async function authenticateUser(username, password) {
    const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Authentication failed');
    }

    const result = await response.json();

    // Store tokens in localStorage
    localStorage.setItem('accessToken', result.accessToken);
    localStorage.setItem('idToken', result.idToken);
    localStorage.setItem('refreshToken', result.refreshToken);

    return result;
}

// Check if user is already authenticated
function checkExistingAuth() {
    const accessToken = localStorage.getItem('accessToken');
    if (accessToken) {
        // Verify token is still valid
        try {
            const payload = JSON.parse(atob(accessToken.split('.')[1]));
            const currentTime = Math.floor(Date.now() / 1000);

            if (payload.exp > currentTime) {
                // Token is still valid, redirect to main app
                window.location.href = '/';
                return true;
            } else {
                // Token expired, clear storage
                localStorage.clear();
            }
        } catch (error) {
            // Invalid token, clear storage
            localStorage.clear();
        }
    }
    return false;
}

// Handle form submission
async function handleLogin(event) {
    event.preventDefault();

    hideError();
    showLoading(true);

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        await authenticateUser(username, password);
        // Redirect to main application
        window.location.href = '/';
    } catch (error) {
        showLoading(false);
        let errorMessage = 'Login failed. Please try again.';

        // Parse server error messages
        if (error.message.includes('NotAuthorizedException')) {
            errorMessage = 'Invalid username or password.';
        } else if (error.message.includes('UserNotConfirmedException')) {
            errorMessage = 'Please confirm your account before logging in.';
        } else if (error.message.includes('PasswordResetRequiredException')) {
            errorMessage = 'Password reset required. Please contact administrator.';
        } else if (error.message.includes('UserNotFoundException')) {
            errorMessage = 'User not found.';
        } else if (error.message.includes('TooManyRequestsException')) {
            errorMessage = 'Too many login attempts. Please try again later.';
        } else if (error.message) {
            errorMessage = error.message;
        }

        showError(errorMessage);
    }
}

// Initialize the page
function initializePage() {
    // Check if user is already authenticated
    if (checkExistingAuth()) {
        return;
    }

    // Set up form handler
    const loginForm = document.getElementById('login-form');
    loginForm.addEventListener('submit', handleLogin);
}

// Start when page is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePage);
} else {
    initializePage();
}