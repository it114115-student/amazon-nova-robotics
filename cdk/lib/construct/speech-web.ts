import { Construct } from "constructs";

import * as assets from "aws-cdk-lib/aws-ecr-assets";
import * as apprunner from "@aws-cdk/aws-apprunner-alpha";
import * as path from "path";
import * as iam from "aws-cdk-lib/aws-iam";
import { DatabaseConstruct } from "./datebase";
import { UserPool, UserPoolClient } from "aws-cdk-lib/aws-cognito";
import { Stack } from "aws-cdk-lib";
import { LambdaMcpServerConstruct } from "./mcp-server";

export interface SpeechControlWebConstructProps {
  readonly database: DatabaseConstruct;
  readonly mcpServerConstruct: LambdaMcpServerConstruct;
  readonly userPool: UserPool;
  readonly userPoolClient: UserPoolClient;
}

export class SpeechControlWebConstruct extends Construct {
  public readonly serviceUrl: string;

  constructor(
    scope: Construct,
    id: string,
    props: SpeechControlWebConstructProps
  ) {
    super(scope, id);

    const imageAsset = new assets.DockerImageAsset(this, "ImageAssets", {
      directory: path.join(__dirname, "../../../speech_control"),
    });

    const autoScalingConfiguration = new apprunner.AutoScalingConfiguration(
      this,
      "AutoScalingConfiguration",
      {
        autoScalingConfigurationName: "RobotWebAutoScalingConfiguration",
        maxConcurrency: 100,
        maxSize: 3,
        minSize: 1,
      }
    );

    const observabilityConfiguration = new apprunner.ObservabilityConfiguration(
      this,
      "ObservabilityConfiguration",
      {
        observabilityConfigurationName: "RobotWeb",
        traceConfigurationVendor: apprunner.TraceConfigurationVendor.AWSXRAY,
      }
    );
    // To create a Service from local docker image asset directory built and pushed to Amazon ECR
    // https://docs.aws.amazon.com/cdk/api/v2/docs/aws-apprunner-alpha-readme.html#ecr
    const service = new apprunner.Service(this, "AppRunnerService", {
      source: apprunner.Source.fromAsset({
        imageConfiguration: {
          port: 3000,
          environmentVariables: {
            IsInCloud: "yes",
            AWS_BEDROCK_REGION: "us-east-1",
            RobotTable: props.database.robotTable.tableName,
            McpServerUrl: props.mcpServerConstruct.functionUrl.url,
            CognitoUserPoolId: props.userPool.userPoolId,
            CognitoUserPoolClientId: props.userPoolClient.userPoolClientId,
            CognitoRegion: Stack.of(this).region,
          },
        },
        asset: imageAsset,
      }),
      cpu: apprunner.Cpu.QUARTER_VCPU,
      memory: apprunner.Memory.HALF_GB,
      autoDeploymentsEnabled: true,
      observabilityConfiguration,
      autoScalingConfiguration,
    });
    props.database.robotTable.grantFullAccess(service);

    service.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ],
        resources: ["*"],
      })
    );

    // Grant permission to invoke the MCP server Lambda function
    props.mcpServerConstruct.mcpFunction.grantInvoke(service);

    this.serviceUrl = service.serviceUrl;
  }
}
