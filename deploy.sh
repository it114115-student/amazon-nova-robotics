cd cdk
cdk deploy --require-approval never --outputs-file output.json --context AwsUserId=$(aws sts get-caller-identity | jq -r .UserId)
jq -S . output.json > output.sorted.json && mv output.sorted.json output.json