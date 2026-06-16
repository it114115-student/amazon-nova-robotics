#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Resolve directories relative to the script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIAGRAMS_DIR="${SCRIPT_DIR}/diagrams"
IMG_DIR="${SCRIPT_DIR}/img"
PUPPETEER_CONFIG="${DIAGRAMS_DIR}/puppeteer-config.json"

echo "========================================="
echo "Regenerating System Design Diagrams"
echo "========================================="
echo "Script directory: ${SCRIPT_DIR}"
echo "Diagrams source:  ${DIAGRAMS_DIR}"
echo "Output images:    ${IMG_DIR}"
echo "Puppeteer config: ${PUPPETEER_CONFIG}"
echo "========================================="

# Ensure output directory exists
mkdir -p "${IMG_DIR}"

# List of diagram files to process (without extension)
DIAGRAMS=(
  "overall_architecture_topology"
  "authenticator_resources"
  "authenticator_flow"
  "database_grants"
  "mcp_server_interactions"
  "robot_tool_gateway_sandbox"
  "robot_tool_gateway_flow"
  "iot_things_batch_vs_legacy"
  "iot_things_lifecycle"
  "robot_ssm_channel"
  "jjk_domain_expansion_architecture"
  "jjk_domain_expansion_flow"
  "jjk_domain_expansion_portrait_fusion"
)

# Run compilation for each diagram
for diagram in "${DIAGRAMS[@]}"; do
  input_file="${DIAGRAMS_DIR}/${diagram}.mmd"
  output_file="${IMG_DIR}/${diagram}.png"
  
  if [ ! -f "${input_file}" ]; then
    echo "Warning: Source file ${input_file} not found. Skipping."
    continue
  fi
  
  echo "Processing [${diagram}.mmd] -> [${diagram}.png]..."
  
  # Run local mermaid-cli via npx with disabled sandbox config
  npx -y @mermaid-js/mermaid-cli -p "${PUPPETEER_CONFIG}" -i "${input_file}" -o "${output_file}" -s 3 -b transparent
done

echo "========================================="
echo "Success! All diagrams successfully compiled."
echo "========================================="
