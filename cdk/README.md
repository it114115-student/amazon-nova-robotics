# Welcome to your CDK TypeScript project

This is a blank project for CDK development with TypeScript.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

## Useful commands

* `npm run build`   compile typescript to js
* `npm run watch`   watch for changes and compile
* `npm run test`    perform the jest unit tests
* `npx cdk deploy`  deploy this stack to your default AWS account/region
* `npx cdk diff`    compare deployed stack with current state
* `npx cdk synth`   emits the synthesized CloudFormation template

## OpenClaw MCP callers

The MCP Lambda URL is granted to the current AWS account by default. That makes both OpenClaw `dev` and `prod` execution roles work in the same account, while the actual caller is still constrained by the identity-based policy attached on the OpenClaw side.

You can override the allowed caller accounts with CDK context:

- `openclawCallerAccountIds`: comma-separated string or array of AWS account IDs that should be allowed to invoke the MCP Lambda URL
