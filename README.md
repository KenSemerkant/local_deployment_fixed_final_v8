# AI Financial Analyst - Local Deployment Setup Guide

This guide provides instructions for setting up and running the AI Financial Analyst solution locally for demonstration purposes.

## Prerequisites

- Docker and Docker Compose installed on your machine
- At least 4GB of available RAM
- At least 2GB of free disk space

## Quick Start

1. Clone or download this repository to your local machine
2. Navigate to the local_deployment directory
3. Create a `.env` file (optional, for OpenAI integration)
4. Start the application with Docker Compose

```bash
# Navigate to the local_deployment directory
cd financial_analyst_project/local_deployment

# Create .env file (optional)
# echo "OPENAI_API_KEY=your_openai_api_key" > .env

# Start the application
docker-compose up -d

# View logs (optional)
docker-compose logs -f
```

5. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - MinIO Console: http://localhost:9001 (login: minioadmin/minioadmin)

## Default Credentials

The application comes with a pre-configured demo user:
- Email: demo@example.com
- Password: demo123

You can also register a new user through the application interface.

## Configuration Options

The application can be configured using environment variables in a `.env` file:

```
# LLM Configuration
LLM_MODE=mock           # Use 'mock' for demo mode or 'openai' for real API
OPENAI_API_KEY=         # Your OpenAI API key (required if LLM_MODE=openai)
MOCK_DELAY=2            # Simulated processing delay in seconds for mock mode

# Security
JWT_SECRET=custom-secret-key  # Custom JWT secret for token generation
```

## Architecture Overview

The local deployment consists of three main services:

1. **Backend (FastAPI)**: Provides the API for document processing, analysis, and user management
2. **Frontend (React)**: Provides the user interface
3. **MinIO**: S3-compatible storage for documents and exports

All services run in Docker containers and communicate over a Docker network.

### Backend Module Structure

The backend has been refactored into a modular architecture for better maintainability and scalability:

#### Core Modules

- **`app.py`** - Main FastAPI application with route definitions and middleware setup
- **`models.py`** - SQLAlchemy database models (User, Document, AnalysisResult, QASession, Question)
- **`schemas.py`** - Pydantic models for request/response validation and serialization
- **`config.py`** - Configuration management, environment variables, and service initialization
- **`auth.py`** - Authentication utilities and user session management
- **`utils.py`** - Database operations and utility functions
- **`background_tasks.py`** - Asynchronous document processing tasks
- **`llm_integration.py`** - LLM service integration for document analysis and Q&A

#### Module Responsibilities

**models.py**
- Database schema definitions
- SQLAlchemy ORM models
- Table relationships and constraints

**schemas.py**
- API request/response models
- Data validation schemas
- Type definitions for API contracts

**config.py**
- Environment variable management
- Database connection setup
- MinIO client initialization
- Directory structure creation

**auth.py**
- User authentication and authorization
- JWT token handling
- Session management dependencies

**utils.py**
- CRUD operations for database entities
- File management utilities
- Data cleanup and deletion functions

**background_tasks.py**
- Document processing workflows
- Asynchronous task management
- Status tracking and error handling

**app.py**
- FastAPI application setup
- Route definitions and endpoints
- Middleware configuration
- CORS and security settings

#### Benefits of Modular Architecture

1. **Separation of Concerns**: Each module has a specific responsibility
2. **Maintainability**: Code is easier to find, understand, and modify
3. **Reusability**: Functions can be imported and reused across modules
4. **Testing**: Individual modules can be tested in isolation
5. **Scalability**: New features can be added without cluttering existing code
6. **Code Organization**: Related functionality is grouped together

#### Import Structure

```python
# Example of clean imports in app.py
from models import User, Document, AnalysisResult
from schemas import UserCreate, DocumentResponse
from config import engine, SessionLocal, STORAGE_PATH
from auth import get_current_user, get_db
from utils import create_user, get_document_by_id
from background_tasks import process_document_task
```

This modular approach makes the codebase more professional, maintainable, and easier to extend with new features.

## Testing the Application

1. **Login**: Use the demo credentials or register a new user
2. **Upload Document**: Upload a financial PDF document from the dashboard
3. **View Analysis**: Once processing is complete, view the document summary and key figures
4. **Ask Questions**: Use the Q&A tab to ask questions about the document
5. **Export Results**: Export the analysis as CSV or TXT

## Troubleshooting

- **Services not starting**: Check Docker logs with `docker-compose logs`
- **Upload failures**: Ensure MinIO is running properly
- **Processing errors**: Check backend logs for specific error messages

## Limitations

The local deployment has some limitations compared to the full cloud deployment:

1. **Performance**: Limited by local machine resources
2. **LLM Capabilities**: When using mock mode, responses are pre-generated
3. **Scalability**: Not designed for processing large volumes of documents
4. **Security**: Simplified for demonstration purposes

## Extending the Application

To use real OpenAI API integration:

1. Obtain an API key from OpenAI
2. Create a `.env` file with:
   ```
   LLM_MODE=openai
   OPENAI_API_KEY=your_api_key_here
   ```
3. Restart the application with `docker-compose down && docker-compose up -d`

## Data Persistence

All data is stored in the `./data` directory, which is mounted as a volume in the Docker containers. This includes:

- SQLite database
- Uploaded documents
- Generated analysis results
- Vector embeddings for Q&A

To reset all data, stop the application and delete the `./data` directory.
