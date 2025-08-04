
cd cdk
aws sts get-caller-identity | jq -r .UserId | xargs -I {} cdk deploy --require-approval never --outputs-file output.json --parameters AwsUserId={}