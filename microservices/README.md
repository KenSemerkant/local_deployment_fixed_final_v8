# AI Financial Analyst - Microservices Architecture

This project implements a microservices architecture for the AI Financial Analyst application using **Clean Architecture** principles. Each service is independently deployable and follows domain-driven design patterns.

## 🏗️ Architecture Overview

### **Clean Architecture Implementation**

Each microservice follows the Clean Architecture pattern with clear separation of concerns:

```
📁 service-name/
├── 📁 domain/           # Business entities and rules
│   ├── entities.py      # Domain entities
│   └── repositories.py  # Repository interfaces
├── 📁 application/      # Use cases and business logic
│   ├── use_cases.py     # Application use cases
│   └── schemas.py       # API schemas
├── 📁 infrastructure/   # External concerns
│   ├── database.py      # Database configuration
│   ├── repositories.py  # Repository implementations
│   └── auth.py          # Authentication utilities
├── app.py              # FastAPI application
├── Dockerfile          # Container configuration
└── requirements.txt    # Dependencies
```

### **Microservices Architecture**

```mermaid
graph TB
    Client[Frontend Client] --> Gateway[API Gateway :8000]
    
    Gateway --> UserSvc[User Service :8001]
    Gateway --> DocSvc[Document Service :8002]
    Gateway --> AnalysisSvc[Analysis Service :8003]
    Gateway --> AnalyticsSvc[Analytics Service :8004]
    Gateway --> StorageSvc[Storage Service :8005]
    
    DocSvc --> MinIO[MinIO Storage]
    DocSvc --> UserSvc
    AnalysisSvc --> DocSvc
    AnalysisSvc --> UserSvc
    AnalyticsSvc --> UserSvc
    StorageSvc --> MinIO
    StorageSvc --> UserSvc
    
    UserSvc --> UserDB[(User Database)]
    DocSvc --> DocDB[(Document Database)]
    AnalysisSvc --> AnalysisDB[(Analysis Database)]
    AnalyticsSvc --> AnalyticsDB[(Analytics Database)]
```

## 🚀 Services Overview

### **1. API Gateway (Port 8000)**
- **Purpose**: Single entry point for all client requests
- **Responsibilities**:
  - Request routing to appropriate services
  - Authentication and authorization
  - Cross-cutting concerns (CORS, logging)
  - Load balancing and circuit breaking

### **2. User Service (Port 8001)**
- **Purpose**: User management and authentication
- **Responsibilities**:
  - User registration and login
  - JWT token management
  - Admin user operations
  - User profile management

### **3. Document Service (Port 8002)**
- **Purpose**: Document upload and metadata management
- **Responsibilities**:
  - File upload and storage
  - Document metadata management
  - File access control
  - Integration with storage service

### **4. Analysis Service (Port 8003)**
- **Purpose**: Document analysis and Q&A functionality
- **Responsibilities**:
  - Document processing and analysis
  - LLM integration
  - Question answering
  - Analysis result management

### **5. Analytics Service (Port 8004)**
- **Purpose**: Analytics and reporting
- **Responsibilities**:
  - Event tracking
  - Performance metrics
  - User feedback collection
  - Analytics reporting

### **6. Storage Service (Port 8005)**
- **Purpose**: File storage and management
- **Responsibilities**:
  - MinIO integration
  - File operations (upload, download, delete)
  - Storage quota management
  - File cleanup operations

## 🛠️ Technology Stack

### **Core Technologies**
- **FastAPI**: Web framework for building APIs
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation and serialization
- **Docker**: Containerization
- **MinIO**: Object storage

### **Authentication & Security**
- **JWT**: JSON Web Tokens for authentication
- **Passlib**: Password hashing
- **CORS**: Cross-origin resource sharing

### **Databases**
- **SQLite**: Lightweight database for each service
- **MinIO**: Object storage for files

## 🚀 Quick Start

