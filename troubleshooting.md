# AI Financial Analyst - Local Deployment Troubleshooting Guide

This document provides solutions for common issues that may occur when deploying the AI Financial Analyst locally.

## Dependency Conflicts

### OpenAI and LangChain Version Conflict

**Issue**: Dependency conflict between OpenAI and LangChain libraries:
```
ERROR: Cannot install -r requirements.txt (line 9) and openai==1.3.0 because these package versions have conflicting dependencies.
The conflict is caused by:
    The user requested openai==1.3.0
    langchain-openai 0.0.2 depends on openai<2.0.0 and >=1.6.1
```

**Solution**: Update the requirements.txt file to use OpenAI version 1.6.1 or higher:
```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.4.2
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib==1.7.4
minio==7.1.17
langchain==0.0.267
openai==1.6.1
faiss-cpu==1.7.4
pymupdf==1.23.3
python-dotenv==1.0.0
```

Then rebuild the Docker containers:
```bash
docker-compose down
docker-compose up --build -d
```

## Docker Compose Issues

### Services Not Starting

**Issue**: One or more services fail to start properly.

**Solution**:
1. Check the logs for each service:
   ```bash
   docker-compose logs backend
   docker-compose logs frontend
   docker-compose logs minio
   ```

2. Ensure all required directories exist:
   ```bash
   mkdir -p data/minio
   chmod -R 777 data
   ```

3. Verify Docker has sufficient resources (CPU, memory).

### Network Connectivity Issues

**Issue**: Services cannot communicate with each other.

**Solution**:
1. Ensure all services are on the same Docker network:
   ```bash
   docker network ls
   docker network inspect financial-analyst-network
   ```

2. Check if services are running:
   ```bash
   docker-compose ps
   ```

3. Verify container health:
   ```bash
   docker ps --format "{{.Names}}: {{.Status}}"
   ```

## MinIO Issues

**Issue**: MinIO service is not accessible or buckets cannot be created.

**Solution**:
1. Check MinIO logs:
   ```bash
   docker-compose logs minio
   ```

2. Ensure MinIO is running:
   ```bash
   curl http://localhost:9000/minio/health/live
   ```

3. Verify MinIO credentials in docker-compose.yml match those in the backend configuration.

## Frontend Issues

**Issue**: Frontend cannot connect to backend API.

**Solution**:
1. Verify the REACT_APP_API_URL in the frontend Dockerfile:
   ```
   REACT_APP_API_URL=http://localhost:8000
   ```

2. Check browser console for CORS errors.

3. Ensure backend is running and accessible:
   ```bash
   curl http://localhost:8000/health
   ```

## Backend Issues

**Issue**: Backend service crashes or returns errors.

**Solution**:
1. Check backend logs:
   ```bash
   docker-compose logs backend
   ```

2. Verify environment variables are set correctly in docker-compose.yml.

3. Ensure data directory has proper permissions:
   ```bash
   chmod -R 777 data
   ```

## Platform-Specific Issues

### Windows

**Issue**: Path issues with Docker volumes.

**Solution**: Use forward slashes in volume paths and ensure Docker has permission to access the directories.

### macOS

**Issue**: Performance issues with Docker Desktop.

**Solution**: Increase resource allocation in Docker Desktop preferences.

### Linux

**Issue**: Permission issues with mounted volumes.

**Solution**: Check SELinux settings or use appropriate volume mount options.

## Additional Resources

If you continue to experience issues, please refer to:
- Docker documentation: https://docs.docker.com/
- FastAPI documentation: https://fastapi.tiangolo.com/
- MinIO documentation: https://min.io/docs/minio/container/index.html
