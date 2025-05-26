# Accessing and Managing the Azure PostgreSQL Database

This guide shows how to access your Azure PostgreSQL database using Azure Cloud Shell.

## Using Azure Cloud Shell

1. Login to the [Azure Portal](https://portal.azure.com)
2. Click on the Cloud Shell icon (>_) at the top of the page
3. Select "Bash" when prompted

## Connect to the PostgreSQL Database

```bash
# First, get your server details
PGSERVER=$(az postgres flexible-server list --query "[0].fullyQualifiedDomainName" -o tsv)
PGUSER=$(az postgres flexible-server list --query "[0].administratorLogin" -o tsv)

# Connect to the PostgreSQL server
psql "host=$PGSERVER port=5432 dbname=proposalgen user=$PGUSER sslmode=require"
```

When prompted, enter your PostgreSQL admin password.

## Useful PostgreSQL Commands

Once connected, you can use these commands:

```sql
-- List all databases
\l

-- Connect to a specific database
\c proposalgen

-- List all tables
\dt

-- View table structure
\d users
\d proposals

-- View sample data
SELECT * FROM users LIMIT 5;
SELECT * FROM proposals LIMIT 5;

-- Create a test user
INSERT INTO users (id, email, name, password) 
VALUES (
    '550e8400-e29b-41d4-a716-446655440001', 
    'test@example.com', 
    'Test User', 
    'pbkdf2:sha256:150000$KkCqT4Mj$7ca33681db68f809b46e9ac6187248f9f20b8895b15dfd29522c51b884306250'
);

-- Exit psql
\q
```

## Checking Connection from App Service

To verify the App Service can connect to the database:

1. Go to your App Service in the Azure Portal
2. Click on "Log stream" in the left menu
3. Look for database connection logs
4. If you see connection errors:
   - Check the environment variables (DB_HOST, DB_USERNAME, etc.)
   - Verify the firewall rules allow connections from your App Service

## Managing Firewall Rules

```bash
# Add a firewall rule to allow Azure services
az postgres flexible-server firewall-rule create \
  --resource-group proposalgen-rg \
  --name proposalgen-db \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# Add a firewall rule for your current IP
MY_IP=$(curl -s https://api.ipify.org)
az postgres flexible-server firewall-rule create \
  --resource-group proposalgen-rg \
  --name proposalgen-db \
  --rule-name AllowMyIP \
  --start-ip-address $MY_IP \
  --end-ip-address $MY_IP
```