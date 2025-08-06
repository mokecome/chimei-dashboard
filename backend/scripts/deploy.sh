#!/bin/bash

# Chime Dashboard Backend Deployment Script
# This script handles the deployment of the Chime Dashboard backend application

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="chime_dashboard"
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_IMAGE="chime-dashboard-backend"
DOCKER_TAG="latest"
CONTAINER_NAME="chime-backend"
NETWORK_NAME="chime-network"
DB_CONTAINER_NAME="chime-mysql"

# Environment configuration
ENVIRONMENT=${1:-"development"}  # development, staging, production
FORCE_REBUILD=${2:-"false"}

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed or not in PATH"
        exit 1
    fi
}

# Function to wait for database to be ready
wait_for_db() {
    print_status "Waiting for database to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker exec $DB_CONTAINER_NAME mysqladmin ping -h localhost -u root -p123456 --silent; then
            print_success "Database is ready"
            return 0
        fi
        
        print_status "Attempt $attempt/$max_attempts: Database not ready, waiting..."
        sleep 2
        ((attempt++))
    done
    
    print_error "Database failed to become ready after $max_attempts attempts"
    return 1
}

# Function to create Docker network if it doesn't exist
create_network() {
    if ! docker network ls | grep -q $NETWORK_NAME; then
        print_status "Creating Docker network: $NETWORK_NAME"
        docker network create $NETWORK_NAME
        print_success "Network created successfully"
    else
        print_status "Network $NETWORK_NAME already exists"
    fi
}

# Function to start MySQL database
start_database() {
    print_status "Starting MySQL database..."
    
    if docker ps -a | grep -q $DB_CONTAINER_NAME; then
        if docker ps | grep -q $DB_CONTAINER_NAME; then
            print_status "Database container is already running"
        else
            print_status "Starting existing database container"
            docker start $DB_CONTAINER_NAME
        fi
    else
        print_status "Creating new database container"
        docker run -d \
            --name $DB_CONTAINER_NAME \
            --network $NETWORK_NAME \
            -e MYSQL_ROOT_PASSWORD=123456 \
            -e MYSQL_DATABASE=chime_dashboard \
            -e MYSQL_CHARACTER_SET_SERVER=utf8mb4 \
            -e MYSQL_COLLATION_SERVER=utf8mb4_unicode_ci \
            -p 3306:3306 \
            -v chime_mysql_data:/var/lib/mysql \
            mysql:8.0
    fi
    
    # Wait for database to be ready
    wait_for_db
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Check if alembic is available
    if [ -f "$BACKEND_DIR/alembic.ini" ]; then
        cd $BACKEND_DIR
        
        # Install dependencies if needed
        if [ ! -d "venv" ]; then
            print_status "Creating virtual environment..."
            python3 -m venv venv
        fi
        
        source venv/bin/activate
        pip install -r requirements.txt
        
        # Run migrations
        alembic upgrade head
        
        print_success "Database migrations completed"
    else
        print_warning "Alembic configuration not found, skipping migrations"
    fi
}

# Function to initialize database with default data
init_database() {
    print_status "Initializing database with default data..."
    
    cd $BACKEND_DIR
    
    if [ -f "scripts/init_db.py" ]; then
        python scripts/init_db.py
        print_success "Database initialized successfully"
    else
        print_warning "Database initialization script not found"
    fi
}

# Function to build Docker image
build_image() {
    print_status "Building Docker image: $DOCKER_IMAGE:$DOCKER_TAG"
    
    cd $BACKEND_DIR
    
    # Build the image
    docker build \
        --tag $DOCKER_IMAGE:$DOCKER_TAG \
        --build-arg ENVIRONMENT=$ENVIRONMENT \
        .
    
    print_success "Docker image built successfully"
}

# Function to stop and remove existing container
stop_container() {
    if docker ps | grep -q $CONTAINER_NAME; then
        print_status "Stopping existing container: $CONTAINER_NAME"
        docker stop $CONTAINER_NAME
    fi
    
    if docker ps -a | grep -q $CONTAINER_NAME; then
        print_status "Removing existing container: $CONTAINER_NAME"
        docker rm $CONTAINER_NAME
    fi
}

# Function to start the application container
start_container() {
    print_status "Starting application container: $CONTAINER_NAME"
    
    # Environment-specific configurations
    case $ENVIRONMENT in
        "production")
            ENV_FILE=".env.production"
            LOG_LEVEL="INFO"
            WORKERS=4
            PORT=8000
            ;;
        "staging")
            ENV_FILE=".env.staging"
            LOG_LEVEL="INFO"
            WORKERS=2
            PORT=8001
            ;;
        "development")
            ENV_FILE=".env.development"
            LOG_LEVEL="DEBUG"
            WORKERS=1
            PORT=8000
            ;;
        *)
            print_error "Unknown environment: $ENVIRONMENT"
            exit 1
            ;;
    esac
    
    # Check if environment file exists
    if [ ! -f "$BACKEND_DIR/$ENV_FILE" ]; then
        print_warning "Environment file $ENV_FILE not found, using .env.example"
        ENV_FILE=".env.example"
    fi
    
    # Start the container
    docker run -d \
        --name $CONTAINER_NAME \
        --network $NETWORK_NAME \
        --env-file $BACKEND_DIR/$ENV_FILE \
        -e ENVIRONMENT=$ENVIRONMENT \
        -e LOG_LEVEL=$LOG_LEVEL \
        -e WORKERS=$WORKERS \
        -p $PORT:8000 \
        -v $BACKEND_DIR/storage:/app/storage \
        -v $BACKEND_DIR/logs:/app/logs \
        --restart unless-stopped \
        $DOCKER_IMAGE:$DOCKER_TAG
    
    print_success "Application container started successfully"
    print_status "Application is available at: http://localhost:$PORT"
    print_status "API documentation: http://localhost:$PORT/docs"
}

