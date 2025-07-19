import { Construct } from "constructs";

import * as assets from "aws-cdk-lib/aws-ecr-assets";
import * as apprunner from "@aws-cdk/aws-apprunner-alpha";
import * as path from "path";

export interface RobotSimulatorConstructProps {}

export class RobotSimulatorConstruct extends Construct {
  public readonly serviceUrl: string;

  constructor(
    scope: Construct,
    id: string,
    props: RobotSimulatorConstructProps
  ) {
    super(scope, id);

    const imageAsset = new assets.DockerImageAsset(this, "ImageAssets", {
      directory: path.join(__dirname, "../../../humanoid-robot-simulator"),
    });

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

    // To create a Service from local docker image asset directory built and pushed to Amazon ECR
    // https://docs.aws.amazon.com/cdk/api/v2/docs/aws-apprunner-alpha-readme.html#ecr
    const service = new apprunner.Service(this, "AppRunnerService", {
      source: apprunner.Source.fromAsset({
        imageConfiguration: {
          port: 5000,
          environmentVariables: {
            IsInCloud: "yes",
            AWS_BEDROCK_REGION: "us-east-1",
            LOG_LEVEL: "INFO",
            DEBUG: "false",
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

    this.serviceUrl = service.serviceUrl;
  }
}
