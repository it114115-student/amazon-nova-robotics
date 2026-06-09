import { Construct } from "constructs";
import * as agentcore from "@aws-cdk/aws-bedrock-agentcore-alpha";
import * as iam from "aws-cdk-lib/aws-iam";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as s3deploy from "aws-cdk-lib/aws-s3-deployment";
import * as cloudfront from "aws-cdk-lib/aws-cloudfront";
import * as origins from "aws-cdk-lib/aws-cloudfront-origins";
import * as path from "path";
import { Platform } from "aws-cdk-lib/aws-ecr-assets";
import { DatabaseConstruct } from "./datebase";
import { LambdaMcpServerConstruct } from "./mcp-server";
import { Stack, RemovalPolicy } from "aws-cdk-lib";

export interface SpeechControlAgentcoreConstructProps {
  readonly database: DatabaseConstruct;
  readonly mcpServerConstruct: LambdaMcpServerConstruct;
  readonly userPoolId: string;
  readonly userPoolClientId: string;
  readonly identityPoolId: string;
}

export class SpeechControlAgentcoreConstruct extends Construct {
  public readonly runtimeArn: string;
  public readonly serviceUrl: string;

  constructor(
    scope: Construct,
    id: string,
    props: SpeechControlAgentcoreConstructProps
  ) {
    super(scope, id);

    // 1. Package container directly onto AWS Bedrock AgentCore Runtime
    const agentRuntimeArtifact = agentcore.AgentRuntimeArtifact.fromAsset(
      path.join(__dirname, "../../../speech_control_agentcore"),
      {
        platform: Platform.LINUX_ARM64,
        exclude: [".venv", "__pycache__", "tests"], // Prevent virtualenv and cache files from inflating container size, keeping the essential public directory
      }
    );

    // 2. Create the AgentCore Runtime with IAM authentication (SigV4)
    const runtime = new agentcore.Runtime(this, "Runtime", {
      runtimeName: "robot_voice_agentcore",
      agentRuntimeArtifact: agentRuntimeArtifact,
      authorizerConfiguration: agentcore.RuntimeAuthorizerConfiguration.usingIAM(),
      environmentVariables: {
        IsInCloud: "yes",
        AWS_BEDROCK_REGION: "us-east-1",
        RobotTable: props.database.robotTable.tableName,
        McpServerUrl: props.mcpServerConstruct.functionUrl.url,
      },
    });

    this.runtimeArn = runtime.agentRuntimeArn;

    // 3. Grant full access to DynamoDB tables
    props.database.robotTable.grantFullAccess(runtime.role);

    // 4. Grant access to invoke Bedrock models (Nova 2 Sonic)
    runtime.role.addToPrincipalPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ],
        resources: [
          "arn:aws:bedrock:*::foundation-model/amazon.nova-sonic-v1:0",
          "arn:aws:bedrock:*::foundation-model/amazon.nova-2-sonic-v1:0",
        ],
      })
    );

    // 5. Grant Lambda invocation for MCP backend routing
    runtime.role.addToPrincipalPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["lambda:InvokeFunction", "lambda:InvokeFunctionUrl"],
        resources: [props.mcpServerConstruct.mcpFunction.functionArn],
      })
    );

    // 6. Serverless Frontend S3 Website Bucket
    const websiteBucket = new s3.Bucket(this, "SpeechAgentcoreWebsiteBucket", {
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
      new iam.PolicyStatement({
        actions: ["s3:GetObject"],
        resources: [websiteBucket.arnForObjects("*")],
        principals: [new iam.AnyPrincipal()],
      })
    );

    // 7. Cost-Efficient CloudFront Distribution (Price Class 100)
    const oai = new cloudfront.OriginAccessIdentity(this, "SpeechOAI");
    websiteBucket.grantRead(oai);

    const distribution = new cloudfront.Distribution(this, "SpeechDistribution", {
      defaultRootObject: "index.html",
      priceClass: cloudfront.PriceClass.PRICE_CLASS_100,
      defaultBehavior: {
        origin: origins.S3BucketOrigin.withOriginAccessIdentity(websiteBucket, { originAccessIdentity: oai }),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
        cachedMethods: cloudfront.CachedMethods.CACHE_GET_HEAD,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
      },
    });

    this.serviceUrl = distribution.distributionDomainName;

    // 8. Deploy static web files and dynamic config.json to website bucket
    new s3deploy.BucketDeployment(this, "DeploySpeechWebsiteAndConfig", {
      sources: [
        s3deploy.Source.asset(path.join(__dirname, "../../../speech_control_agentcore/frontend")),
        s3deploy.Source.jsonData("config.json", {
          region: Stack.of(this).region,
          userPoolId: props.userPoolId,
          clientId: props.userPoolClientId,
          identityPoolId: props.identityPoolId,
          runtimeArn: runtime.agentRuntimeArn,
        }),
      ],
      destinationBucket: websiteBucket,
      distribution,
      distributionPaths: ["/*"],
    });
  }
}
