import { RestApi, LambdaIntegration } from "aws-cdk-lib/aws-apigateway";
import { Duration, IgnoreMode } from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import { PythonFunction } from "@aws-cdk/aws-lambda-python-alpha";
import { Construct } from "constructs";
import path = require("path");
import * as iam from "aws-cdk-lib/aws-iam";
import { DatabaseConstruct } from "./datebase";

export interface TextControlWebConstructProps {
  readonly database: DatabaseConstruct;
  readonly mcpServerUrl: string;
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
    });

    const flaskLambda = new PythonFunction(this, "TextControlLambda", {
      entry: path.join(__dirname, "../../../text_control"),
      runtime: lambda.Runtime.PYTHON_3_13,
      index: "app.py",
      handler: "handler",
      timeout: Duration.seconds(30),
      environment: {
        AWS_BEDROCK_REGION: "us-east-1",
        RobotTable: props.database.robotTable.tableName,
        McpServerUrl: props.mcpServerUrl,
      },
      bundling: {
        assetExcludes: [
          ".venv",
          "create_virtual_env.sh",
          ".dockerignore",
          "Dockerfile",
        ],
      },
    });

    props.database.robotTable.grantFullAccess(flaskLambda);

    flaskLambda.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["iot:Publish"],
        resources: ["arn:aws:iot:*:*:topic/robot_*/topic"],
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

    const rootResource = restApi.root;

    rootResource.addProxy({
      defaultIntegration: new LambdaIntegration(flaskLambda),
      anyMethod: true,
    });

    this.serviceUrl = restApi.url + "index";
  }
}
