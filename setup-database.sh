#!/bin/bash

# Connect to PostgreSQL server and execute the setup script
echo "Setting up Proposal Drafter database..."

# Get database connection details from environment or use defaults
DB_HOST=${DB_HOST:-proposalgen-db.postgres.database.azure.com}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-proposalgen}
DB_USERNAME=${DB_USERNAME:-postgresadmin}
DB_PASSWORD=${DB_PASSWORD:-your-secure-password}

# Create the database if it doesn't exist
echo "Creating database $DB_NAME if it doesn't exist..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USERNAME -p $DB_PORT -c "CREATE DATABASE $DB_NAME;" || echo "Database already exists or couldn't be created."

# Execute the SQL script
echo "Running setup script..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USERNAME -p $DB_PORT -d $DB_NAME -f database-setup.sql

echo "Database setup complete!"