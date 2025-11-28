#!/bin/bash

# Deployment script for AI Financial Analyst Microservices

set -e  # Exit on any error

echo "Starting deployment of AI Financial Analyst Microservices..."

# Create necessary directories
mkdir -p data/db data/temp data/vector_db data/cache data/storage

# Build and start all services
echo "Building and starting services..."
docker-compose -f docker-compose.microservices.yml up --build -d

# Wait for services to start
echo "Waiting for services to start..."
sleep 30

# Check service status
echo "Checking service status..."
docker-compose -f docker-compose.microservices.yml ps

# Verify health of services
echo "Verifying health of services..."

# Check gateway
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Gateway is healthy"
else
    echo "❌ Gateway health check failed"
fi

# Check frontend
if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is accessible"
else
    echo "⚠️  Frontend may not be accessible yet"
fi

# Check MinIO
if curl -sf http://localhost:9000/minio/health/ready > /dev/null 2>&1; then
    echo "✅ MinIO is healthy"
else
    echo "⚠️  MinIO health check failed"
fi

echo
echo "Deployment Summary:"
echo "==================="
echo "Frontend: http://localhost:3000"
echo "Gateway:  http://localhost:8000"
echo "MinIO:    http://localhost:9001 (console)"
echo
echo "Default credentials:"
echo "  Demo user: demo@example.com / demo123"
echo "  Admin user: admin@example.com / admin123"
echo
echo "To view logs: docker-compose -f docker-compose.microservices.yml logs -f"
echo "To stop services: docker-compose -f docker-compose.microservices.yml down"
echo
echo "Deployment completed!"