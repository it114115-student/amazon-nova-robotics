#!/usr/bin/env python3
"""
Script to create users in Cognito User Pool for testing
"""

import os
import sys

import boto3
from botocore.exceptions import ClientError


def create_user(email, temporary_password, user_pool_id):
    """Create a user in Cognito User Pool using email as username"""
    client = boto3.client("cognito-idp")

    try:
        client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "true"},
            ],
            TemporaryPassword=temporary_password,
            MessageAction="SUPPRESS",  # Don't send welcome email
        )

        print(f"User {email} created successfully!")

        # Set permanent password
        try:
            client.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=email,
                Password=temporary_password,
                Permanent=True,
            )
            print(f"Password set as permanent for {email}")
        except ClientError as e:
            print(f"Warning: Could not set permanent password: {e}")

        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "UsernameExistsException":
            print(f"User {email} already exists")
        else:
            print(f"Error creating user: {e}")
        return False


def main():
    """Main function to create a Cognito user from command line arguments."""
    if len(sys.argv) != 3:
        print("Usage: python create_user.py <email> <password>")
        print("Example: python create_user.py test@example.com TestPass123!")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]

    # Get User Pool ID from environment or CDK output
    user_pool_id = os.getenv("CognitoUserPoolId")

    if not user_pool_id:
        print("Error: CognitoUserPoolId environment variable not set")
        print("You can get this from the CDK stack outputs")
        sys.exit(1)

    print(f"Creating user with email {email}...")

    if create_user(email, password, user_pool_id):
        print("\nUser created successfully!")
        print(f"Username (email): {email}")
        print(f"Password: {password}")
        print("\nYou can now use these credentials to log in to the application.")
    else:
        print("Failed to create user")
        sys.exit(1)


if __name__ == "__main__":
    main()
