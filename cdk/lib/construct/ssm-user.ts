import { Construct } from "constructs";
import * as iam from "aws-cdk-lib/aws-iam";
import * as cdk from "aws-cdk-lib";

export interface SsmUserConstructProps {
  userName?: string;
}

export class SsmUserConstruct extends Construct {
  public readonly ssmUser: iam.User;
  public readonly accessKey: iam.CfnAccessKey;

  constructor(scope: Construct, id: string, props?: SsmUserConstructProps) {
    super(scope, id);

    const userName = props?.userName || "RobotSsmRunCommandUser";

    this.ssmUser = new iam.User(this, "SsmRunCommandUser", {
      userName: userName,
    });

    this.ssmUser.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["ssm:List*", "ssm:Describe*", "ssm:Get*"],
        resources: ["*"],
      })
    );

    this.ssmUser.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["ssm:SendCommand", "ssm:StartSession"],
        resources: ["arn:aws:ssm:*:*:document/*"],
      })
    );

    this.ssmUser.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["ssm:SendCommand", "ssm:StartSession"],
        resources: ["arn:aws:ssm:*:*:managed-instance/*"],
      })
    );

    this.ssmUser.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["ssm:CancelCommand"],
        resources: ["*"],
      })
    );

    // Add policy for session resources
    this.ssmUser.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["ssm:ResumeSession", "ssm:TerminateSession"],
        resources: ["arn:aws:ssm:*:*:session/${aws:username}-*"],
      })
    );

    this.ssmUser.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "iam:ChangePassword",
          "iam:GetAccountPasswordPolicy",
          "ssm:GetDocument",
          "ssm:ListCommandInvocations",
          "ssm:ListCommands",
          "ssm:UpdateInstanceInformation",
          "sts:GetCallerIdentity",
        ],
        resources: ["*"],
      })
    );

    new cdk.CfnOutput(this, "SsmRunCommandUserName", {
      value: this.ssmUser.userName,
      description: "IAM user with Run Command access for robots.",
    });

    this.accessKey = new iam.CfnAccessKey(this, "CfnAccessKey", {
      userName: this.ssmUser.userName,
    });

    new cdk.CfnOutput(this, "accessKeyId", { value: this.accessKey.ref });
    new cdk.CfnOutput(this, "secretAccessKey", {
      value: this.accessKey.attrSecretAccessKey,
    });
  }
}
