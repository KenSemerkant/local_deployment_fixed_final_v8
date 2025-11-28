from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import asyncio
import logging

# OpenTelemetry tracing setup
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Configure OpenTelemetry
otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://jaeger:4318/v1/traces")
service_name = os.getenv("OTEL_SERVICE_NAME", "gateway")

# Set up the tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Add OTLP span processor
span_processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint=otel_endpoint)
)
trace.get_tracer_provider().add_span_processor(span_processor)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="API Gateway", version="1.0.0")

# Enable tracing for the FastAPI app
FastAPIInstrumentor.instrument_app(app)

# Instrument other libraries
RequestsInstrumentor().instrument()
LoggingInstrumentor().instrument()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service endpoints configuration
SERVICE_ENDPOINTS = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000"),
    "document": os.getenv("DOCUMENT_SERVICE_URL", "http://document-service:8000"),
    "llm": os.getenv("LLM_SERVICE_URL", "http://llm-service:8000"),
    "analytics": os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8000"),
    "storage": os.getenv("STORAGE_SERVICE_URL", "http://storage-service:8000"),
}

# HTTP client for service calls
http_client = httpx.AsyncClient(timeout=30.0)

@app.get("/")
async def root():
    return {"message": "API Gateway", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check for the gateway and downstream services"""
    try:
        # Check that service endpoints are configured
        for service_name, service_url in SERVICE_ENDPOINTS.items():
            try:
                # Make a simple request to each service's health endpoint
                health_url = f"{service_url}/health"
                response = await http_client.get(health_url)
                if response.status_code != 200:
                    logger.warning(f"Health check failed for {service_name} at {health_url}")
            except Exception as e:
                logger.error(f"Could not reach {service_name} at {service_url}: {e}")
        
        return {
            "status": "healthy",
            "services": {name: "available" for name in SERVICE_ENDPOINTS.keys()}
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Gateway health check failed")

# Authentication Service Routes
@app.post("/token")
async def token(request: Request):
    return await forward_request("auth", "/token", request)

@app.post("/users")
async def register_user(request: Request):
    return await forward_request("auth", "/users", request)

@app.get("/users/me")
async def get_current_user(request: Request):
    return await forward_request("auth", "/users/me", request)

# Document Service Routes
@app.post("/documents")
async def upload_document(request: Request):
    return await forward_request("document", "/documents", request)

@app.get("/documents")
async def list_documents(request: Request):
    return await forward_request("document", "/documents", request)

@app.get("/documents/{document_id}")
async def get_document(document_id: int, request: Request):
    return await forward_request("document", f"/documents/{document_id}", request)

@app.delete("/documents/{document_id}")
async def delete_document(document_id: int, request: Request):
    return await forward_request("document", f"/documents/{document_id}", request)

@app.get("/documents/{document_id}/download")
async def download_document(document_id: int, request: Request):
    return await forward_request("document", f"/documents/{document_id}/download", request)

@app.get("/documents/{document_id}/analysis")
async def get_document_analysis(document_id: int, request: Request):
    return await forward_request("document", f"/documents/{document_id}/analysis", request)

@app.post("/documents/{document_id}/ask")
async def ask_document_question(document_id: int, request: Request):
    return await forward_request("document", f"/documents/{document_id}/ask", request)

@app.get("/documents/{document_id}/questions")
async def list_document_questions(document_id: int, request: Request):
    return await forward_request("document", f"/documents/{document_id}/questions", request)

@app.get("/documents/{document_id}/export")
async def export_document_analysis(document_id: int, request: Request):
    return await forward_request("document", f"/documents/{document_id}/export", request)

@app.post("/documents/{document_id}/cancel")
async def cancel_document_processing(document_id: int, request: Request):
    return await forward_request("document", f"/documents/{document_id}/cancel", request)

@app.get("/documents/{document_id}/status")
async def get_document_processing_status(document_id: int, request: Request):
    return await forward_request("document", f"/documents/{document_id}/status", request)

@app.post("/documents/{document_id}/clear-cache")
async def clear_document_cache(document_id: int, request: Request):
    return await forward_request("document", f"/documents/{document_id}/clear-cache", request)

# LLM Service Routes
@app.get("/llm/status")
async def get_llm_status(request: Request):
    return await forward_request("llm", "/status", request)

@app.post("/llm/mode")
async def set_llm_mode(request: Request):
    return await forward_request("llm", "/mode", request)

@app.get("/llm/modes")
async def get_available_llm_modes(request: Request):
    return await forward_request("llm", "/modes", request)

# Analytics Service Routes (Admin only)
@app.get("/admin/users")
async def get_users_admin(request: Request):
    return await forward_request("analytics", "/admin/users", request)

@app.post("/admin/users")
async def create_user_admin(request: Request):
    return await forward_request("analytics", "/admin/users", request)

@app.get("/admin/users/{user_id}")
async def get_user_admin(user_id: int, request: Request):
    return await forward_request("analytics", f"/admin/users/{user_id}", request)

@app.put("/admin/users/{user_id}")
async def update_user_admin(user_id: int, request: Request):
    return await forward_request("analytics", f"/admin/users/{user_id}", request)

@app.delete("/admin/users/{user_id}")
async def delete_user_admin(user_id: int, request: Request):
    return await forward_request("analytics", f"/admin/users/{user_id}", request)

# LLM Configuration endpoints (Admin only)
@app.get("/admin/llm/config")
async def get_llm_config_admin(request: Request):
    logger.info(f"LLM Configuration - Request to /admin/llm/config from {request.client.host}")
    response = await forward_request("llm", "/admin/config", request)
    logger.info(f"LLM Configuration - Response from /admin/llm/config: {response.status_code if hasattr(response, 'status_code') else 'unknown'}")
    return response

@app.post("/admin/llm/config")
async def update_llm_config_admin(request: Request):
    logger.info(f"LLM Configuration - Request to /admin/llm/config from {request.client.host}")
    response = await forward_request("llm", "/admin/config", request)
    logger.info(f"LLM Configuration - Response from /admin/llm/config: {response.status_code if hasattr(response, 'status_code') else 'unknown'}")
    return response

@app.get("/admin/llm/vendors")
async def get_llm_vendors_admin(request: Request):
    logger.info(f"LLM Configuration - Request to /admin/llm/vendors from {request.client.host}")
    response = await forward_request("llm", "/admin/vendors", request)
    logger.info(f"LLM Configuration - Response from /admin/llm/vendors: {response.status_code if hasattr(response, 'status_code') else 'unknown'}")
    return response

@app.get("/admin/llm/models/{vendor}")
async def get_vendor_models_admin(vendor: str, request: Request):
    logger.info(f"LLM Configuration - Request to /admin/llm/models/{vendor} from {request.client.host}")
    response = await forward_request("llm", f"/admin/models/{vendor}", request)
    logger.info(f"LLM Configuration - Response from /admin/llm/models/{vendor}: {response.status_code if hasattr(response, 'status_code') else 'unknown'}")
    return response

@app.post("/admin/llm/test")
async def test_llm_config_admin(request: Request):
    logger.info(f"LLM Configuration - Request to /admin/llm/test from {request.client.host}")
    response = await forward_request("llm", "/admin/test", request)
    logger.info(f"LLM Configuration - Response from /admin/llm/test: {response.status_code if hasattr(response, 'status_code') else 'unknown'}")
    return response

# Storage Management endpoints (Admin only)
@app.get("/admin/storage/overview")
async def get_storage_overview_admin(request: Request):
    return await forward_request("storage", "/admin/overview", request)

@app.get("/admin/storage/users")
async def get_user_storage_admin(request: Request):
    return await forward_request("storage", "/admin/users", request)

@app.post("/admin/storage/cleanup/user/{user_id}")
async def cleanup_user_storage_admin(user_id: int, request: Request):
    return await forward_request("storage", f"/admin/cleanup/user/{user_id}", request)

@app.post("/admin/storage/cleanup/orphaned")
async def cleanup_orphaned_files_admin(request: Request):
    return await forward_request("storage", "/admin/cleanup/orphaned", request)

# Analytics endpoints (Admin only)
@app.get("/admin/analytics/overview")
async def get_analytics_overview_admin(request: Request):
    return await forward_request("analytics", "/admin/overview", request)

@app.get("/admin/analytics/usage-patterns")
async def get_usage_patterns_admin(request: Request):
    return await forward_request("analytics", "/admin/usage-patterns", request)

@app.get("/admin/analytics/tokens")
async def get_token_analytics_admin(request: Request):
    return await forward_request("analytics", "/admin/tokens", request)

@app.get("/admin/analytics/performance")
async def get_performance_analytics_admin(request: Request):
    return await forward_request("analytics", "/admin/performance", request)

@app.get("/admin/analytics/satisfaction")
async def get_user_satisfaction_admin(request: Request):
    return await forward_request("analytics", "/admin/satisfaction", request)

@app.post("/feedback")
async def submit_feedback(request: Request):
    return await forward_request("analytics", "/feedback", request)

@app.post("/admin/clear-all-cache")
async def clear_all_cache_admin(request: Request):
    return await forward_request("llm", "/admin/clear-all-cache", request)

async def forward_request(service_name: str, path: str, original_request: Request):
    """
    Forward the request to the appropriate microservice
    """
    service_url = SERVICE_ENDPOINTS.get(service_name)
    if not service_url:
        raise HTTPException(status_code=502, detail=f"Service {service_name} not available")
    
    target_url = f"{service_url}{path}"
    logger.info(f"Forwarding request to: {target_url}")
    
    # Extract headers and body from the original request
    headers = dict(original_request.headers)
    
    # Remove hop-by-hop headers that shouldn't be forwarded
    headers.pop('host', None)
    headers.pop('connection', None)
    
    # Get the body content
    body = await original_request.body()
    
    # Get query parameters
    params = dict(original_request.query_params)
    
    try:
        # Make the request to the target service
        response = await http_client.request(
            method=original_request.method,
            url=target_url,
            headers=headers,
            params=params,
            content=body
        )
        
        # Return the response from the target service
        return response.json()
    except httpx.RequestError as e:
        logger.error(f"Request to {target_url} failed: {e}")
        raise HTTPException(status_code=502, detail=f"Service {service_name} unavailable")
    except Exception as e:
        logger.error(f"Unexpected error forwarding to {target_url}: {e}")
        raise HTTPException(status_code=500, detail="Gateway error")

# Graceful shutdown
@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)