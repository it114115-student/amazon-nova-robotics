#!/bin/bash
# Load CdkStack dict from output.json into environment variables

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
json_file="$script_dir/cdk/output.json"

if ! command -v jq &> /dev/null; then
  echo "Error: jq is not installed. Please install jq to use this script."
  exit 1
fi

export_cmds=$(jq -r '.CdkStack | to_entries[] | "export " + .key + "=\"" + (.value|tostring) + "\"" ' "$json_file")

eval "$export_cmds"
echo "CdkStack environment variables loaded."
