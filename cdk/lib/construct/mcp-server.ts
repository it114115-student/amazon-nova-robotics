import {
  Runtime,
  FunctionUrl,
  FunctionUrlAuthType,
  HttpMethod,
} from "aws-cdk-lib/aws-lambda";
import { PythonFunction } from "@aws-cdk/aws-lambda-python-alpha";
import { Construct } from "constructs";
import { Duration, Stack } from "aws-cdk-lib";
import * as iam from "aws-cdk-lib/aws-iam";

import path = require("path");

export class LambdaMcpServerConstruct extends Construct {
  public readonly mcpFunction: PythonFunction;
  public readonly functionUrl: FunctionUrl;
  private permissionCounter = 0;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    this.mcpFunction = new PythonFunction(this, "McpFunction", {
      entry: path.join(__dirname, "../../../mcp_server"), // required
      runtime: Runtime.PYTHON_3_13, // required
      timeout: Duration.seconds(30), // optional, defaults to 3 seconds
      bundling: {
        // translates to `rsync --exclude='.venv'`
        assetExcludes: [".venv", "create_virtual_env.sh"],
      },
    });

    this.mcpFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["iot:Publish", "iot-data:Publish"],
        resources: [
          "arn:aws:iot:*:*:topic/robot_*/topic",
          "arn:aws:iot:*:*:topic/drone_*/topic",
          "arn:aws:iot:*:*:topic/dog_*/topic",
        ],
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
    // Generate a unique ID using a counter
    const permissionId = `InvokeFunctionUrlPermission-${++this
      .permissionCounter}`;

    this.mcpFunction.addPermission(permissionId, {
      principal: principal,
      action: "lambda:InvokeFunctionUrl",
      functionUrlAuthType: FunctionUrlAuthType.AWS_IAM,
    });
  }
}
