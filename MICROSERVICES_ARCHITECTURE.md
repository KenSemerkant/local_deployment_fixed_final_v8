# AI Financial Analyst - Microservices Architecture

## Overview

The AI Financial Analyst application has been restructured into a microservices architecture with an API Gateway to route requests to specialized services. This provides better scalability, maintainability, and fault isolation compared to the previous monolithic design.

## Architecture Components

### 1. API Gateway Service
- **Location**: `./microservices/gateway/`
- **Port**: 8000 (externally accessible)
- **Function**: Routes API requests to appropriate microservices, handles cross-cutting concerns like authentication and rate limiting

### 2. Auth Service
- **Location**: `./microservices/auth-service/`
- **Function**: Handles user authentication, JWT token management, and user registration
- **Endpoints**: `/token`, `/users`, `/users/me`

### 3. Document Service
- **Location**: `./microservices/document-service/`
- **Function**: Manages document upload, processing, analysis, and Q&A functionality
- **Endpoints**: `/documents`, `/documents/{id}/analysis`, `/documents/{id}/ask`

### 4. LLM Service
- **Location**: `./microservices/llm-service/`
- **Function**: Handles all LLM interactions, document processing, and Q&A generation
- **Endpoints**: `/process`, `/ask`, `/status`, `/mode`

### 5. Analytics Service
- **Location**: `./microservices/analytics-service/`
- **Function**: Tracks usage, performance metrics, token usage, and user feedback
- **Endpoints**: `/admin/analytics/*`, `/feedback`

### 6. Storage Service
- **Location**: `./microservices/storage-service/`
- **Function**: Manages file storage, cleanup, and storage analytics
- **Endpoints**: `/admin/storage/*`

### 7. Supporting Services
- **Frontend**: React.js application served via Nginx
- **MinIO**: S3-compatible storage for documents
- **Database**: SQLite databases for each service

## Data Flow

1. **User Request**: Received by API Gateway
2. **Authentication**: Gateway validates JWT token with Auth Service
3. **Routing**: Gateway routes to appropriate service based on endpoint
4. **Processing**: Each service handles its specific functionality
5. **Response**: Gateway returns response to client

## Service Dependencies

- Gateway → All Services (for routing)
- Document Service → LLM Service (for processing)
- Document Service → Analytics Service (for tracking)
- Frontend → Gateway (for all API calls)

## Environment Variables

### Core Configuration
```bash
JWT_SECRET=your-secret-key
LLM_MODE=openai|ollama|mock
OPENAI_BASE_URL=http://host.docker.internal:1234/v1
OPENAI_API_KEY=lm-studio
OPENAI_MODEL=mistralai/magistral-small-2509
```

### Service URLs (for Gateway)
```bash
AUTH_SERVICE_URL=http://auth-service:8000
DOCUMENT_SERVICE_URL=http://document-service:8000
LLM_SERVICE_URL=http://llm-service:8000
ANALYTICS_SERVICE_URL=http://analytics-service:8000
STORAGE_SERVICE_URL=http://storage-service:8000
```

## Deployment

### Quick Start
```bash
# Deploy all services
./deploy_microservices.sh

# Or manually:
docker-compose -f docker-compose.microservices.yml up --build -d
```

### Access Points
- **Frontend**: http://localhost:3000
- **Gateway API**: http://localhost:8000
- **MinIO Console**: http://localhost:9001

### Default Credentials
- Demo: `demo@example.com` / `demo123`
- Admin: `admin@example.com` / `admin123`

## Health Checks

Each service provides a health check endpoint:
- Gateway: `GET /health`
- Auth Service: `GET /health`
- Document Service: `GET /health`
- LLM Service: `GET /health`
- Analytics Service: `GET /health`
- Storage Service: `GET /health`

## Scaling

The microservices architecture allows for independent scaling:
- Gateway: Scale based on API request volume
- Document Service: Scale based on document processing load
- LLM Service: Scale based on LLM usage patterns
- Analytics Service: Scale based on data collection volume

## Security

- JWT-based authentication across all services
- Service-to-service communication over private network
- Input validation and sanitization
- Rate limiting at gateway level

## Monitoring and Logging

- Centralized logging through Docker
- Health check endpoints for each service
- Performance metrics collected by analytics service
- Structured logging with request tracing

## Troubleshooting

### Common Issues:
1. **Service connectivity**: Ensure services are on the same network
2. **Database initialization**: Services automatically create tables on startup
3. **LLM connectivity**: Verify LLM service configuration in LLM_MODE
4. **File permissions**: Ensure data volumes have proper permissions

### Checking Service Status:
```bash
docker-compose -f docker-compose.microservices.yml ps
docker-compose -f docker-compose.microservices.yml logs [service-name]
```

## Development

### Adding New Services:
1. Create new service directory with Dockerfile, requirements.txt, and main.py
2. Update docker-compose.microservices.yml with new service
3. Add routing rules to API Gateway
4. Update health check and initialization logic

### Testing Changes:
1. Make changes to your service
2. Rebuild with: `docker-compose -f docker-compose.microservices.yml build [service-name]`
3. Restart service: `docker-compose -f docker-compose.microservices.yml up -d [service-name]`

## Benefits of Microservices Architecture

1. **Scalability**: Individual components can be scaled independently
2. **Fault Isolation**: Failure in one service doesn't bring down the entire system
3. **Technology Flexibility**: Each service can use different technology stacks
4. **Team Development**: Different teams can work on different services
5. **Deployment Flexibility**: Services can be deployed independently
6. **Maintainability**: Smaller, focused codebases are easier to maintain
7. **Resilience**: Better fault tolerance and recovery capabilities