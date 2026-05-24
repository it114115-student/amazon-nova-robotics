# Fix Docker credential helper issue that occurs in dev containers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "${SCRIPT_DIR}/fix_docker_credentials.sh"

# Ensure arm64 build emulation is registered for Bedrock AgentCore container builds
if ! docker run --rm --platform linux/arm64 alpine arch 2>/dev/null | grep -q "aarch64"; then
    echo "🚀 Installing arm64 build emulation..."
    docker run --privileged --rm tonistiigi/binfmt --install arm64
else
    echo "✅ arm64 build emulation is active."
fi

cd cdk
npx cdk deploy --require-approval never --outputs-file output.json --context AwsUserId=$(aws sts get-caller-identity | jq -r .UserId)
jq -S . output.json > output.sorted.json && mv output.sorted.json output.json
BUCKET=$(jq -r '.[].RobotDataBucketName' output.json)
aws s3 sync s3://"$BUCKET"/iot-certificates/ ../robot_client/certificates

WEBSITE_BUCKET=$(jq -r '.[].ServerlessWebsiteBucket' output.json)
aws s3 sync ../humanoid-robot-simulator-serverless/frontend/video s3://"$WEBSITE_BUCKET"/video

DOMAIN_WEBSITE_BUCKET=$(jq -r '.[].DomainExpansionWebsiteBucket' output.json)
aws s3 sync ../domain-expansion-ar-game/static/video s3://"$DOMAIN_WEBSITE_BUCKET"/static/video