# Amazon Nova Robotics

Robotic with AWS IoT, AWS Bedrock, and Amazon Nova.

### Tech Blog

[Voice-Controlled Humanoid Robots Using Amazon Nova Sonic and AWS IoT](https://community.aws/content/2vqYxQLMJ8dYsL9kJnfPj0wIps3/voice-controlled-humanoid-robots-using-amazon-nova-sonic-and-aws-iot)

## Update CDK and all packages for CodeSpaces

Upgrade node.js to version 22

```
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash
```

Close the terminal.

```
nvm use 22
nvm alias default 22
```

```
cd cdk
pip install --upgrade awscli
npm uninstall -g cdk
npm install -g cdk
npm i -g npm-check-updates && ncu -u && npm i
```

Configure AWS CLI

```
aws configure
```

Default region name [None]: us-east-1

Default output format [None]: json

# Server side Deployment

## Use CDK bootstrap

```
cd cdk
cdk bootstrap
```

## Deploy Stacks

```
cdk deploy --require-approval never --outputs-file output.json
```

## Destory Stacks

```
cdk destroy --require-approval never
```

## Local Stack Output as environment variable

For local developement, you need to set them.

```
sudo apt update && sudo apt install -y jq
source /workspaces/amazon-nova-robotics/load_cdkstack_env.sh
```

## Download AWS IoT Certifications

```
source load_cdkstack_env.sh
aws s3 sync s3://$RobotDataBucketName robot_client/certificates/
```

# Robot Deployment

1. Generate the deployment package:

   ```bash
   ./create_deploy_package.sh
   ```

2. Transfer the `deploy_package.zip` file to the robot.

3. Extract the contents of the package:

   ```bash
   unzip deploy_package.zip
   ```

4. Update the `settings.yaml` file to specify the `robot_name`. By default, up to 5 robots can be configured.

5. Set up a virtual environment:

   ```bash
   ./create_virtual_env.sh
   ```

6. Activate the virtual environment and start the `pubsub.py` script:

   ```bash
   source venv/bin/activate
   python pubsub.py
   ```

# TODO

1. Fine grant the AWS IOT device permission.
