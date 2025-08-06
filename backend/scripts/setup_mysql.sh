#!/bin/bash

# MySQL Setup Script for Chime Dashboard
# This script helps create the database and user for the application

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root!"
   exit 1
fi

print_status "MySQL Setup for Chime Dashboard"
echo "================================"
echo

# Prompt for MySQL root password
read -sp "Enter MySQL root password: " MYSQL_ROOT_PASSWORD
echo

# Test connection
print_status "Testing MySQL connection..."
if mysql -u root -p"$MYSQL_ROOT_PASSWORD" -e "SELECT 1" &>/dev/null; then
    print_success "Successfully connected to MySQL"
else
    print_error "Failed to connect to MySQL with provided password"
    exit 1
fi

# Database configuration
DB_NAME="chime_dashboard"
DB_USER="root"
DB_PASSWORD="123456"
DB_HOST="localhost"

print_status "Creating database and user..."

# Create database and user
mysql -u root -p"$MYSQL_ROOT_PASSWORD" <<EOF
-- Create database if not exists
CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user if not exists (MySQL 5.7+ syntax)
CREATE USER IF NOT EXISTS '${DB_USER}'@'${DB_HOST}' IDENTIFIED BY '${DB_PASSWORD}';

-- Grant privileges
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'${DB_HOST}';

-- Also create user for 127.0.0.1
CREATE USER IF NOT EXISTS '${DB_USER}'@'127.0.0.1' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'127.0.0.1';

-- Flush privileges
FLUSH PRIVILEGES;

-- Show created database
SHOW DATABASES LIKE '${DB_NAME}';
EOF

if [ $? -eq 0 ]; then
    print_success "Database and user created successfully"
else
    print_error "Failed to create database or user"
    exit 1
fi

# Update .env file
ENV_FILE="../.env"
ENV_BACKUP="../.env.backup.$(date +%Y%m%d_%H%M%S)"

print_status "Updating .env file..."

# Backup existing .env
if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "$ENV_BACKUP"
    print_status "Backed up existing .env to $ENV_BACKUP"
fi

# Create new database URL
NEW_DB_URL="mysql+pymysql://${DB_USER}:${DB_PASSWORD}@127.0.0.1:3306/${DB_NAME}?charset=utf8mb4"

# Update or create .env file
if [ -f "$ENV_FILE" ]; then
    # Update existing DATABASE_URL
    sed -i.tmp "s|^DATABASE_URL=.*|DATABASE_URL=${NEW_DB_URL}|" "$ENV_FILE"
    rm -f "$ENV_FILE.tmp"
else
    # Create new .env from example
    if [ -f "../.env.example" ]; then
        cp "../.env.example" "$ENV_FILE"
        sed -i.tmp "s|^DATABASE_URL=.*|DATABASE_URL=${NEW_DB_URL}|" "$ENV_FILE"
        rm -f "$ENV_FILE.tmp"
    else
        print_error ".env.example not found"
        exit 1
    fi
fi

print_success "Updated DATABASE_URL in .env file"

# Show summary
echo
print_success "MySQL setup completed!"
echo "========================="
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
echo "Password: ${DB_PASSWORD}"
echo "Connection URL: ${NEW_DB_URL}"
echo
print_warning "Please keep these credentials safe!"
echo

# Ask if user wants to initialize the database
read -p "Do you want to initialize the database with default data? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Initializing database..."
    cd ..
    python scripts/init_db.py
    if [ $? -eq 0 ]; then
        print_success "Database initialized successfully"
    else
        print_error "Failed to initialize database"
        exit 1
    fi
fi

print_success "Setup complete! You can now start the application with:"
echo "  cd .."
echo "  python run_server.py"