import { Construct } from "constructs";

import * as assets from "aws-cdk-lib/aws-ecr-assets";
import * as apprunner from "@aws-cdk/aws-apprunner-alpha";
import * as path from "path";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as cdk from "aws-cdk-lib";
import { RemovalPolicy, Stack } from "aws-cdk-lib";
import { PolicyStatement, AnyPrincipal } from "aws-cdk-lib/aws-iam";

export interface RobotSimulatorConstructProps {}

export class RobotSimulatorConstruct extends Construct {
  public readonly serviceUrl: string;
  public readonly songWebsiteBucket: s3.Bucket;

  constructor(
    scope: Construct,
    id: string,
    props: RobotSimulatorConstructProps
  ) {
    super(scope, id);

    const imageAsset = new assets.DockerImageAsset(this, "ImageAssets", {
      directory: path.join(__dirname, "../../../humanoid-robot-simulator"),
    });

    const websiteBucket = new s3.Bucket(this, "RobotSimulatorWebsiteBucket", {
      websiteIndexDocument: "index.html",
      removalPolicy: RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      publicReadAccess: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ACLS_ONLY,
      cors: [
        {
          allowedHeaders: ["*"],
          allowedMethods: [s3.HttpMethods.GET, s3.HttpMethods.HEAD],
          allowedOrigins: ["*"],
          exposedHeaders: ["Date", "ETag", "x-amz-request-id"],
          maxAge: 3000,
        },
      ],
    });

    websiteBucket.addToResourcePolicy(
      new PolicyStatement({
        actions: ["s3:GetObject"],
        resources: [websiteBucket.arnForObjects("*")],
        principals: [new AnyPrincipal()],
      })
    );

    const autoScalingConfiguration = new apprunner.AutoScalingConfiguration(
      this,
      "AutoScalingConfiguration",
      {
        autoScalingConfigurationName: "RobotSimAutoScalingConfiguration",
        maxConcurrency: 100,
        maxSize: 3,
        minSize: 1,
      }
    );

    const observabilityConfiguration = new apprunner.ObservabilityConfiguration(
      this,
      "ObservabilityConfiguration",
      {
        observabilityConfigurationName: "HumanoidRobotSimulator",
        traceConfigurationVendor: apprunner.TraceConfigurationVendor.AWSXRAY,
      }
    );

    const service = new apprunner.Service(this, "AppRunnerService", {
      source: apprunner.Source.fromAsset({
        imageConfiguration: {
          port: 5000,
          environmentVariables: {
            IsInCloud: "yes",
            AWS_BEDROCK_REGION: "us-east-1",
            LOG_LEVEL: "INFO",
            DEBUG: "false",
            VIDEO_BUCKET_URL: `https://${websiteBucket.bucketName}.s3.${Stack.of(this).region}.amazonaws.com/`,
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

    this.songWebsiteBucket = websiteBucket;

    this.serviceUrl = service.serviceUrl;

    // Grant permission to read SSM parameters for service discovery
    service.addToRolePolicy(
      new cdk.aws_iam.PolicyStatement({
        actions: ["ssm:GetParameter"],
        resources: [
          `arn:aws:ssm:${Stack.of(this).region}:${Stack.of(this).account}:parameter/robotics/*`,
        ],
      })
    );
  }
}

