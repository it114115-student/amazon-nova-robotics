// Cognito Authentication using CDN-loaded libraries
// Global authentication manager
window.CognitoAuth = (function () {
  let userPool = null;
  let currentUser = null;
  let authConfig = null;

  // Initialize the authentication system
  function init(config) {
    authConfig = config;
    userPool = new AmazonCognitoIdentity.CognitoUserPool({
      UserPoolId: config.userPoolId,
      ClientId: config.clientId,
    });

    // Check if user is already authenticated
    currentUser = userPool.getCurrentUser();
    if (currentUser) {
      currentUser.getSession((err, session) => {
        if (err) {
          console.error('Session error:', err);
          return;
        }
        if (session && session.isValid()) {
          console.log('User already authenticated');
          hideAuthModal();
          showUserInfo(currentUser.getUsername());
        } else {
          showAuthModal();
        }
      });
    } else {
      showAuthModal();
    }
  }

  // Show authentication modal
  function showAuthModal() {
    document.getElementById('auth-modal').style.display = 'block';
    document.getElementById('user-info').style.display = 'none';
  }

  // Hide authentication modal
  function hideAuthModal() {
    document.getElementById('auth-modal').style.display = 'none';
    document.getElementById('user-info').style.display = 'block';
  }

  // Show user info
  function showUserInfo(username) {
    document.getElementById('user-name').textContent = username;
    document.getElementById('user-info').style.display = 'block';
  }

  // Sign in function
  function signIn(username, password) {
    return new Promise((resolve, reject) => {
      const authenticationDetails = new AmazonCognitoIdentity.AuthenticationDetails({
        Username: username,
        Password: password,
      });

      const cognitoUser = new AmazonCognitoIdentity.CognitoUser({
        Username: username,
        Pool: userPool,
      });

      cognitoUser.authenticateUser(authenticationDetails, {
        onSuccess: (session) => {
          currentUser = cognitoUser;
          const tokens = {
            accessToken: session.getAccessToken().getJwtToken(),
            idToken: session.getIdToken().getJwtToken(),
            refreshToken: session.getRefreshToken().getToken(),
          };
          localStorage.setItem('cognitoTokens', JSON.stringify(tokens));
          hideAuthModal();
          showUserInfo(username);
          resolve(tokens);
        },
        onFailure: (err) => {
          reject(err);
        },
        newPasswordRequired: (userAttributes, requiredAttributes) => {
          // Store the user object for completing the challenge
          window.cognitoUserForChallenge = cognitoUser;
          showNewPasswordForm();
          reject({
            name: 'NewPasswordRequiredError',
            message: 'New password required',
            challengeName: 'NEW_PASSWORD_REQUIRED',
          });
        },
      });
    });
  }

  // Complete new password challenge
  function completeNewPasswordChallenge(newPassword) {
    return new Promise((resolve, reject) => {
      if (!window.cognitoUserForChallenge) {
        reject(new Error('No challenge in progress'));
        return;
      }

      window.cognitoUserForChallenge.completeNewPasswordChallenge(
        newPassword,
        {},
        {
          onSuccess: (session) => {
            currentUser = window.cognitoUserForChallenge;
            const tokens = {
              accessToken: session.getAccessToken().getJwtToken(),
              idToken: session.getIdToken().getJwtToken(),
              refreshToken: session.getRefreshToken().getToken(),
            };
            localStorage.setItem('cognitoTokens', JSON.stringify(tokens));
            hideNewPasswordForm();
            hideAuthModal();
            showUserInfo(currentUser.getUsername());
            window.cognitoUserForChallenge = null;
            resolve(tokens);
          },
          onFailure: (err) => {
            reject(err);
          },
        }
      );
    });
  }

  // Show new password form
  function showNewPasswordForm() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('new-password-form').style.display = 'block';
  }

  // Hide new password form
  function hideNewPasswordForm() {
    document.getElementById('new-password-form').style.display = 'none';
    document.getElementById('login-form').style.display = 'block';
  }

  // Sign out function
  function signOut() {
    if (currentUser) {
      currentUser.signOut();
    }
    currentUser = null;
    localStorage.removeItem('cognitoTokens');
    showAuthModal();
  }

  // Get access token
  function getAccessToken() {
    return new Promise((resolve) => {
      if (!currentUser) {
        resolve(null);
        return;
      }

      currentUser.getSession((err, session) => {
        if (err || !session || !session.isValid()) {
          resolve(null);
          return;
        }
        resolve(session.getAccessToken().getJwtToken());
      });
    });
  }

  // Check if authenticated
  function isAuthenticated() {
    return new Promise((resolve) => {
      if (!currentUser) {
        resolve(false);
        return;
      }

      currentUser.getSession((err, session) => {
        if (err || !session || !session.isValid()) {
          resolve(false);
          return;
        }
        resolve(true);
      });
    });
  }

  // Show error message
  function showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    errorElement.textContent = message;
    errorElement.style.display = 'block';
  }

  // Hide error message
  function hideError(elementId) {
    const errorElement = document.getElementById(elementId);
    errorElement.style.display = 'none';
  }

  // Public API
  return {
    init,
    signIn,
    signOut,
    getAccessToken,
    isAuthenticated,
    completeNewPasswordChallenge,
    showError,
    hideError,
  };
})();

// Initialize authentication when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
  // Get Cognito config from environment or default values
  // In production, these would come from your CDK stack outputs
  const cognitoConfig = {
    userPoolId: 'us-east-1_TCeygz7nY', // Will be replaced by actual values
    clientId: '51l3dtt6e6o3e7s6pu1i4bre0m', // Will be replaced by actual values
    region: 'us-east-1',
  };

  // Try to get config from global window object if set by server
  if (window.COGNITO_CONFIG) {
    Object.assign(cognitoConfig, window.COGNITO_CONFIG);
  }

  CognitoAuth.init(cognitoConfig);

  // Login form event handlers
  document.getElementById('login-btn').addEventListener('click', async function () {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    if (!username || !password) {
      CognitoAuth.showError('auth-error', 'Please enter both username and password');
      return;
    }

    CognitoAuth.hideError('auth-error');

    try {
      await CognitoAuth.signIn(username, password);
      console.log('Login successful');
    } catch (error) {
      console.error('Login error:', error);
      if (error.name === 'NewPasswordRequiredError') {
        // New password form will be shown automatically
        return;
      }
      CognitoAuth.showError('auth-error', error.message || 'Login failed');
    }
  });

  // New password form event handlers
  document.getElementById('set-password-btn').addEventListener('click', async function () {
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;

    if (!newPassword || !confirmPassword) {
      CognitoAuth.showError('new-password-error', 'Please enter both password fields');
      return;
    }

    if (newPassword !== confirmPassword) {
      CognitoAuth.showError('new-password-error', 'Passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      CognitoAuth.showError('new-password-error', 'Password must be at least 8 characters long');
      return;
    }

    CognitoAuth.hideError('new-password-error');

    try {
      await CognitoAuth.completeNewPasswordChallenge(newPassword);
      console.log('Password set successfully');
    } catch (error) {
      console.error('Set password error:', error);
      CognitoAuth.showError('new-password-error', error.message || 'Failed to set password');
    }
  });

  // Logout button event handler
  document.getElementById('logout-btn').addEventListener('click', function () {
    CognitoAuth.signOut();
  });

  // Allow Enter key to submit forms
  document.getElementById('password').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
      document.getElementById('login-btn').click();
    }
  });

  document.getElementById('confirm-password').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
      document.getElementById('set-password-btn').click();
    }
  });
});
