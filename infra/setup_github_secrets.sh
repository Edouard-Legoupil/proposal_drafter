#!/bin/bash

# This script sets up the required GitHub secrets for the CI/CD workflows.

# Check if gh is installed
if ! command -v gh &> /dev/null
then
    echo "GitHub CLI (gh) could not be found. Please install it to continue."
    echo "Installation instructions: https://github.com/cli/cli#installation"
    exit 1
fi

# Get the repository name
read -p "Enter the GitHub repository name (e.g., owner/repo): " REPO

# Check if the repository is valid
if ! gh repo view $REPO > /dev/null 2>&1; then
    echo "Error: Repository '$REPO' not found or you don't have access."
    exit 1
fi

echo "Choose the deployment option:"
echo "1) With SSO"
echo "2) No SSO"
read -p "Enter your choice (1 or 2): " DEPLOYMENT_OPTION

# --- Common Secrets ---
echo "--- Enter common secret values ---"
read -p "AZURE_SUBSCRIPTION_ID: " AZURE_SUBSCRIPTION_ID
read -p "AZURE_RG (resource group name): " AZURE_RG
read -p "RESOURCE_PREFIX (e.g., ppg-prod): " RESOURCE_PREFIX
read -p "BACKEND_IMAGE (e.g., backend:latest): " BACKEND_IMAGE
read -p "ENVIRONMENT_SIZE (Testing, Exploratory, Expanded, or Organization-Wide): " ENVIRONMENT_SIZE
read -s -p "SERPER_API_KEY: " SERPER_API_KEY
echo
read -s -p "SECRET_KEY: " SECRET_KEY
echo
read -p "CF_ACCESS_CLIENT_ID: " CF_ACCESS_CLIENT_ID
read -s -p "CF_ACCESS_CLIENT_SECRET: " CF_ACCESS_CLIENT_SECRET
echo

# Set common secrets
echo "Setting common secrets..."
gh secret set AZURE_SUBSCRIPTION_ID --body "$AZURE_SUBSCRIPTION_ID" --repo $REPO
gh secret set AZURE_RG --body "$AZURE_RG" --repo $REPO
gh secret set RESOURCE_PREFIX --body "$RESOURCE_PREFIX" --repo $REPO
gh secret set BACKEND_IMAGE --body "$BACKEND_IMAGE" --repo $REPO
gh secret set ENVIRONMENT_SIZE --body "$ENVIRONMENT_SIZE" --repo $REPO
gh secret set SERPER_API_KEY --body "$SERPER_API_KEY" --repo $REPO
gh secret set SECRET_KEY --body "$SECRET_KEY" --repo $REPO
gh secret set CF_ACCESS_CLIENT_ID --body "$CF_ACCESS_CLIENT_ID" --repo $REPO
gh secret set CF_ACCESS_CLIENT_SECRET --body "$CF_ACCESS_CLIENT_SECRET" --repo $REPO

if [ "$DEPLOYMENT_OPTION" == "1" ]; then
    # --- SSO Secrets ---
    echo "--- Enter SSO secret values ---"
    read -p "AZURE_CLIENT_ID (appId from 'az ad sp create-for-rbac'): " AZURE_CLIENT_ID
    read -p "AZURE_TENANT_ID (tenant from 'az ad sp create-for-rbac'): " AZURE_TENANT_ID
    read -s -p "ENTRA_TENANT_ID: " ENTRA_TENANT_ID
    echo
    read -s -p "ENTRA_CLIENT_ID: " ENTRA_CLIENT_ID
    echo
    read -s -p "ENTRA_CLIENT_SECRET: " ENTRA_CLIENT_SECRET
    echo

    # Set SSO secrets
    echo "Setting SSO secrets..."
    gh secret set AZURE_CLIENT_ID --body "$AZURE_CLIENT_ID" --repo $REPO
    gh secret set AZURE_TENANT_ID --body "$AZURE_TENANT_ID" --repo $REPO
    gh secret set ENTRA_TENANT_ID --body "$ENTRA_TENANT_ID" --repo $REPO
    gh secret set ENTRA_CLIENT_ID --body "$ENTRA_CLIENT_ID" --repo $REPO
    gh secret set ENTRA_CLIENT_SECRET --body "$ENTRA_CLIENT_SECRET" --repo $REPO

elif [ "$DEPLOYMENT_OPTION" == "2" ]; then
    # --- No-SSO Secrets ---
    echo "--- Enter No-SSO secret values ---"
    echo "Paste the JSON output from 'az ad sp create-for-rbac --sdk-auth':"
    read -s AZURE_CREDENTIALS
    echo

    # Set No-SSO secret
    echo "Setting No-SSO secret..."
    gh secret set AZURE_CREDENTIALS --body "$AZURE_CREDENTIALS" --repo $REPO

else
    echo "Invalid option. Exiting."
    exit 1
fi

echo "All secrets have been set successfully for repository: $REPO"
