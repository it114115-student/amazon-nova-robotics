#!/bin/bash
# fix_docker_credentials.sh
# Fixes the Docker credential helper error:
#   "Docker credential helper 'docker-credential-secretservice' not found: write EPIPE"
#
# This error occurs in dev container environments where the credential store
# (e.g. secretservice or pass) is not available. The fix clears the credsStore
# so Docker stores credentials directly in ~/.docker/config.json.

set -e

DOCKER_CONFIG="${HOME}/.docker/config.json"

if [ ! -f "$DOCKER_CONFIG" ]; then
    echo "Docker config not found at $DOCKER_CONFIG, creating directory..."
    mkdir -p "${HOME}/.docker"
    echo '{"auths": {}, "credsStore": ""}' > "$DOCKER_CONFIG"
fi

echo "Current credsStore: $(python3 -c "import json; d=json.load(open('$DOCKER_CONFIG')); print(repr(d.get('credsStore','(not set)')))")"

python3 - <<'PYEOF'
import json, os

config_path = os.path.expanduser("~/.docker/config.json")
with open(config_path) as f:
    config = json.load(f)

creds_store = config.get("credsStore", "")
if creds_store:
    print(f"Removing credsStore: '{creds_store}'")
    config["credsStore"] = ""
    # Clear any stored auth tokens that relied on the old credential store
    # (they will be refreshed on next login)
    if "auths" in config:
        for registry in config["auths"]:
            config["auths"][registry] = {}
    with open(config_path, "w") as f:
        json.dump(config, f, indent=8)
    print("Docker config updated. Credentials will be stored directly in config.json.")
else:
    print("credsStore is already empty — no change needed.")
PYEOF

# Re-authenticate with ECR if AWS CLI is available and region/account are set
if command -v aws &>/dev/null; then
    AWS_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
    AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || true)
    if [ -n "$AWS_ACCOUNT" ]; then
        ECR_REGISTRY="${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        echo "Logging in to ECR: $ECR_REGISTRY"
        aws ecr get-login-password --region "$AWS_REGION" \
            | docker login --username AWS --password-stdin "$ECR_REGISTRY"
        echo "ECR login successful."
    else
        echo "Could not determine AWS account ID — skipping ECR login."
    fi
else
    echo "AWS CLI not found — skipping ECR login."
fi
