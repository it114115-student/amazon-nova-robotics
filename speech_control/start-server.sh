#!/bin/bash

# Load CDK stack environment variables
source ../load_cdkstack_env.sh

# Set Cognito environment variables for the server
export COGNITO_USER_POOL_ID="$CognitoUserPoolId"
export COGNITO_CLIENT_ID="$CognitoUserPoolClientId"
export COGNITO_REGION="us-east-1"

# Set AWS region
export AWS_BEDROCK_REGION="us-east-1"

echo "Starting speech control server with:"
echo "COGNITO_USER_POOL_ID: $COGNITO_USER_POOL_ID"
echo "COGNITO_CLIENT_ID: $COGNITO_CLIENT_ID"
echo "COGNITO_REGION: $COGNITO_REGION"

# Start the server
npm run dev