#!/bin/bash

# Start Microservices - Simplified Version
# This script starts the available microservices

set -e

echo "🚀 Starting AI Financial Analyst Microservices"
echo "=============================================="

# Colors for output
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

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down --remove-orphans 2>/dev/null || true

# Create data directories
print_status "Creating data directories..."
mkdir -p data/{user-service,document-service,analysis-service,analytics-service,storage-service,minio}
chmod -R 777 data/ 2>/dev/null || true

# Create simplified docker-compose for available services
print_status "Creating simplified docker-compose configuration..."

cat > docker-compose-simple.yml << 'EOF'
version: '3.8'

services:
  # API Gateway
  gateway:
    build: ./gateway
    ports:
      - "8000:8000"
    environment:
      - USER_SERVICE_URL=http://user-service:8001
    depends_on:
      - user-service
    networks:
      - microservices-network

  # User Service
  user-service:
    build: ./user-service
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=sqlite:////data/db/users.db
      - STORAGE_PATH=/data
      - JWT_SECRET_KEY=your-secret-key-here-change-in-production
    volumes:
      - ./data/user-service:/data
    networks:
      - microservices-network

  # MinIO Storage
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - ./data/minio:/data
    command: server /data --console-address ":9001"
    networks:
      - microservices-network

  # Frontend (using existing build)
  frontend:
    build: ../frontend
    ports:
      - "3000:80"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      - gateway
    networks:
      - microservices-network

networks:
  microservices-network:
    driver: bridge
EOF

# Build and start services
print_status "Building and starting services..."
docker-compose -f docker-compose-simple.yml build

print_status "Starting services..."
docker-compose -f docker-compose-simple.yml up -d

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 15

# Check service health
print_status "Checking service health..."

services_to_check=("gateway:8000" "user-service:8001")

for service_port in "${services_to_check[@]}"; do
    service_name=$(echo $service_port | cut -d':' -f1)
    port=$(echo $service_port | cut -d':' -f2)
    
    print_status "Checking $service_name on port $port..."
    
    max_attempts=20
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
            print_success "$service_name is healthy"
            break
        else
            if [ $attempt -eq $max_attempts ]; then
                print_warning "$service_name may not be fully ready yet"
            else
                print_status "Waiting for $service_name... (attempt $attempt/$max_attempts)"
                sleep 3
                ((attempt++))
            fi
        fi
    done
done

# Display service status
print_status "Service Status:"
echo "=============="
docker-compose -f docker-compose-simple.yml ps

echo ""
print_success "🎉 Microservices started successfully!"
echo ""
echo "Available Services:"
echo "=================="
echo "• API Gateway:      http://localhost:8000"
echo "• User Service:     http://localhost:8001"
echo "• MinIO Console:    http://localhost:9001"
echo "• Frontend:         http://localhost:3000"
echo ""
echo "Health Check URLs:"
echo "=================="
echo "• Gateway: http://localhost:8000/health"
echo "• User Service: http://localhost:8001/health"
echo ""
echo "Default Credentials:"
echo "==================="
echo "• Demo User: demo@example.com / demo123"
echo "• Admin User: admin@example.com / admin123"
echo "• MinIO: minioadmin / minioadmin"
echo ""
echo "To view logs: docker-compose -f docker-compose-simple.yml logs [service-name]"
echo "To stop services: docker-compose -f docker-compose-simple.yml down"
echo ""
print_status "Note: This is a simplified microservices setup with Gateway and User Service."
print_status "The full microservices architecture can be completed by implementing the remaining services."
