# Microservice Migration Guide

This document describes how we've migrated the monolithic AI Financial Analyst application to a microservice architecture.

## Architecture Overview

The application has been decomposed into the following services:

1. **Gateway Service**: API Gateway and frontend hosting
2. **Authentication Service**: User authentication and authorization
3. **Document Service**: Document processing and management
4. **LLM Service**: LLM integration and processing
5. **Analytics Service**: Usage analytics and metrics
6. **Storage Service**: File storage management

## Service Responsibilities

### Gateway Service
- Routes API requests to appropriate services
- Serves frontend application
- Handles authentication token forwarding

### Authentication Service (`/auth`)
- Manages user accounts and authentication
- Handles JWT token generation and validation
- Provides user management endpoints

### Document Service (`/documents`)
- Manages document upload, storage, and retrieval
- Handles document processing and analysis
- Interfaces with storage service for file operations

### LLM Service (`/llm`)
- Processes document analysis using LLMs
- Handles Q&A functionality
- Manages vector database operations

### Analytics Service (`/analytics`)
- Tracks system usage and metrics
- Provides analytics dashboards
- Manages user feedback data

### Storage Service (`/storage`)
- Manages file storage operations
- Handles cleanup and maintenance tasks
- Provides storage analytics

## API Endpoints Mapping

The following API endpoints have been redistributed:

### Authentication Endpoints
Moved from: `http://localhost:8000/auth/*`
To: `http://localhost:8000/api/auth/*` → routed to auth-service

### Document Endpoints  
Moved from: `http://localhost:8000/documents/*`
To: `http://localhost:8000/api/documents/*` → routed to document-service

### LLM Endpoints
Moved from: `http://localhost:8000/llm/*`
To: `http://localhost:8000/api/llm/*` → routed to llm-service

### Analytics Endpoints
Moved from: `http://localhost:8000/analytics/*`
To: `http://localhost:8000/api/analytics/*` → routed to analytics-service

### Storage Endpoints
Moved from: `http://localhost:8000/storage/*`
To: `http://localhost:8000/api/storage/*` → routed to storage-service

## Deployment

The application is deployed using the new docker-compose.microservices.yml file which orchestrates all services.

To deploy:
```bash
cd microservices
docker-compose -f docker-compose.microservices.yml up -d --build
```

## Configuration

Environment variables have been updated to support the microservice architecture:
- `REACT_APP_API_URL`: Points to the gateway service
- Service-specific configurations in docker-compose file

## Database Changes

Each service now maintains its own database for its specific domain:
- Authentication service: auth.db
- Document service: documents.db
- Analytics service: analytics.db
- Storage service: storage.db
- LLM service: maintains its own state in vector databases

## Frontend Changes

The frontend has been updated to work with the new microservice API structure:
- Updated API service to route through gateway
- New service-specific API functions
- Maintained backward compatibility where possible