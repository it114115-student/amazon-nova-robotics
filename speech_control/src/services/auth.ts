import {
  CognitoIdentityProviderClient,
  InitiateAuthCommand,
  RespondToAuthChallengeCommand,
  SignUpCommand,
  ConfirmSignUpCommand,
  ForgotPasswordCommand,
  ConfirmForgotPasswordCommand,
  GetUserCommand,
  AdminCreateUserCommand,
  AdminSetUserPasswordCommand,
  AdminDeleteUserCommand,
  AdminListGroupsForUserCommand,
  AdminAddUserToGroupCommand,
  AdminRemoveUserFromGroupCommand,
  ListUsersCommand,
  AuthFlowType,
  AttributeType,
  UserType,
} from "@aws-sdk/client-cognito-identity-provider";
import { fromContainerMetadata, fromIni } from "@aws-sdk/credential-providers";
import jwt, { JwtPayload } from "jsonwebtoken";

// Simple JWKS client interface to avoid type issues
interface JwksKey {
  getPublicKey(): string;
}

interface JwksClient {
  getSigningKey(kid: string): Promise<JwksKey>;
}

// Simple jwks client function
function createJwksClient(jwksUri: string): JwksClient {
  const jwksClient = require("jwks-client");
  // Handle both default export and named export patterns
  const clientConstructor = jwksClient.default || jwksClient;

  const client = clientConstructor({
    jwksUri: jwksUri,
    requestHeaders: {},
    timeout: 30000,
  });

  return {
    getSigningKey: (kid: string): Promise<JwksKey> => {
      return new Promise((resolve, reject) => {
        client.getSigningKey(kid, (err: any, key: any) => {
          if (err) {
            reject(err);
          } else {
            // Handle different key formats from jwks-client
            console.log('JWKS key object:', Object.keys(key), typeof key);
            let publicKey: string;

            if (typeof key.getPublicKey === 'function') {
              publicKey = key.getPublicKey();
            } else if (key.publicKey) {
              publicKey = key.publicKey;
            } else if (key.rsaPublicKey) {
              publicKey = key.rsaPublicKey;
            } else if (typeof key === 'string') {
              publicKey = key;
            } else {
              // Log the key structure for debugging
              console.error('Unknown key format:', key);
              reject(new Error('Unable to extract public key from JWKS response'));
              return;
            }

            resolve({
              getPublicKey: () => publicKey
            });
          }
        });
      });
    }
  };
}

interface CognitoConfig {
  userPoolId: string;
  clientId: string;
  region: string;
}

interface AuthResponse {
  accessToken?: string;
  idToken?: string;
  refreshToken?: string;
  challengeName?: string;
  challengeParameters?: Record<string, string>;
  session?: string;
}

interface UserInfo {
  username: string;
  email: string;
  emailVerified: boolean;
  groups?: string[];
}

export class CognitoAuthService {
  private client: CognitoIdentityProviderClient;
  private config: CognitoConfig;
  private jwksClientInstance: JwksClient;

  constructor(config: CognitoConfig) {
    this.config = config;

    const isInCloud = process.env.IsInCloud || false;
    const AWS_PROFILE_NAME = process.env.AWS_PROFILE || "default";

    this.client = new CognitoIdentityProviderClient({
      region: config.region,
      credentials: isInCloud
        ? fromContainerMetadata()
        : fromIni({ profile: AWS_PROFILE_NAME }),
    });

    // Initialize JWKS client for token verification
    this.jwksClientInstance = createJwksClient(
      `https://cognito-idp.${config.region}.amazonaws.com/${config.userPoolId}/.well-known/jwks.json`
    );
  }

  /**
   * Sign in a user with username and password
   */
  async signIn(username: string, password: string): Promise<AuthResponse> {
    try {
      const command = new InitiateAuthCommand({
        AuthFlow: AuthFlowType.USER_PASSWORD_AUTH,
        ClientId: this.config.clientId,
        AuthParameters: {
          USERNAME: username,
          PASSWORD: password,
        },
      });

      const response = await this.client.send(command);

      return {
        accessToken: response.AuthenticationResult?.AccessToken,
        idToken: response.AuthenticationResult?.IdToken,
        refreshToken: response.AuthenticationResult?.RefreshToken,
        challengeName: response.ChallengeName,
        challengeParameters: response.ChallengeParameters,
        session: response.Session,
      };
    } catch (error) {
      console.error("Error signing in:", error);
      throw error;
    }
  }

