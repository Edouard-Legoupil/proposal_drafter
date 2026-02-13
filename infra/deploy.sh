#!/bin/bash
set -euo pipefail

# Configuration
APP_NAME="${1:-proposalgen-app}"
RESOURCE_GROUP="${2:-proposalgen-rg}"

echo "============================================================"
echo "📦 Packaging Proposal Generator for App Service"
echo "============================================================"

# 1. Build Frontend
echo "🏗️ Building Frontend..."
cd frontend
npm install
npm run build
cd ..

# 2. Prepare deployment directory
echo "📂 Preparing deployment package..."
rm -rf deploy_pkg
mkdir -p deploy_pkg

# Copy backend
cp -r backend deploy_pkg/
# Copy frontend dist (keeping the structure app.py expects: ../frontend/dist)
mkdir -p deploy_pkg/frontend
cp -r frontend/dist deploy_pkg/frontend/

# Copy infra (for startup.sh)
cp -r infra deploy_pkg/

# Copy requirements.txt to root for Azure detection
cp backend/requirements.txt deploy_pkg/

# 3. Create Zip
echo "🤐 Zipping package..."
cd deploy_pkg
zip -r ../deploy.zip .
cd ..

echo "✅ Package ready: deploy.zip"

# 4. Deploy
echo "🚀 Deploying to Azure App Service: ${APP_NAME}..."
az webapp deployment source config-zip \
    --resource-group "${RESOURCE_GROUP}" \
    --name "${APP_NAME}" \
    --src deploy.zip

echo "============================================================"
echo "🎉 Deployment Complete!"
echo "============================================================"
