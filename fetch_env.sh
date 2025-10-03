#!/bin/bash
# fetch_env.sh - Fetch environment variables from AWS SSM Parameter Store
# This script runs on the EC2 instance to populate .env file

set -euo pipefail

# Configuration
SSM_PREFIX="/cinereads/prod"
ENV_FILE=".env"

echo "Fetching environment variables from SSM Parameter Store..."

# Get all parameters under the prefix
# This will get parameters like:
# /cinereads/prod/OPENAI_API_KEY
# /cinereads/prod/HARDCOVER_API_KEY
# etc.

# Clear existing env file if it exists
> "$ENV_FILE"

# Get parameters and write to .env file
if command -v aws &> /dev/null; then
    echo "Using AWS CLI to fetch parameters..."

    # Get all parameters under the prefix
    PARAMETERS=$(aws ssm get-parameters-by-path \
        --path "$SSM_PREFIX" \
        --recursive \
        --with-decryption \
        --query 'Parameters[*].[Name,Value]' \
        --output text)

    # Convert SSM parameter names to env var names and write to .env
    echo "$PARAMETERS" | while read -r param_name param_value; do
        # Skip empty rows that can produce malformed entries like '='
        if [[ -z "${param_name}" || -z "${param_value}" ]]; then
            continue
        fi

        # Extract the parameter name (remove prefix) and trim possible carriage returns
        env_name=$(basename "$param_name")
        param_value=${param_value%$'\r'}

        # Only write well-formed KEY=VALUE pairs
        if [[ -n "${env_name}" ]]; then
            echo "${env_name}=${param_value}" >> "$ENV_FILE"
        fi
    done

    echo "Environment variables written to $ENV_FILE"
else
    echo "AWS CLI not found. Please install AWS CLI or ensure it's available."
    exit 1
fi

# Verify the env file was created and has content
if [ -s "$ENV_FILE" ]; then
    echo "✅ Successfully created $ENV_FILE with $(wc -l < "$ENV_FILE") variables"
else
    echo "❌ Failed to create $ENV_FILE or file is empty"
    exit 1
fi