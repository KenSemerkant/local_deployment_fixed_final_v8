#!/bin/bash

# Build and Deploy Microservices Script
# This script builds all microservices and deploys them using Docker Compose

set -e

echo "🚀 Building and Deploying AI Financial Analyst Microservices"
echo "============================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    print_error "Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

# Create data directories
print_status "Creating data directories..."
mkdir -p data/{user-service,document-service,analysis-service,analytics-service,storage-service,minio}
chmod -R 777 data/

# Stop existing services
print_status "Stopping existing services..."
docker-compose down --remove-orphans || true

# Build all services
print_status "Building microservices..."

services=("gateway" "user-service" "document-service" "analysis-service" "analytics-service" "storage-service")

for service in "${services[@]}"; do
    if [ -d "$service" ]; then
        print_status "Building $service..."
        docker-compose build $service
        if [ $? -eq 0 ]; then
            print_success "$service built successfully"
        else
            print_error "Failed to build $service"
            exit 1
        fi
    else
        print_warning "$service directory not found, skipping..."
    fi
done

# Start services
print_status "Starting microservices..."
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 10

# Check service health
print_status "Checking service health..."

services_to_check=("gateway:8000" "user-service:8001" "document-service:8002" "analysis-service:8003" "analytics-service:8004" "storage-service:8005")

for service_port in "${services_to_check[@]}"; do
    service_name=$(echo $service_port | cut -d':' -f1)
    port=$(echo $service_port | cut -d':' -f2)
    
    print_status "Checking $service_name on port $port..."
    
    # Try to connect to the service health endpoint
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
            print_success "$service_name is healthy"
            break
        else
            if [ $attempt -eq $max_attempts ]; then
                print_error "$service_name failed to start properly"
                print_status "Checking logs for $service_name..."
                docker-compose logs $service_name | tail -20
            else
                print_status "Waiting for $service_name... (attempt $attempt/$max_attempts)"
                sleep 2
                ((attempt++))
            fi
        fi
    done
done

# Display service status
print_status "Service Status:"
echo "=============="
docker-compose ps

# Display service URLs
echo ""
print_success "🎉 Microservices deployment completed!"
echo ""
echo "Service URLs:"
echo "============="
echo "• API Gateway:      http://localhost:8000"
echo "• User Service:     http://localhost:8001"
echo "• Document Service: http://localhost:8002"
echo "• Analysis Service: http://localhost:8003"
echo "• Analytics Service: http://localhost:8004"
echo "• Storage Service:  http://localhost:8005"
echo "• MinIO Console:    http://localhost:9001"
echo "• Frontend:         http://localhost:3000"
echo ""
echo "Health Check URLs:"
echo "=================="
for service_port in "${services_to_check[@]}"; do
    service_name=$(echo $service_port | cut -d':' -f1)
    port=$(echo $service_port | cut -d':' -f2)
    echo "• $service_name: http://localhost:$port/health"
done
echo ""

# Test API Gateway
print_status "Testing API Gateway..."
if curl -s -f "http://localhost:8000/health" > /dev/null 2>&1; then
    print_success "API Gateway is responding"
    echo ""
    echo "🚀 You can now access the application at:"
    echo "   Frontend: http://localhost:3000"
    echo "   API: http://localhost:8000"
    echo ""
    echo "Default credentials:"
    echo "   Demo User: demo@example.com / demo123"
    echo "   Admin User: admin@example.com / admin123"
else
    print_error "API Gateway is not responding"
    print_status "Checking gateway logs..."
    docker-compose logs gateway | tail -20
fi

echo ""
print_status "To view logs: docker-compose logs [service-name]"
print_status "To stop services: docker-compose down"
print_status "To restart services: docker-compose restart"
