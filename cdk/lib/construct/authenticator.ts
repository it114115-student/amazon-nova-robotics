import { Construct } from "constructs";
import {
  UserPool,
  UserPoolClient,
  VerificationEmailStyle,
} from "aws-cdk-lib/aws-cognito";

export interface AuthenticatorProps {
  userPoolName?: string;
}

export class Authenticator extends Construct {
  public readonly userPool: UserPool;
  public readonly userPoolClient: UserPoolClient;

  constructor(scope: Construct, id: string, props?: AuthenticatorProps) {
    super(scope, id);

    this.userPool = new UserPool(this, "UserPool", {
      userPoolName: props?.userPoolName ?? "amazon-nona-robotics-app-user-pool",
      selfSignUpEnabled: false,
      signInAliases: { email: true },
      standardAttributes: {
        email: { required: true, mutable: true },
      },
      userVerification: {
        emailStyle: VerificationEmailStyle.CODE,
      },
    });

    this.userPoolClient = new UserPoolClient(this, "UserPoolClient", {
      userPool: this.userPool,
      generateSecret: false,
      authFlows: {
        userPassword: true,
        adminUserPassword: true,
      },
    });
  }
}
