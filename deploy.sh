cd cdk
cdk deploy --require-approval never --outputs-file output.json --context AwsUserId=$(aws sts get-caller-identity | jq -r .UserId)
jq -S . output.json > output.sorted.json && mv output.sorted.json output.json
BUCKET=$(jq -r '.[].RobotDataBucketName' output.json)
aws s3 sync s3://"$BUCKET"/iot-certificates/ ../robot_client/certificates