#!/bin/bash
set -e

# Configuration
BACKEND_DIR="./backend"
FRONTEND_DIR="./frontend-dist"
FRONTEND_SERVE_DIR="/var/www/proposal-drafter"
SERVICE_NAME="proposal-drafter"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting deployment of Proposal Drafter...${NC}"

# 1. Setup virtual environment for backend
if [ ! -d "${BACKEND_DIR}/venv" ]; then
    echo -e "${GREEN}Creating Python virtual environment...${NC}"
    cd ${BACKEND_DIR}
    python3 -m venv venv
    cd ..
fi

# 2. Install backend dependencies
echo -e "${GREEN}Installing backend dependencies...${NC}"
cd ${BACKEND_DIR}
source venv/bin/activate
pip install -r requirements.txt
cd ..

# 3. Install Redis if not present
if ! command -v redis-server &> /dev/null; then
    echo -e "${GREEN}Installing Redis...${NC}"
    sudo apt-get update
    sudo apt-get install -y redis-server
    sudo systemctl enable redis-server
    sudo systemctl start redis-server
fi

# 4. Create systemd service file for backend
echo -e "${GREEN}Setting up backend service...${NC}"
sudo bash -c "cat > /etc/systemd/system/${SERVICE_NAME}.service" << EOL
[Unit]
Description=Proposal Drafter Backend
After=network.target redis.service
Wants=redis.service

[Service]
User=$(whoami)
WorkingDirectory=$(pwd)/${BACKEND_DIR}
ExecStart=$(pwd)/${BACKEND_DIR}/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8502
Restart=always
Environment="PATH=$(pwd)/${BACKEND_DIR}/venv/bin"

[Install]
WantedBy=multi-user.target
EOL

# 5. Deploy frontend
echo -e "${GREEN}Deploying frontend...${NC}"
sudo mkdir -p ${FRONTEND_SERVE_DIR}
sudo cp -r ${FRONTEND_DIR}/* ${FRONTEND_SERVE_DIR}/

# 6. Configure Nginx (if needed)
if [ ! -f "/etc/nginx/sites-available/${SERVICE_NAME}" ]; then
    echo -e "${GREEN}Configuring Nginx...${NC}"
    sudo bash -c "cat > /etc/nginx/sites-available/${SERVICE_NAME}" << EOL
server {
    listen 80;
    server_name proposal.example.com;  # Replace with your domain

    location / {
        root ${FRONTEND_SERVE_DIR};
        try_files \$uri \$uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8502;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOL
    sudo ln -sf /etc/nginx/sites-available/${SERVICE_NAME} /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx
fi

# 7. Start/restart the service
echo -e "${GREEN}Starting backend service...${NC}"
sudo systemctl daemon-reload
sudo systemctl restart ${SERVICE_NAME}
sudo systemctl enable ${SERVICE_NAME}

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}Backend API: http://localhost:8502${NC}"
echo -e "${GREEN}Frontend: http://proposal.example.com${NC}"