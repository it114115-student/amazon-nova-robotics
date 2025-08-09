import { RestApi, LambdaIntegration } from "aws-cdk-lib/aws-apigateway";
import { CfnOutput, Duration } from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";

import { Construct } from "constructs";
import path = require("path");
import * as iam from "aws-cdk-lib/aws-iam";
import { DatabaseConstruct } from "./datebase";
import { UserPool, UserPoolClient } from "aws-cdk-lib/aws-cognito";
import { LambdaMcpServerConstruct } from "./mcp-server";
import * as crypto from "crypto";
import { PythonFunction } from "@aws-cdk/aws-lambda-python-alpha";

export interface TextControlWebConstructProps {
  readonly database: DatabaseConstruct;
  readonly mcpServerConstruct: LambdaMcpServerConstruct;
  readonly userPool: UserPool;
  readonly userPoolClient: UserPoolClient;
}

export class TextControlWebConstruct extends Construct {
  public readonly serviceUrl: string;

  constructor(
    scope: Construct,
    id: string,
    props: TextControlWebConstructProps
  ) {
    super(scope, id);

    const restApi = new RestApi(this, "TextControlWebApi", {
      restApiName: "TextControlWebApi",
      description: "API for Text Control Robot Web",
      deployOptions: {
        stageName: "prod",
        throttlingRateLimit: 100,
        throttlingBurstLimit: 200,
      },
    });

    const awsUserId = this.node.tryGetContext("AwsUserId") || "default-user";
    console.log("AWS User ID:", awsUserId);
    const hash = crypto.createHash("sha256").update(awsUserId).digest("hex");

    const chatSecretKey = crypto
      .createHash("sha256")
      .update(hash + "chat-secret-key")
      .digest("hex");

    const chatAccessKey = crypto
      .createHash("sha256")
      .update(hash + "chat-access-key")
      .digest("hex");

    const flaskLambda = new PythonFunction(this, "TextControlLambda", {
      entry: path.join(__dirname, "../../../text_control"),
      runtime: lambda.Runtime.PYTHON_3_12,
      index: "app.py",
      handler: "handler",
      timeout: Duration.seconds(30),
      environment: {
        AWS_BEDROCK_REGION: "us-east-1",
        RobotTable: props.database.robotTable.tableName,
        McpServerUrl: props.mcpServerConstruct.functionUrl.url,
        CognitoUserPoolId: props.userPool.userPoolId,
        CognitoUserPoolClientId: props.userPoolClient.userPoolClientId,
        FlaskSecretKey: hash,
        ChatSecretKey: chatSecretKey,
        ChatAccessKey: chatAccessKey,
      },
      bundling: {
        assetExcludes: [
          ".venv",
          "create_virtual_env.sh",
          ".dockerignore",
          "Dockerfile",
        ],
        // Pre-build commands to run before packaging
        commandHooks: {
          beforeBundling(inputDir: string, outputDir: string): string[] {
            return [
              `echo "Running pre-build commands for ${inputDir}"`,
              `cd ${inputDir}`,
              `chmod +x pre_deploy_update_commands.sh`,
              `./pre_deploy_update_commands.sh`,
            ];
          },
          afterBundling(inputDir: string, outputDir: string): string[] {
            return [
              `echo "Post-build verification for ${outputDir}"`,
              `ls -la ${outputDir}/command_config/`,
            ];
          },
        },
      },
    });

    props.database.robotTable.grantFullAccess(flaskLambda);

    flaskLambda.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["iot:Publish"],
        resources: [
          "arn:aws:iot:*:*:topic/robot_*/topic",
          "arn:aws:iot:*:*:topic/drone_*/topic",
          "arn:aws:iot:*:*:topic/dog_*/topic",
        ],
      })
    );
    flaskLambda.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ],
        resources: ["*"],
      })
    );

    // Add Cognito permissions for authentication
    flaskLambda.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "cognito-idp:AdminInitiateAuth",
          "cognito-idp:AdminCreateUser",
          "cognito-idp:AdminSetUserPassword",
          "cognito-idp:AdminGetUser",
          "cognito-idp:AdminDeleteUser",
          "cognito-idp:ListUsers",
          "cognito-idp:AdminRespondToAuthChallenge",
        ],
        resources: [props.userPool.userPoolArn],
      })
    );

    // Grant permission to invoke the MCP server Lambda function URL
    props.mcpServerConstruct.functionUrl.grantInvokeUrl(flaskLambda);

    const rootResource = restApi.root;

    // Add root redirect (public)
    rootResource.addMethod("GET", new LambdaIntegration(flaskLambda));

    // Add UI routes (authentication handled by Flask middleware)
    const indexResource = rootResource.addResource("index");
    indexResource.addMethod("GET", new LambdaIntegration(flaskLambda));

    const robotResource = rootResource.addResource("robot");
    robotResource.addMethod("GET", new LambdaIntegration(flaskLambda));

    // Add public routes (no authentication required)
    const loginResource = rootResource.addResource("login");
    loginResource.addMethod("GET", new LambdaIntegration(flaskLambda));

    const staticResource = rootResource.addResource("static");
    staticResource.addProxy({
      defaultIntegration: new LambdaIntegration(flaskLambda),
      anyMethod: true,
    });

    // Add API routes (authentication handled by Flask middleware)
    const apiResource = rootResource.addResource("api");
    apiResource.addProxy({
      defaultIntegration: new LambdaIntegration(flaskLambda),
      anyMethod: true,
    });

    // Add auth routes for login/logout
    const authResource = rootResource.addResource("auth");
    authResource.addProxy({
      defaultIntegration: new LambdaIntegration(flaskLambda),
      anyMethod: true,
    });

    this.serviceUrl = restApi.url + "index";

    new CfnOutput(this, "XiaoiceChatSecretKey", {
      key: "XiaoiceChatSecretKey",
      value: chatSecretKey,
    });

    new CfnOutput(this, "XiaoiceChatAccessKey", {
      key: "XiaoiceChatAccessKey",
      value: chatAccessKey,
    });

    new CfnOutput(this, "XiaoiceApiUrl", {
      key: "XiaoiceApiUrl",
      value: restApi.url + "api/xiaoice-chat-api",
    });
  }
}
