#!/bin/bash

# Proposal Drafter - Secrets Rotation Script
# This script automates the rotation of secrets in Google Cloud Secret Manager
# Usage: ./scripts/secrets-rotation.sh [--dry-run] [--force]

set -euo pipefail

# Configuration
PROJECT_ID="${SECRET_MANAGER_PROJECT_ID:-}"
DRY_RUN=false
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            echo "Unknown argument: $1"
            exit 1
            ;;
    esac
done

# Check if project ID is set
if [[ -z "$PROJECT_ID" ]]; then
    echo "ERROR: SECRET_MANAGER_PROJECT_ID environment variable not set"
    exit 1
fi

# Check if gcloud is installed and authenticated
echo "Checking gcloud authentication..."
if ! gcloud auth list --format="value(account)" | grep -q "@"; then
    echo "ERROR: gcloud not authenticated. Please run 'gcloud auth login'"
    exit 1
fi

# Check if gcloud is configured for the right project
echo "Checking gcloud project configuration..."
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
if [[ "$CURRENT_PROJECT" != "$PROJECT_ID" ]]; then
    echo "Setting gcloud project to $PROJECT_ID..."
    gcloud config set project "$PROJECT_ID"
fi

# Function to generate random secrets
generate_random_secret() {
    local length=${1:-32}
    openssl rand -base64 "$length" | tr -d '/+=' | head -c "$length"
}

# Function to rotate a secret
otate_secret() {
    local secret_name="$1"
    local env_var="$2"
    local length="$3"

    echo "Rotating secret: $secret_name"

    # Generate new secret value
    local new_value=$(generate_random_secret "$length")

    if [[ "$DRY_RUN" == true ]]; then
        echo "  [DRY RUN] Would create new secret version for $secret_name"
        echo "  [DRY RUN] New value length: ${#new_value}"
        return 0
    fi

    # Check if secret exists
    if gcloud secrets describe "$secret_name" --project="$PROJECT_ID" >/dev/null 2>&1; then
        echo "  Secret exists, creating new version..."
    else
        echo "  Secret does not exist, creating new secret..."
        gcloud secrets create "$secret_name" --replication-policy="automatic" --project="$PROJECT_ID"
    fi

    # Add new secret version
    echo "$new_value" | gcloud secrets versions add "$secret_name" --data-file=- --project="$PROJECT_ID"

    # Disable old versions (keep last 2 versions)
    local versions=$(gcloud secrets versions list "$secret_name" --project="$PROJECT_ID" --format="value(name)" | sort -r)
    local version_count=$(echo "$versions" | wc -l)

    if [[ $version_count -gt 2 ]]; then
        echo "  Disabling old versions (keeping last 2)..."
        local versions_to_disable=$(echo "$versions" | tail -n +3)
        for old_version in $versions_to_disable; do
            gcloud secrets versions disable "$old_version" --project="$PROJECT_ID"
        done
    fi

    echo "  ✓ Successfully rotated $secret_name"

    # If this is a local development environment, update the .env file
    if [[ -f ".env" && "$FORCE" == true ]]; then
        echo "  Updating .env file..."
        sed -i "/^${env_var}=/c${env_var}=\"${new_value}\"" .env
    fi
}

# Main rotation function
rotate_all_secrets() {
    echo "Starting secrets rotation for project: $PROJECT_ID"
    echo "Dry run: $DRY_RUN"
    echo "Force update .env: $FORCE"
    echo ""

    # List of secrets to rotate with their environment variable names and lengths
    declare -a secrets=(
        "secret_key:SECRET_KEY:32"
        "db_password:DB_PASSWORD:24"
        "entra_client_secret:ENTRA_CLIENT_SECRET:32"
        "azure_openai_api_key:AZURE_OPENAI_API_KEY:32"
        "gemini_api_key:GEMINI_API_KEY:32"
        "sharepoint_client_secret:SHAREPOINT_CLIENT_SECRET:32"
    )

    # Rotate each secret
    for secret_info in "${secrets[@]}"; do
        IFS=':' read -r secret_name env_var length <<< "$secret_info"
        rotate_secret "$secret_name" "$env_var" "$length"
        echo ""
    done

    echo "Secrets rotation completed!"

    if [[ "$DRY_RUN" == false ]]; then
        echo ""
        echo "IMPORTANT: Update your application configurations to use the new secret values."
        echo "If you're using environment variables, you may need to restart your services."
    fi
}

# Run the rotation
rotate_all_secrets
