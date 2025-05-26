#!/bin/bash

# This script connects to the Azure PostgreSQL database and sets up the required tables

# Get the database connection details from Azure portal
echo "Enter the Azure PostgreSQL server details:"
read -p "Server FQDN (e.g., proposalgen-db.postgres.database.azure.com): " DB_HOST
read -p "Admin Username: " DB_USERNAME
read -s -p "Admin Password: " DB_PASSWORD
echo
read -p "Database Name (default: proposalgen): " DB_NAME
DB_NAME=${DB_NAME:-proposalgen}
DB_PORT=5432

# Create a temporary SQL file with the setup script
echo "Preparing database setup script..."
TMP_SQL=$(mktemp)
cat database-setup.sql > $TMP_SQL

# Add firewall rule to allow your IP (this requires az cli to be installed)
echo "Adding firewall rule to allow your current IP..."
MY_IP=$(curl -s https://api.ipify.org)
if [ -n "$MY_IP" ]; then
  echo "Your IP address is: $MY_IP"
  az postgres flexible-server firewall-rule create \
    --resource-group proposalgen-rg \
    --name proposalgen-db \
    --rule-name AllowMyIP \
    --start-ip-address $MY_IP \
    --end-ip-address $MY_IP
fi

# Connect and run the script as admin
echo "Connecting to database and running setup script as admin..."
PGPASSWORD=$DB_PASSWORD psql "sslmode=require host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USERNAME" -f $TMP_SQL

# Test connection as application user
echo "Testing connection as application user (iom_uc1_user)..."
PGPASSWORD=IomUC1@20250523$ psql "sslmode=require host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=iom_uc1_user" -c "SELECT 'Connection successful as application user' AS status;"

# Clean up
rm $TMP_SQL

echo "Database setup complete!"