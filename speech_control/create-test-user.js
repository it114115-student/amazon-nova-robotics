const { CognitoIdentityProviderClient, AdminCreateUserCommand, AdminSetUserPasswordCommand } = require('@aws-sdk/client-cognito-identity-provider');

// Configuration
const USER_POOL_ID = process.env.CognitoUserPoolId || 'your-user-pool-id';
const REGION = process.env.CognitoRegion || 'us-east-1';
const USERNAME = process.env.TEST_USERNAME || 'testuser';
const PASSWORD = process.env.TEST_PASSWORD || 'TempPassword123!';

const cognitoClient = new CognitoIdentityProviderClient({
    region: REGION
});

async function createTestUser() {
    try {
        console.log(`Creating test user: ${USERNAME}`);

        // Create user
        const createUserCommand = new AdminCreateUserCommand({
            UserPoolId: USER_POOL_ID,
            Username: USERNAME,
            MessageAction: 'SUPPRESS', // Don't send welcome email
            TemporaryPassword: PASSWORD,
        });

        await cognitoClient.send(createUserCommand);
        console.log('User created successfully');

        // Set permanent password
        const setPasswordCommand = new AdminSetUserPasswordCommand({
            UserPoolId: USER_POOL_ID,
            Username: USERNAME,
            Password: PASSWORD,
            Permanent: true
        });

        await cognitoClient.send(setPasswordCommand);
        console.log('Password set successfully');

        console.log(`Test user created:
    Username: ${USERNAME}
    Password: ${PASSWORD}
    
    You can now use these credentials to log in to the application.`);

    } catch (error) {
        console.error('Error creating test user:', error);

        if (error.name === 'UsernameExistsException') {
            console.log('User already exists. Trying to set password...');
            try {
                const setPasswordCommand = new AdminSetUserPasswordCommand({
                    UserPoolId: USER_POOL_ID,
                    Username: USERNAME,
                    Password: PASSWORD,
                    Permanent: true
                });

                await cognitoClient.send(setPasswordCommand);
                console.log('Password updated successfully');
            } catch (passwordError) {
                console.error('Error updating password:', passwordError);
            }
        }
    }
}

createTestUser();