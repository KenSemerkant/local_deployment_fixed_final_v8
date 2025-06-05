# AI Financial Analyst - Local Deployment Architecture

This document outlines the architecture for local deployment of the AI Financial Analyst solution, designed for demonstration purposes on a laptop or desktop computer.

## Architecture Overview

The local deployment architecture adapts the cloud-based microservices design to run in Docker containers on a local machine. The key differences from the AWS deployment are:

1. **Container Orchestration**: Docker Compose instead of AWS ECS/Fargate
2. **Data Storage**: Local file system and SQLite instead of S3 and DynamoDB
3. **Authentication**: Simplified JWT-based auth instead of Amazon Cognito
4. **LLM Integration**: Configurable to use either OpenAI API or mock responses
5. **API Gateway**: Direct service access instead of AWS API Gateway

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Docker Compose Network                       │
│                                                                     │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐    │
│  │  Frontend   │     │   Backend   │     │  Document Storage   │    │
│  │  Container  │────▶│  Container  │────▶│      Container      │    │
│  │  (React)    │     │  (FastAPI)  │     │  (MinIO/S3 Compat)  │    │
│  └─────────────┘     └─────────────┘     └─────────────────────┘    │
│         │                   │                       │               │
│         │                   │                       │               │
│         ▼                   ▼                       ▼               │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐    │
│  │    Nginx    │     │  Database   │     │   LLM Service       │    │
│  │  Container  │     │  Container  │     │     Container       │    │
│  │  (Reverse   │     │  (SQLite)   │     │  (OpenAI or Mock)   │    │
│  │   Proxy)    │     │             │     │                     │    │
│  └─────────────┘     └─────────────┘     └─────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Frontend Container

- **Technology**: React.js with TypeScript
- **Purpose**: Provides the user interface for the application
- **Modifications for Local**:
  - Configuration to connect to local backend services
  - Environment variables for local development
  - Build optimized for local serving

### 2. Backend Container

- **Technology**: Python with FastAPI
- **Purpose**: Unified API service combining all microservices
- **Modifications for Local**:
  - Consolidated microservices into a monolithic application
  - Simplified authentication with JWT
  - Direct integration with SQLite and local file system
  - Configurable LLM integration

### 3. Document Storage Container

- **Technology**: MinIO (S3-compatible storage)
- **Purpose**: Stores uploaded documents and generated exports
- **Modifications for Local**:
  - Simplified configuration for local use
  - Persistent volume for data storage

### 4. Database Container

- **Technology**: SQLite with persistent volume
- **Purpose**: Stores user data, document metadata, and analysis results
- **Modifications for Local**:
  - Simplified schema for demonstration
  - Pre-populated with sample data

### 5. LLM Service Container

- **Technology**: Python service with OpenAI SDK or mock implementation
- **Purpose**: Provides LLM capabilities for document analysis
- **Modifications for Local**:
  - Configurable to use OpenAI API or mock responses
  - Caching for improved performance and reduced API calls

### 6. Nginx Container

- **Technology**: Nginx web server
- **Purpose**: Serves as reverse proxy and static file server
- **Modifications for Local**:
  - Configuration for routing to backend and frontend
  - CORS handling for local development

## Data Flow

1. **User Authentication**:
   - User logs in through the frontend
   - Backend validates credentials and issues JWT token
   - Frontend stores token for subsequent requests

2. **Document Upload**:
   - User uploads document through frontend
   - Backend receives file and stores in MinIO
   - Document metadata is stored in SQLite

3. **Document Processing**:
   - Backend processes document using LangChain and LangGraph
   - LLM service provides text analysis capabilities
   - Results are stored in SQLite and MinIO

4. **Document Analysis**:
   - User views document analysis in frontend
   - Backend retrieves analysis results from SQLite
   - Frontend displays summary, key figures, and enables Q&A

5. **Interactive Q&A**:
   - User asks questions about document
   - Backend uses LLM service to generate answers
   - Results are displayed in frontend

6. **Export**:
   - User requests export of analysis
   - Backend generates export file and stores in MinIO
   - Frontend provides download link

## Configuration

The local deployment uses environment variables for configuration, with sensible defaults for demonstration purposes:

- `LLM_MODE`: `openai` or `mock` (determines LLM integration method)
- `OPENAI_API_KEY`: OpenAI API key (required if `LLM_MODE=openai`)
- `STORAGE_PATH`: Path for persistent storage
- `JWT_SECRET`: Secret for JWT token generation
- `MOCK_DELAY`: Simulated processing delay for mock mode

## Limitations

The local deployment has some limitations compared to the full AWS deployment:

1. **Scalability**: Limited to local machine resources
2. **Security**: Simplified for demonstration purposes
3. **Persistence**: Data persists only on the local machine
4. **LLM Capabilities**: Limited by API access or mock implementation

These limitations are acceptable for demonstration purposes but should be considered if adapting for production use.
