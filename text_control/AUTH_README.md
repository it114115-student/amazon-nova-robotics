# Authentication Setup for Text Control Application

This document describes how to set up and use Cognito authentication for the text control robotics application.

## Overview

The application now uses AWS Cognito User Pools for authentication:

- **Public Routes**: `/index`, `/login`, `/static/*` - No authentication required
- **Protected Routes**: `/api/*` - Requires valid JWT token
- **Auth Routes**: `/auth/*` - Handle login/logout functionality

## Architecture

```
Browser → API Gateway → Lambda (Flask App)
   ↓
Cognito User Pool (Authentication)
```

### Authentication Flow

1. User visits `/index` → Redirected to `/login` if not authenticated
2. User enters credentials → Posted to `/auth/login`
3. Backend validates with Cognito → Returns JWT tokens
4. Frontend stores tokens in localStorage
5. Subsequent API calls include `Authorization: Bearer <token>` header
6. API Gateway validates token against Cognito User Pool
7. Valid requests proceed to protected routes

## Deployment Steps

### 1. Deploy CDK Stack

The CDK stack creates:

- Cognito User Pool with email sign-in
- User Pool Client for the application
- API Gateway with Cognito authorizer
- Lambda function with environment variables

```bash
cd cdk
npm run deploy
```

### 2. Get Configuration Values

After deployment, note these outputs:

- `CognitoUserPoolId`: User Pool ID
- `CognitoUserPoolClientId`: Client ID
- `textUrl`: Your application URL

### 3. Create Test User

```bash
# Set environment variable
export COGNITO_USER_POOL_ID="your-user-pool-id"

# Create a test user
cd text_control
python create_user.py testuser test@example.com TestPass123!
```

### 4. Test Authentication

1. Visit your application URL
2. You should be redirected to `/login`
3. Enter the test credentials
4. Upon successful login, you'll be redirected to `/index`
5. Test the chat functionality (now requires authentication)

## File Structure

```
text_control/
├── routes/
│   ├── auth.py          # Authentication endpoints
│   ├── api.py           # Protected API endpoints
│   └── ui.py            # Public UI routes
├── middleware.py        # JWT validation middleware
├── static/
│   ├── auth.js          # Frontend authentication
│   └── chat.js          # Updated chat with auth
├── templates/
│   ├── login.html       # Login page
│   └── index.html       # Main app (with logout)
└── create_user.py       # User creation utility
```

## Security Features

- **JWT Token Validation**: Tokens are validated against Cognito JWKS
- **Route Protection**: API routes require valid authentication
- **Token Refresh**: Automatic token refresh when expired
- **Secure Storage**: Tokens stored in localStorage (consider httpOnly cookies for production)

## Environment Variables

The Lambda function receives these environment variables:

- `COGNITO_USER_POOL_ID`: User Pool ID
- `COGNITO_CLIENT_ID`: User Pool Client ID
- `AWS_REGION`: AWS region (us-east-1)

## API Endpoints

### Authentication Routes

- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh access token
- `POST /auth/verify` - Verify token
- `GET /auth/config` - Get auth configuration

### Protected API Routes

- `POST /api/chat` - Chat with robots (requires auth)
- `GET /api/robots` - List robots (requires auth)
- `POST /api/robots` - Create robot (requires auth)
- `GET|PUT|DELETE /api/robots/{id}` - Robot operations (requires auth)

### Public Routes

- `GET /index` - Main application page
- `GET /login` - Login page
- `GET /static/*` - Static assets

## Troubleshooting

### Common Issues

1. **"Unauthorized" errors**: Check if token is included in Authorization header
2. **Token validation fails**: Verify User Pool ID and Client ID in environment
3. **CORS errors**: Ensure CORS headers are set for all requests
4. **User creation fails**: Check IAM permissions for Cognito operations

### Debug Authentication

```javascript
// In browser console
console.log("Auth tokens:", localStorage.getItem("auth_tokens"));
console.log("Current user:", window.authManager.tokens);
```

### Reset Authentication

```javascript
// Clear stored tokens
localStorage.removeItem("auth_tokens");
window.location.reload();
```

## Production Considerations

1. **Use HTTPS**: Always use HTTPS in production
2. **Token Storage**: Consider httpOnly cookies instead of localStorage
3. **Password Policy**: Configure strong password requirements in Cognito
4. **MFA**: Enable multi-factor authentication
5. **Session Management**: Implement proper logout and session timeout
6. **Error Handling**: Provide user-friendly error messages
7. **Monitoring**: Monitor authentication failures and suspicious activity

## Next Steps

1. **User Management**: Build admin interface for user management
2. **Role-Based Access**: Implement role-based permissions
3. **Social Login**: Add social identity providers
4. **Email Verification**: Enable email verification workflow
5. **Password Reset**: Implement password reset functionality