  /**
   * Respond to authentication challenge
   */
  async respondToAuthChallenge(
    challengeName: string,
    session: string,
    challengeResponses: Record<string, string>
  ): Promise<AuthResponse> {
    try {
      const command = new RespondToAuthChallengeCommand({
        ClientId: this.config.clientId,
        ChallengeName: challengeName as any,
        Session: session,
        ChallengeResponses: challengeResponses,
      });

      const response = await this.client.send(command);

      return {
        accessToken: response.AuthenticationResult?.AccessToken,
        idToken: response.AuthenticationResult?.IdToken,
        refreshToken: response.AuthenticationResult?.RefreshToken,
        challengeName: response.ChallengeName,
        challengeParameters: response.ChallengeParameters,
        session: response.Session,
      };
    } catch (error) {
      console.error("Error responding to auth challenge:", error);
      throw error;
    }
  }

  /**
   * Sign up a new user (Admin only - since selfSignUp is disabled)
   */
  async adminCreateUser(
    username: string,
    email: string,
    temporaryPassword: string,
    permanent: boolean = false
  ): Promise<void> {
    try {
      const createCommand = new AdminCreateUserCommand({
        UserPoolId: this.config.userPoolId,
        Username: username,
        UserAttributes: [
          {
            Name: "email",
            Value: email,
          },
          {
            Name: "email_verified",
            Value: "true",
          },
        ],
        TemporaryPassword: temporaryPassword,
        MessageAction: "SUPPRESS", // Don't send welcome email
      });

      await this.client.send(createCommand);

      if (permanent) {
        const setPasswordCommand = new AdminSetUserPasswordCommand({
          UserPoolId: this.config.userPoolId,
          Username: username,
          Password: temporaryPassword,
          Permanent: true,
        });

        await this.client.send(setPasswordCommand);
      }
    } catch (error) {
      console.error("Error creating user:", error);
      throw error;
    }
  }

  /**
   * Delete a user (Admin only)
   */
  async adminDeleteUser(username: string): Promise<void> {
    try {
      const command = new AdminDeleteUserCommand({
        UserPoolId: this.config.userPoolId,
        Username: username,
      });

      await this.client.send(command);
    } catch (error) {
      console.error("Error deleting user:", error);
      throw error;
    }
  }

  /**
   * Get user information from access token
   */
  async getUser(accessToken: string): Promise<UserInfo> {
    try {
      const command = new GetUserCommand({
        AccessToken: accessToken,
      });

      const response = await this.client.send(command);

      const email =
        response.UserAttributes?.find(
          (attr: AttributeType) => attr.Name === "email"
        )?.Value || "";
      const emailVerified =
        response.UserAttributes?.find(
          (attr: AttributeType) => attr.Name === "email_verified"
        )?.Value === "true";

      return {
        username: response.Username!,
        email,
        emailVerified,
      };
    } catch (error) {
      console.error("Error getting user:", error);
      throw error;
    }
  }

  /**
   * List all users (Admin only)
   */
  async listUsers(limit: number = 60): Promise<UserInfo[]> {
    try {
      const command = new ListUsersCommand({
        UserPoolId: this.config.userPoolId,
        Limit: limit,
      });

      const response = await this.client.send(command);

      return (
        response.Users?.map((user: UserType) => {
          const email =
            user.Attributes?.find(
              (attr: AttributeType) => attr.Name === "email"
            )?.Value || "";
          const emailVerified =
            user.Attributes?.find(
              (attr: AttributeType) => attr.Name === "email_verified"
            )?.Value === "true";

          return {
            username: user.Username!,
            email,
            emailVerified,
          };
        }) || []
      );
    } catch (error) {
      console.error("Error listing users:", error);
      throw error;
    }
  }

  /**
   * Verify JWT token
   */
  async verifyToken(token: string): Promise<any> {
    try {
      const decoded = jwt.decode(token, { complete: true });
      if (!decoded || !decoded.header.kid) {
        throw new Error("Invalid token");
      }

      const key = await this.jwksClientInstance.getSigningKey(
        decoded.header.kid
      );
      const signingKey = key.getPublicKey();

      const verified = jwt.verify(token, signingKey, {
        algorithms: ["RS256"],
        issuer: `https://cognito-idp.${this.config.region}.amazonaws.com/${this.config.userPoolId}`,
      });

      return verified;
    } catch (error) {
      console.error("Error verifying token:", error);
      throw error;
    }
  }

  /**
   * Forgot password
   */
  async forgotPassword(username: string): Promise<void> {
    try {
      const command = new ForgotPasswordCommand({
        ClientId: this.config.clientId,
        Username: username,
      });

      await this.client.send(command);
    } catch (error) {
      console.error("Error sending forgot password:", error);
      throw error;
    }
  }

  /**
   * Confirm forgot password
   */
  async confirmForgotPassword(
    username: string,
    confirmationCode: string,
    newPassword: string
  ): Promise<void> {
    try {
      const command = new ConfirmForgotPasswordCommand({
        ClientId: this.config.clientId,
        Username: username,
        ConfirmationCode: confirmationCode,
        Password: newPassword,
      });

      await this.client.send(command);
    } catch (error) {
      console.error("Error confirming forgot password:", error);
      throw error;
    }
  }
}
