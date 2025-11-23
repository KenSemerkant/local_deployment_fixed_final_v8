# 🚀 Microservices Startup Guide

This guide will help you start the AI Financial Analyst microservices-based solution.

## 📋 Prerequisites

Before starting, ensure you have:

- **Docker** (version 20.0 or higher)
- **Docker Compose** (version 1.29 or higher)
- **Git** (for cloning the repository)
- **8GB+ RAM** (recommended for running all services)

### Check Prerequisites

```bash
# Check Docker
docker --version
docker-compose --version

# Check if Docker is running
docker info
```

## 🚀 Quick Start (Recommended)

### Option 1: Simplified Microservices Setup

This starts the core services (Gateway + User Service) that are fully implemented:

```bash
# Navigate to microservices directory
cd microservices

# Start the simplified microservices
./start-microservices.sh
```

**What this includes:**
- ✅ API Gateway (Port 8000)
- ✅ User Service (Port 8001) 
- ✅ MinIO Storage (Ports 9000, 9001)
- ✅ Frontend (Port 3000)

### Option 2: Full Microservices (Advanced)

If you want to try the full microservices setup (some services may need completion):

```bash
# Navigate to microservices directory
cd microservices

# Build and deploy all services
./build-and-deploy.sh
```

## 🌐 Access the Application

Once started, you can access:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Main application interface |
| **API Gateway** | http://localhost:8000 | API entry point |
| **User Service** | http://localhost:8001 | User management |
| **MinIO Console** | http://localhost:9001 | File storage admin |

## 🔐 Default Credentials

### Application Users
- **Demo User**: `demo@example.com` / `demo123`
- **Admin User**: `admin@example.com` / `admin123`

### MinIO Storage
- **Username**: `minioadmin`
- **Password**: `minioadmin`

## 🔍 Verify Installation

### 1. Check Service Health

```bash
# Check API Gateway
curl http://localhost:8000/health

# Check User Service
curl http://localhost:8001/health

# Expected response: {"status": "healthy", ...}
```

### 2. Test Authentication

```bash
# Test login via API Gateway
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo@example.com&password=demo123"

# Expected: {"access_token": "...", "token_type": "bearer"}
```

### 3. Access Frontend

1. Open http://localhost:3000 in your browser
2. Login with demo credentials
3. Verify the interface loads correctly

## 🛠️ Development Commands

### View Logs
```bash
# View all service logs
docker-compose -f docker-compose-simple.yml logs

# View specific service logs
docker-compose -f docker-compose-simple.yml logs gateway
docker-compose -f docker-compose-simple.yml logs user-service
```

### Restart Services
```bash
# Restart all services
docker-compose -f docker-compose-simple.yml restart

# Restart specific service
docker-compose -f docker-compose-simple.yml restart gateway
```

### Stop Services
```bash
# Stop all services
docker-compose -f docker-compose-simple.yml down

# Stop and remove volumes
docker-compose -f docker-compose-simple.yml down -v
```

### Rebuild Services
```bash
# Rebuild and restart
docker-compose -f docker-compose-simple.yml down
docker-compose -f docker-compose-simple.yml build --no-cache
docker-compose -f docker-compose-simple.yml up -d
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using the port
lsof -i :8000
lsof -i :3000

# Kill the process or change ports in docker-compose
```

#### 2. Docker Permission Issues
```bash
# On Linux, add user to docker group
sudo usermod -aG docker $USER
# Then logout and login again
```

#### 3. Services Not Starting
```bash
# Check Docker resources
docker system df
docker system prune  # Clean up if needed

# Check service logs
docker-compose -f docker-compose-simple.yml logs [service-name]
```

#### 4. Database Issues
```bash
# Reset databases
rm -rf data/user-service/db/
./start-microservices.sh
```

### Service-Specific Troubleshooting

#### Gateway Issues
```bash
# Check gateway logs
docker-compose -f docker-compose-simple.yml logs gateway

# Test direct access
curl http://localhost:8000/health
```

#### User Service Issues
```bash
# Check user service logs
docker-compose -f docker-compose-simple.yml logs user-service

# Test direct access
curl http://localhost:8001/health
```

#### Frontend Issues
```bash
# Check frontend logs
docker-compose -f docker-compose-simple.yml logs frontend

# Rebuild frontend
docker-compose -f docker-compose-simple.yml build frontend --no-cache
```

## 📊 Monitoring

### Health Checks
- Gateway: http://localhost:8000/health
- User Service: http://localhost:8001/health

### Service Status
```bash
# Check running containers
docker-compose -f docker-compose-simple.yml ps

# Check resource usage
docker stats
```

## 🔄 Migration from Monolith

If you're migrating from the monolithic version:

1. **Stop the monolithic backend**:
   ```bash
   cd .. # Go back to main directory
   docker-compose down
   ```

2. **Start microservices**:
   ```bash
   cd microservices
   ./start-microservices.sh
   ```

3. **Update frontend configuration** (if needed):
   - The frontend should automatically connect to the new API Gateway

## 🚀 Next Steps

### Completing the Microservices

To implement the full microservices architecture:

1. **Document Service** - Handle file uploads and metadata
2. **Analysis Service** - Process documents with LLM
3. **Analytics Service** - Track usage and metrics
4. **Storage Service** - Manage file storage operations

### Production Deployment

For production deployment:

1. **Use external databases** (PostgreSQL, MySQL)
2. **Configure proper secrets** and environment variables
3. **Set up load balancing** and service discovery
4. **Implement monitoring** and logging solutions
5. **Configure HTTPS** and security headers

## 📞 Support

If you encounter issues:

1. Check the logs: `docker-compose -f docker-compose-simple.yml logs`
2. Verify prerequisites are met
3. Try rebuilding: `docker-compose -f docker-compose-simple.yml build --no-cache`
4. Reset everything: `docker-compose -f docker-compose-simple.yml down -v && ./start-microservices.sh`

## 🎯 Success Indicators

You'll know the microservices are working when:

- ✅ All health checks return "healthy"
- ✅ Frontend loads at http://localhost:3000
- ✅ You can login with demo credentials
- ✅ API Gateway routes requests correctly
- ✅ No error messages in service logs
