// Authentication JavaScript
class AuthManager {
    constructor() {
        this.authConfig = null;
        this.tokens = null;
        this.init();
    }

    async init() {
        // Load auth config
        await this.loadAuthConfig();
        
        // Check if we have stored tokens
        this.loadStoredTokens();
        
        // Set up login form if on login page
        if (document.getElementById('login-form')) {
            this.setupLoginForm();
        }
        
        // Check authentication status
        this.checkAuthStatus();
    }

    async loadAuthConfig() {
        try {
            const basePath = this.getBasePath();
            const response = await fetch(basePath + '/auth/config');
            this.authConfig = await response.json();
        } catch (error) {
            console.error('Failed to load auth config:', error);
        }
    }

    loadStoredTokens() {
        const stored = localStorage.getItem('auth_tokens');
        if (stored) {
            try {
                this.tokens = JSON.parse(stored);
            } catch (error) {
                localStorage.removeItem('auth_tokens');
            }
        }
    }

    storeTokens(tokens) {
        this.tokens = tokens;
        localStorage.setItem('auth_tokens', JSON.stringify(tokens));
    }

    clearTokens() {
        this.tokens = null;
        localStorage.removeItem('auth_tokens');
    }

    setupLoginForm() {
        const form = document.getElementById('login-form');
        const errorDiv = document.getElementById('error-message');
        const successDiv = document.getElementById('success-message');
        const loginBtn = document.getElementById('login-btn');
        const loginSpinner = document.getElementById('login-spinner');
        const loginText = document.getElementById('login-text');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Show loading state
            loginBtn.disabled = true;
            loginSpinner.classList.remove('d-none');
            loginText.textContent = 'Logging in...';
            errorDiv.classList.add('d-none');
            successDiv.classList.add('d-none');

            const formData = new FormData(form);
            const credentials = {
                username: formData.get('username'),
                password: formData.get('password')
            };

            try {
                const basePath = this.getBasePath();
                const response = await fetch(basePath + '/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(credentials)
                });

                const result = await response.json();

                if (response.ok && result.success) {
                    // Store tokens
                    this.storeTokens(result.tokens);
                    
                    // Show success message
                    successDiv.textContent = 'Login successful! Redirecting...';
                    successDiv.classList.remove('d-none');
                    
                    // Redirect to main page after a short delay
                    setTimeout(() => {
                        const basePath = this.getBasePath();
                        window.location.href = basePath + '/index';
                    }, 1500);
                } else {
                    // Show error message
                    errorDiv.textContent = result.error || 'Login failed';
                    errorDiv.classList.remove('d-none');
                }
            } catch (error) {
                errorDiv.textContent = 'Network error occurred';
                errorDiv.classList.remove('d-none');
            } finally {
                // Reset loading state
                loginBtn.disabled = false;
                loginSpinner.classList.add('d-none');
                loginText.textContent = 'Login';
            }
        });
    }

    checkAuthStatus() {
        // Get the base path (e.g., /prod or empty for root)
        const basePath = this.getBasePath();
        
        // If we're on a page that requires auth and we don't have tokens, redirect to login
        if (!this.tokens && this.requiresAuth()) {
            window.location.href = basePath + '/login';
            return false;
        }
        
        // If we're on the root path, redirect to index
        const currentPath = window.location.pathname;
        if (currentPath === '/' || currentPath === basePath + '/' || currentPath === basePath) {
            window.location.href = basePath + '/index';
            return false;
        }
        
        // If we have tokens, we can proceed
        return !!this.tokens;
    }

    getBasePath() {
        // Extract base path from current URL (e.g., /prod)
        const pathParts = window.location.pathname.split('/');
        if (pathParts.length > 1 && pathParts[1] === 'prod') {
            return '/prod';
        }
        return '';
    }

    requiresAuth() {
        // Check if current page requires authentication
        const path = window.location.pathname;
        const basePath = this.getBasePath();
        
        // Pages that don't require auth (account for base path)
        const publicPaths = [
            basePath + '/login',
            basePath + '/static',
            '/login',
            '/static'
        ];
        
        return !publicPaths.some(publicPath => path.startsWith(publicPath));
    }

    getAuthToken() {
        return this.tokens ? this.tokens.id_token : null;
    }

    async makeAuthenticatedRequest(url, options = {}) {
        const token = this.getAuthToken();
        if (!token) {
            throw new Error('No authentication token available');
        }

        const authOptions = {
            ...options,
            headers: {
                ...options.headers,
                'Authorization': `Bearer ${token}`
            }
        };

        const response = await fetch(url, authOptions);
        
        // If we get a 401, token might be expired - try to refresh
        if (response.status === 401) {
            const refreshed = await this.refreshToken();
            if (refreshed) {
                // Retry the request with new token
                authOptions.headers['Authorization'] = `Bearer ${this.getAuthToken()}`;
                return fetch(url, authOptions);
            } else {
                // Refresh failed, redirect to login
                this.logout();
                return response;
            }
        }

        return response;
    }

    async refreshToken() {
        if (!this.tokens || !this.tokens.refresh_token) {
            return false;
        }

        try {
            const basePath = this.getBasePath();
            const response = await fetch(basePath + '/auth/refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    refresh_token: this.tokens.refresh_token
                })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Update stored tokens (keep the same refresh token)
                const newTokens = {
                    ...result.tokens,
                    refresh_token: this.tokens.refresh_token
                };
                this.storeTokens(newTokens);
                return true;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
        }

        return false;
    }

    logout() {
        this.clearTokens();
        const basePath = this.getBasePath();
        window.location.href = basePath + '/login';
    }

    // Add logout button functionality
    setupLogoutButton() {
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                this.logout();
            });
        }
    }
}

// Initialize authentication manager
const authManager = new AuthManager();

// Make it globally available
window.authManager = authManager;