# Function to run health checks
health_check() {
    print_status "Running health checks..."
    
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health &>/dev/null; then
            print_success "Application health check passed"
            return 0
        fi
        
        print_status "Attempt $attempt/$max_attempts: Health check failed, waiting..."
        sleep 3
        ((attempt++))
    done
    
    print_error "Application failed health check after $max_attempts attempts"
    return 1
}

# Function to show logs
show_logs() {
    print_status "Showing application logs..."
    docker logs -f $CONTAINER_NAME
}

# Function to show status
show_status() {
    print_status "Deployment Status:"
    echo
    
    # Check database
    if docker ps | grep -q $DB_CONTAINER_NAME; then
        print_success "✓ Database container is running"
    else
        print_error "✗ Database container is not running"
    fi
    
    # Check application
    if docker ps | grep -q $CONTAINER_NAME; then
        print_success "✓ Application container is running"
        
        # Get container details
        local container_info=$(docker inspect $CONTAINER_NAME --format='{{.State.Status}}|{{.NetworkSettings.Ports}}')
        echo "  Status: $(echo $container_info | cut -d'|' -f1)"
        echo "  Ports: $(echo $container_info | cut -d'|' -f2)"
    else
        print_error "✗ Application container is not running"
    fi
    
    # Check network
    if docker network ls | grep -q $NETWORK_NAME; then
        print_success "✓ Docker network exists"
    else
        print_error "✗ Docker network does not exist"
    fi
}

# Function to cleanup (stop and remove containers)
cleanup() {
    print_status "Cleaning up deployment..."
    
    # Stop and remove application container
    if docker ps | grep -q $CONTAINER_NAME; then
        docker stop $CONTAINER_NAME
    fi
    if docker ps -a | grep -q $CONTAINER_NAME; then
        docker rm $CONTAINER_NAME
    fi
    
    # Optionally stop database (uncomment if needed)
    # if docker ps | grep -q $DB_CONTAINER_NAME; then
    #     docker stop $DB_CONTAINER_NAME
    # fi
    
    print_success "Cleanup completed"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [ENVIRONMENT] [OPTION]"
    echo
    echo "ENVIRONMENT:"
    echo "  development  - Development environment (default)"
    echo "  staging      - Staging environment"
    echo "  production   - Production environment"
    echo
    echo "OPTIONS:"
    echo "  rebuild      - Force rebuild of Docker image"
    echo
    echo "Commands:"
    echo "  $0 deploy [ENVIRONMENT] [rebuild]  - Deploy the application"
    echo "  $0 status                          - Show deployment status"
    echo "  $0 logs                            - Show application logs"
    echo "  $0 cleanup                         - Stop and remove containers"
    echo "  $0 health                          - Run health check"
    echo
    echo "Examples:"
    echo "  $0 development                     - Deploy to development"
    echo "  $0 production rebuild              - Deploy to production with rebuild"
    echo "  $0 status                          - Show current status"
    echo "  $0 cleanup                         - Clean up deployment"
}

# Main deployment function
deploy() {
    print_status "Starting deployment for environment: $ENVIRONMENT"
    
    # Check prerequisites
    check_command "docker"
    check_command "curl"
    
    # Create network
    create_network
    
    # Start database
    start_database
    
    # Build Docker image (rebuild if forced or image doesn't exist)
    if [ "$FORCE_REBUILD" = "true" ] || [ -z "$(docker images -q $DOCKER_IMAGE:$DOCKER_TAG)" ]; then
        build_image
    else
        print_status "Using existing Docker image (use 'rebuild' to force rebuild)"
    fi
    
    # Stop existing container
    stop_container
    
    # Run database migrations
    run_migrations
    
    # Initialize database if needed
    if [ "$ENVIRONMENT" = "development" ]; then
        init_database
    fi
    
    # Start new container
    start_container
    
    # Wait a moment for container to start
    sleep 5
    
    # Run health check
    health_check
    
    print_success "Deployment completed successfully!"
    print_status "Environment: $ENVIRONMENT"
    print_status "Application URL: http://localhost:$(docker port $CONTAINER_NAME 8000/tcp | cut -d':' -f2)"
    print_status "API Documentation: http://localhost:$(docker port $CONTAINER_NAME 8000/tcp | cut -d':' -f2)/docs"
}

# Main script logic
case "${1:-deploy}" in
    "deploy")
        shift
        ENVIRONMENT=${1:-"development"}
        FORCE_REBUILD=$([ "${2}" = "rebuild" ] && echo "true" || echo "false")
        deploy
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "cleanup")
        cleanup
        ;;
    "health")
        health_check
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        # If first argument is an environment, treat as deploy
        if [[ "$1" =~ ^(development|staging|production)$ ]]; then
            ENVIRONMENT=$1
            FORCE_REBUILD=$([ "${2}" = "rebuild" ] && echo "true" || echo "false")
            deploy
        else
            show_usage
            exit 1
        fi
        ;;
esac