### **Prerequisites**
- Docker and Docker Compose
- Python 3.9+ (for local development)
- Git

### **1. Clone and Setup**
```bash
git clone <repository-url>
cd microservices
```

### **2. Build and Deploy**
```bash
# Make the script executable
chmod +x build-and-deploy.sh

# Build and deploy all services
./build-and-deploy.sh
```

### **3. Access the Application**
- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **MinIO Console**: http://localhost:9001

### **Default Credentials**
- **Demo User**: demo@example.com / demo123
- **Admin User**: admin@example.com / admin123

## 📊 Service Communication

### **Synchronous Communication**
- HTTP/REST APIs between services
- API Gateway routes requests to appropriate services
- Services communicate via HTTP clients (httpx)

### **Authentication Flow**
1. Client authenticates with User Service via API Gateway
2. User Service returns JWT token
3. API Gateway validates token for subsequent requests
4. User information passed to services via headers

### **Data Consistency**
- Each service owns its data
- No direct database access between services
- Eventual consistency for cross-service operations

## 🔧 Development

### **Local Development Setup**
```bash
# Install dependencies for a service
cd user-service
pip install -r requirements.txt

# Run service locally
python app.py
```

### **Adding a New Service**
1. Create service directory with clean architecture structure
2. Implement domain entities and repositories
3. Create application use cases
4. Build infrastructure layer
5. Add service to docker-compose.yml
6. Update API Gateway routing

### **Testing**
```bash
# Test individual service
curl http://localhost:8001/health

# Test via API Gateway
curl http://localhost:8000/health
```

## 📈 Monitoring and Observability

### **Health Checks**
Each service provides a `/health` endpoint:
- **Gateway**: http://localhost:8000/health
- **User Service**: http://localhost:8001/health
- **Document Service**: http://localhost:8002/health
- **Analysis Service**: http://localhost:8003/health
- **Analytics Service**: http://localhost:8004/health
- **Storage Service**: http://localhost:8005/health

### **Logging**
- Structured logging with Python logging
- Service-specific log levels
- Centralized logging via Docker Compose

### **Service Discovery**
- Docker Compose networking
- Environment variable configuration
- Health check endpoints

## 🔒 Security

### **Authentication**
- JWT-based authentication
- Token validation at API Gateway
- User context propagation via headers

### **Authorization**
- Role-based access control (admin/user)
- Service-level authorization checks
- Resource ownership validation

### **Data Protection**
- Password hashing with bcrypt
- Secure token generation
- HTTPS ready (configure reverse proxy)

## 🚀 Deployment

### **Production Deployment**
1. **Container Registry**: Push images to registry
2. **Orchestration**: Use Kubernetes or Docker Swarm
3. **Load Balancing**: Configure external load balancer
4. **Database**: Use managed database services
5. **Storage**: Use cloud object storage
6. **Monitoring**: Add APM and logging solutions

### **Environment Configuration**
```bash
# User Service
DATABASE_URL=postgresql://user:pass@host:5432/users
JWT_SECRET_KEY=your-secret-key

# Document Service
MINIO_ENDPOINT=minio.example.com:9000
USER_SERVICE_URL=http://user-service:8001

# Analysis Service
OPENAI_API_KEY=your-openai-key
DOCUMENT_SERVICE_URL=http://document-service:8002
```

## 🔄 Migration from Monolith

This microservices architecture is designed to replace the monolithic backend while maintaining API compatibility:

1. **API Gateway** maintains existing endpoints
2. **Database Migration** scripts provided for data migration
3. **Gradual Migration** possible service by service
4. **Backward Compatibility** ensured during transition

## 📚 Additional Resources

- [Clean Architecture Principles](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Microservices Patterns](https://microservices.io/patterns/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)

## 🤝 Contributing

1. Follow clean architecture principles
2. Maintain service independence
3. Add comprehensive tests
4. Update documentation
5. Follow semantic versioning
