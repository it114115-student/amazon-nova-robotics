# Cognito Authentication Setup

This application now includes AWS Cognito authentication. Users must log in before accessing the main speech control interface.

## Features Added

1. **Login Page** (`/login.html`) - Simple login form with username/password
2. **Server-Side Authentication** - Login handled server-side to avoid CORS/CORB issues
3. **Authentication Middleware** - Protects the main application and Socket.IO connections
4. **Automatic Redirects** - Unauthenticated users are redirected to login
5. **Token Management** - JWT tokens stored in localStorage with expiration checking
6. **Logout Functionality** - Logout button added to main interface

## Environment Variables

The following environment variables are required:

```bash
CognitoUserPoolId=your-user-pool-id
CognitoUserPoolClientId=your-client-id
CognitoRegion=us-east-1
```

These are automatically set by the CDK deployment.

## Development Setup

### 1. Create a Test User

After deploying with CDK, create a test user:

```bash
# Set environment variables
export CognitoUserPoolId="your-user-pool-id"
export CognitoRegion="us-east-1"
export TEST_USERNAME="testuser"
export TEST_PASSWORD="TempPassword123!"

# Create the user
npm run create-test-user
```

### 2. Login Flow

1. Navigate to your application URL
2. You'll be automatically redirected to `/login.html`
3. Enter your username and password
4. Upon successful authentication, you'll be redirected to the main application
5. Your session will persist until the token expires or you logout

## Security Features

- **JWT Token Validation** - All requests validated against Cognito
- **Socket.IO Authentication** - WebSocket connections require valid tokens
- **Automatic Token Expiry** - Expired tokens trigger re-authentication
- **Secure Token Storage** - Tokens stored in localStorage (consider httpOnly cookies for production)

## Files Modified/Added

### New Files:
- `public/login.html` - Login page
- `public/src/auth.js` - Authentication logic
- `public/src/auth-check.js` - Authentication verification for main app
- `create-test-user.js` - Script to create test users
- `COGNITO_SETUP.md` - This documentation

### Modified Files:
- `src/server.ts` - Added authentication middleware and login endpoint
- `public/src/main.js` - Added token to Socket.IO connection
- `public/index.html` - Added authentication check script
- `package.json` - Added Cognito dependencies and test user script
- `cdk/lib/construct/authenticator.ts` - Already configured for USER_PASSWORD_AUTH

## Production Considerations

1. **HTTPS Only** - Ensure all authentication happens over HTTPS
2. **Token Storage** - Consider using httpOnly cookies instead of localStorage
3. **Session Management** - Implement proper session timeout and refresh
4. **Error Handling** - Add comprehensive error handling for network issues
5. **User Management** - Implement user registration, password reset, etc.
6. **Rate Limiting** - Add rate limiting to login endpoints

## Troubleshooting

### Common Issues:

1. **"Authentication error: No token provided"**
   - Clear localStorage and try logging in again
   - Check that Cognito environment variables are set correctly

2. **"Invalid token"**
   - Token may have expired, try logging in again
   - Verify Cognito User Pool and Client configuration

3. **Connection errors**
   - Check network connectivity
   - Verify Cognito service is accessible from your deployment region

### Debug Steps:

1. Check browser console for authentication errors
2. Verify environment variables in server logs
3. Test Cognito configuration with AWS CLI
4. Check CloudWatch logs for detailed error messages