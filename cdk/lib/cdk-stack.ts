import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import { RoboticConstruct } from "./construct/robot-iot";
import { SpeechControlWebConstruct } from "./construct/speech-web";
import { TextControlWebConstruct } from "./construct/text-web";
import { RobotSsmConstruct } from "./construct/robot-ssm";
import { SsmUserConstruct } from "./construct/ssm-user";
import { DatabaseConstruct } from "./construct/datebase";
import { LambdaMcpServerConstruct } from "./construct/mcp-server";
import { RobotSimulatorConstruct } from "./construct/robot-simulator";
import { Authenticator } from "./construct/authenticator";

export class AmazonNovaRoboticCdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const authenticator = new Authenticator(this, "Authenticator");

    const mcpServerConstruct = new LambdaMcpServerConstruct(
      this,
      "LambdaMcpServerConstruct"
    );

    const numberOfRobots = 9; // Number of robots
    const numberOfDrones = 1; // Number of drones
    const numberOfDogs = 3; // Number of dogs

    const thingNames = Array.from(
      { length: numberOfRobots },
      (_, i) => `robot_${i + 1}`
    );
    const droneNames = Array.from(
      { length: numberOfDrones },
      (_, i) => `drone_${i + 1}`
    );
    const dogNames = Array.from(
      { length: numberOfDogs },
      (_, i) => `dog_${i + 1}`
    );
    thingNames.push(...droneNames);
    thingNames.push(...dogNames);
    const roboticConstruct = new RoboticConstruct(this, "RoboticConstruct", {
      thingNames: thingNames,
    });

    const databaseConstruct = new DatabaseConstruct(this, "DatabaseConstruct");

    const webConstruct = new SpeechControlWebConstruct(this, "WebConstruct", {
      database: databaseConstruct,
      mcpServerConstruct: mcpServerConstruct,
      userPool: authenticator.userPool,
      userPoolClient: authenticator.userPoolClient,
    });

    const humanoidRobotSimulatorConstruct = new RobotSimulatorConstruct(
      this,
      "RobotSimulatorConstruct",
      {}
    );

    const textControlWebConstruct = new TextControlWebConstruct(
      this,
      "TextControlWebConstruct",
      {
        database: databaseConstruct,
        mcpServerConstruct: mcpServerConstruct,
        userPool: authenticator.userPool,
        userPoolClient: authenticator.userPoolClient,
      }
    );

    // Create shared SSM user construct
    const ssmUserConstruct = new SsmUserConstruct(this, "SsmUserConstruct", {
      userName: "AmazonNovaRoboticsSsmUser",
    });

    const ssmRobotNames = Array.from(
      { length: numberOfRobots },
      (_, i) => `RaspberryPiRobot${i + 1}`
    );
    new RobotSsmConstruct(this, "RobotSsmConstruct", {
      prefix: "humanoid",
      thingNames: ssmRobotNames,
      ssmUserConstruct: ssmUserConstruct,
    });

    const ssmDogNames = Array.from(
      { length: numberOfDogs },
      (_, i) => `RaspberryPiDog${i + 1}`
    );
    new RobotSsmConstruct(this, "RobotDogSsmConstruct", {
      prefix: "dog",
      thingNames: ssmDogNames,
      ssmUserConstruct: ssmUserConstruct,
    });

    new cdk.CfnOutput(this, "speechUrl", {
      description: "The URL of the Speech Control Web",
      value: "https://" + webConstruct.serviceUrl,
    });

    new cdk.CfnOutput(this, "textUrl", {
      description: "The URL of the Text Control Web",
      value: textControlWebConstruct.serviceUrl,
    });

    new cdk.CfnOutput(this, "humanoidRobotSimulatorUrl", {
      description: "The URL of the Humanoid Robot Simulator",
      value: "https://" + humanoidRobotSimulatorConstruct.serviceUrl,
    });

    new cdk.CfnOutput(this, "SongWebsiteBucket", {
      value: humanoidRobotSimulatorConstruct.songWebsiteBucket.bucketName,
      description: "The name of the S3 bucket for the Humanoid Robot Simulator",
    });
    new cdk.CfnOutput(this, "SongWebsiteBucketUrl", {
      value: humanoidRobotSimulatorConstruct.songWebsiteBucket.bucketWebsiteUrl,
      description:
        "The website URL of the S3 bucket for the Humanoid Robot Simulator",
    });

    new cdk.CfnOutput(this, "RobotDataBucketName", {
      value: roboticConstruct.bucket.bucketName,
      description: "The name of the S3 bucket for storing robot data",
    });

    new cdk.CfnOutput(this, "McpServerUrl", {
      value: mcpServerConstruct.functionUrl.url,
      description: "The URL of the MCP Server Lambda Function",
    });

    new cdk.CfnOutput(this, "CognitoUserPoolId", {
      value: authenticator.userPool.userPoolId,
      description: "Cognito User Pool ID for authentication",
    });

    new cdk.CfnOutput(this, "CognitoUserPoolClientId", {
      value: authenticator.userPoolClient.userPoolClientId,
      description: "Cognito User Pool Client ID for authentication",
    });

    new cdk.CfnOutput(this, "CognitoRegion", {
      value: this.region,
      description: "AWS region for Cognito User Pool",
    });

    new cdk.CfnOutput(this, "CognitoUserPoolDomain", {
      value: `https://cognito-idp.${this.region}.amazonaws.com/${authenticator.userPool.userPoolId}`,
      description: "Cognito User Pool domain for JWKS",
    });
  }
}
