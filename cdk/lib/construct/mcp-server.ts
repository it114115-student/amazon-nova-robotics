import {
  Runtime,
  FunctionUrl,
  FunctionUrlAuthType,
  HttpMethod,
} from "aws-cdk-lib/aws-lambda";
import { PythonFunction } from "@aws-cdk/aws-lambda-python-alpha";
import { Construct } from "constructs";
import { Duration, Stack, RemovalPolicy, DockerImage } from "aws-cdk-lib";
import * as iam from "aws-cdk-lib/aws-iam";
import * as s3 from "aws-cdk-lib/aws-s3";
import { DatabaseConstruct } from "./datebase";
import { AttributeType, Billing, TableV2 } from "aws-cdk-lib/aws-dynamodb";
import * as cdk from "aws-cdk-lib";

import path = require("path");

export interface LambdaMcpServerConstructProps {
  readonly database: DatabaseConstruct;
  readonly simulatorEndpoint?: string;
}

export class LambdaMcpServerConstruct extends Construct {
  public readonly mcpFunction: PythonFunction;
  public readonly functionUrl: FunctionUrl;
  public readonly imageBucket: s3.Bucket;
  public readonly speechTable: TableV2;
  private permissionCounter = 0;

  constructor(scope: Construct, id: string, props: LambdaMcpServerConstructProps) {
    super(scope, id);

    // DynamoDB table for xiaoice speech messages
    this.speechTable = new TableV2(this, "SpeechTable", {
      partitionKey: {
        name: "id",
        type: AttributeType.STRING,
      },
      billing: Billing.onDemand(),
      removalPolicy: RemovalPolicy.DESTROY,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: false,
      },
    });

    new cdk.CfnOutput(this, "SpeechTableName", {
      key: "SpeechTable",
      value: this.speechTable.tableName,
      description: "The name of the DynamoDB table for xiaoice speech messages",
    });

    // S3 bucket for robot captured images
    this.imageBucket = new s3.Bucket(this, "RobotImageBucket", {
      versioned: false,
      removalPolicy: RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      cors: [
        {
          allowedMethods: [s3.HttpMethods.PUT, s3.HttpMethods.GET],
          allowedOrigins: ["*"],
          allowedHeaders: ["*"],
        },
      ],
    });

    this.mcpFunction = new PythonFunction(this, "McpFunction", {
      entry: path.join(__dirname, "../../../mcp_server"), // required
      runtime: Runtime.PYTHON_3_13, // required
      timeout: Duration.seconds(30), // optional, defaults to 3 seconds
      bundling: {
        // translates to `rsync --exclude='.venv'`
        assetExcludes: [".venv", "create_virtual_env.sh"],
        image: DockerImage.fromRegistry('public.ecr.aws/sam/build-python3.13'),
      },
      environment: {
        IMAGE_BUCKET_NAME: this.imageBucket.bucketName,
        SpeechTable: this.speechTable.tableName,
        RobotTable: props.database.robotTable.tableName,
        SIMULATOR_ENDPOINT: props.simulatorEndpoint || "",
      },
    });

    // Grant the Lambda function read/write access to the image bucket
    this.imageBucket.grantReadWrite(this.mcpFunction);

    // Grant the Lambda function read/write access to the speech table
    this.speechTable.grantReadWriteData(this.mcpFunction);

    // Grant the Lambda function read access to the robot table (for presenter context)
    props.database.robotTable.grantReadData(this.mcpFunction);

    this.mcpFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["iot:Publish", "iot-data:Publish"],
        resources: [
          "arn:aws:iot:*:*:topic/robot_*/topic",
          "arn:aws:iot:*:*:topic/drone_*/topic",
          "arn:aws:iot:*:*:topic/dog_*/topic",
          "arn:aws:iot:*:*:topic/xiaoice_*/topic",
        ],
      })
    );

    // Grant the Lambda function permission to use Amazon Polly for speech synthesis
    this.mcpFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["polly:SynthesizeSpeech"],
        resources: ["*"],
      })
    );

    // Enable Function URL
    this.functionUrl = this.mcpFunction.addFunctionUrl({
      authType: FunctionUrlAuthType.AWS_IAM,
      cors: {
        allowedOrigins: ["*"],
        allowedMethods: [HttpMethod.ALL],
        allowedHeaders: ["*"],
      },
    });
  }

  /**
   * Grant permission to invoke the MCP server function URL
   * @param principal The AWS principal (role, user, or service) to grant permission to
   */
  public grantInvokeFunctionUrl(principal: iam.IPrincipal): void {
    // Generate unique IDs using a counter
    const functionUrlPermissionId = `InvokeFunctionUrlPermission-${++this
      .permissionCounter}`;
    const invokeFunctionPermissionId = `InvokeFunctionPermission-${this.permissionCounter}`;

    // Add lambda:InvokeFunctionUrl permission (required for function URL access)
    this.mcpFunction.addPermission(functionUrlPermissionId, {
      principal: principal,
      action: "lambda:InvokeFunctionUrl",
      functionUrlAuthType: FunctionUrlAuthType.AWS_IAM,
    });

    // Add lambda:InvokeFunction permission (required as of new authorization model)
    // AWS Lambda now requires both actions for function URL invocations
    this.mcpFunction.addPermission(invokeFunctionPermissionId, {
      principal: principal,
      action: "lambda:InvokeFunction",
    });
  }
}
