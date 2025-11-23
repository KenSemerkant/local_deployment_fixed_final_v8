# AI Financial Analyst - Local Deployment

## Project Overview

The AI Financial Analyst is a comprehensive web application designed for analyzing financial documents such as 10-K and 10-Q filings. It provides intelligent document analysis, key figure extraction, and interactive Q&A capabilities using large language models (LLMs). The application includes both frontend and backend components, with support for local deployment using Docker Compose.

### Key Features

- **Document Upload & Analysis**: Supports PDF document uploads with intelligent financial analysis
- **Key Figure Extraction**: Automatically identifies and extracts important financial metrics
- **Interactive Q&A**: Allows users to ask questions about document content with source citations
- **Export Functionality**: Exports analysis results as CSV files
- **Multi-LLM Support**: Supports various LLM providers including OpenAI, Ollama, LM Studio, and mock responses
- **User Management**: Registration, authentication, and admin capabilities
- **Analytics & Monitoring**: Tracks usage, performance, and user satisfaction metrics
- **Admin Dashboard**: Administrative interface for managing users and system configuration

### Technologies Used

- **Backend**: Python with FastAPI framework
- **Frontend**: React.js with TypeScript
- **Database**: SQLite (local deployment)
- **Storage**: MinIO (S3-compatible storage)
- **Authentication**: JWT-based authentication
- **LLM Integration**: OpenAI-compatible API, Ollama, LM Studio
- **Containerization**: Docker and Docker Compose
- **Document Processing**: LangChain and LangGraph

## Architecture

The application follows a microservices architecture adapted for local deployment:

1. **Frontend Container**: React.js interface served via Nginx
2. **Backend Container**: FastAPI service with all business logic
3. **MinIO Container**: S3-compatible storage for documents
4. **LLM Service**: Configurable to use OpenAI, Ollama, LM Studio, or mock responses

### Key Components

- **Models**: SQLAlchemy ORM models for User, Document, AnalysisResult, QASession, Question, etc.
- **Schemas**: Pydantic models for API request/response validation
- **Auth Module**: JWT-based authentication and authorization
- **LLM Integration**: Flexible LLM vendor support with caching
- **Background Tasks**: Asynchronous document processing with cancellation support
- **Analytics**: Comprehensive tracking of user activity, token usage, performance, and satisfaction

## Building and Running

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB of available RAM (8GB+ recommended)
- At least 2GB of free disk space

### Quick Start

1. **Clone or download** the repository to your local machine
2. **Navigate to the project directory**:
   ```bash
   cd /Users/kadirs/Dev/local_deployment_fixed_final_v8
   ```
3. **Start the application**:
   ```bash
   docker-compose up --build -d
   ```
4. **Access the application**:
   - Frontend: [http://localhost:3000](http://localhost:3000)
   - Backend API: [http://localhost:8000](http://localhost:8000)
   - MinIO Console: [http://localhost:9001](http://localhost:9001) (login: minioadmin/minioadmin)

### Default Credentials

The application comes with a pre-configured demo user:
- Email: `demo@example.com`
- Password: `demo123`

Admin user:
- Email: `admin@example.com`
- Password: `admin123`

### Configuration Options

The application uses environment variables for configuration in `docker-compose.yml`:

#### LLM Configuration
- `LLM_MODE`: openai, ollama, or mock (determines LLM integration method)
- `OPENAI_BASE_URL`: API endpoint for OpenAI-compatible services (like LM Studio)
- `OPENAI_API_KEY`: API key for OpenAI or any value for LM Studio
- `OPENAI_MODEL`: Model name to use
- `OLLAMA_BASE_URL`: Ollama endpoint
- `OLLAMA_MODEL`: Ollama model to use

#### Application Settings
- `JWT_SECRET`: Secret for JWT token generation
- `STORAGE_PATH`: Path for persistent storage
- `MOCK_DELAY`: Simulated processing delay for mock mode (default: 2 seconds)

### LM Studio Integration

The application is configured to work with LM Studio using the `deepseek-r1-0528-qwen3-8b-mlx` model by default. To use LM Studio:

1. Install and run LM Studio
2. Download the DeepSeek R1 model
3. Start the local server in LM Studio
4. The docker-compose.yml is already configured to connect to LM Studio at `http://host.docker.internal:1234/v1`

### Ollama Integration

To switch to Ollama:

1. Install Ollama
2. Pull the required model: `ollama pull gemma3:27b`
3. Update docker-compose.yml to set:
   ```yaml
   - LLM_MODE=ollama
   - OLLAMA_MODEL=gemma3:27b
   ```

## Development Conventions

### Backend Structure

The backend follows a modular architecture with the following key modules:

- **app.py**: Main FastAPI application with route definitions
- **models.py**: SQLAlchemy database models
- **schemas.py**: Pydantic request/response schemas
- **auth.py**: Authentication utilities
- **config.py**: Configuration management
- **utils.py**: Utility functions and database operations
- **llm_integration.py**: LLM service integration
- **background_tasks.py**: Asynchronous document processing
- **analytics.py**: Analytics tracking and reporting

### API Endpoints

The application provides a comprehensive REST API:

- **Authentication**: `/token`, `/users`
- **Documents**: `/documents`, `/documents/{id}`, `/documents/{id}/download`
- **Analysis**: `/documents/{id}/analysis`, `/documents/{id}/ask`
- **Q&A**: `/documents/{id}/questions`
- **Export**: `/documents/{id}/export`
- **LLM Configuration**: `/llm/status`, `/llm/mode`
- **Admin**: `/admin/users`, `/admin/analytics/*`, `/admin/storage/*`

### Frontend Structure

The frontend is built with React and includes:

- **Document Upload**: Drag-and-drop interface for PDF uploads
- **Document Analysis Dashboard**: Summary and key figures display
- **Q&A Interface**: Interactive chat-like interface for asking questions
- **Export Functionality**: CSV export of analysis results
- **Admin Panel**: User management and system configuration

## Data Persistence

All data is stored in the `./data` directory, which is mounted as a volume:

- SQLite database files
- Uploaded documents
- Generated analysis results
- Vector databases for Q&A functionality
- Analytics and performance metrics

To reset all data, stop the application and delete the data directory:
```bash
docker-compose down -v
rm -rf ./data
```

## Testing

The application can be tested by:
1. Logging in with demo credentials
2. Uploading a financial PDF document
3. Viewing the document analysis
4. Asking questions about the document
5. Exporting results as CSV

## Troubleshooting

- **Services not starting**: Check Docker logs with `docker-compose logs`
- **Upload failures**: Verify MinIO is running properly
- **Processing errors**: Check backend logs for specific error messages
- **LLM connection**: Verify the LLM service is running and accessible
- **Performance issues**: Check system resource availability

## Limitations

- Local deployment has limited scalability compared to cloud solutions
- Performance depends on local hardware capabilities
- Data persistence is limited to the local machine
- Security implementation is simplified for demonstration

## Extending the Application

The modular design allows for easy extension:

- New LLM providers can be integrated in `llm_integration.py`
- Additional analytics can be tracked using the analytics module
- New document types can be supported by extending the processing pipeline
- Additional export formats can be added to the export endpoints