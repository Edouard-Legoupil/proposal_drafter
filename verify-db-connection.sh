#!/bin/bash

# This script verifies the database connection for both admin and application user

# Get database connection details
read -p "Server FQDN (e.g., proposalgen-db.postgres.database.azure.com): " DB_HOST
read -p "Admin Username: " ADMIN_USER
read -s -p "Admin Password: " ADMIN_PASSWORD
echo
DB_NAME="proposalgen"
DB_PORT=5432

# Test admin connection
echo "Testing connection as admin user ($ADMIN_USER)..."
PGPASSWORD=$ADMIN_PASSWORD psql "sslmode=require host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$ADMIN_USER" -c "SELECT current_user, current_database();"

# Test application user connection
echo "Testing connection as application user (iom_uc1_user)..."
PGPASSWORD=IomUC1@20250523$ psql "sslmode=require host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=iom_uc1_user" -c "SELECT current_user, current_database();"

# Check if tables exist
echo "Checking if tables exist (as application user)..."
PGPASSWORD=IomUC1@20250523$ psql "sslmode=require host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=iom_uc1_user" -c "\dt"

# Check if application user has correct permissions
echo "Verifying permissions (as application user)..."
PGPASSWORD=IomUC1@20250523$ psql "sslmode=require host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=iom_uc1_user" -c "INSERT INTO users (id, email, name, password) VALUES ('550e8400-e29b-41d4-a716-446655440001', 'test2@example.com', 'Test User 2', 'test_password') ON CONFLICT (email) DO NOTHING; SELECT * FROM users WHERE email='test2@example.com';"