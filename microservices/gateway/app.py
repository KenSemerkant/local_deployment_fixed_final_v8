"""
API Gateway for the AI Financial Analyst microservices.
Routes requests to appropriate services and handles cross-cutting concerns.
"""

import os
import httpx
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service URLs from environment
SERVICE_URLS = {
    "user": os.getenv("USER_SERVICE_URL", "http://user-service:8001"),
    "document": os.getenv("DOCUMENT_SERVICE_URL", "http://document-service:8002"),
    "analysis": os.getenv("ANALYSIS_SERVICE_URL", "http://analysis-service:8003"),
    "analytics": os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8004"),
    "storage": os.getenv("STORAGE_SERVICE_URL", "http://storage-service:8005"),
}

# FastAPI app
app = FastAPI(title="AI Financial Analyst API Gateway", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# HTTP client for service communication
client = httpx.AsyncClient(timeout=30.0)


class ServiceRouter:
    """Routes requests to appropriate microservices."""
    
    def __init__(self):
        self.routes = {
            # Authentication routes
            "/token": "user",
            "/register": "user",
            "/users/me": "user",
            
            # Admin user management routes
            "/admin/users": "user",
            
            # Document routes
            "/documents": "document",
            "/documents/": "document",
            
            # Analysis routes
            "/analysis": "analysis",
            "/questions": "analysis",
            "/llm": "analysis",
            
            # Analytics routes (temporarily routed to user-service)
            "/admin/analytics": "user",
            "/feedback": "user",
            
            # Storage routes
            "/admin/storage": "storage",
        }
    
    def get_service_for_path(self, path: str) -> str:
        """Determine which service should handle the request."""
        for route_prefix, service in self.routes.items():
            if path.startswith(route_prefix):
                return service
        
        # Default to user service for unmatched routes
        return "user"


router = ServiceRouter()


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token with user service."""
    try:
        response = await client.get(
            f"{SERVICE_URLS['user']}/verify-token",
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Token verification failed")


async def forward_request(request: Request, service: str) -> StreamingResponse:
    """Forward request to the appropriate microservice."""
    service_url = SERVICE_URLS.get(service)
    if not service_url:
        raise HTTPException(status_code=500, detail=f"Service {service} not configured")
    
    # Build target URL
    target_url = f"{service_url}{request.url.path}"
    if request.url.query:
        target_url += f"?{request.url.query}"
    
    # Prepare headers (exclude host header)
    headers = dict(request.headers)
    headers.pop("host", None)
    
    # Get request body
    body = await request.body()
    
    try:
        # Forward request to microservice
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            follow_redirects=True
        )
        
        # Return response
        return StreamingResponse(
            iter([response.content]),
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type")
        )
        
    except Exception as e:
        logger.error(f"Error forwarding request to {service}: {e}")
        raise HTTPException(status_code=500, detail="Service unavailable")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Gateway health check and service status."""
    status = {
        "gateway": "healthy",
        "services": {}
    }
    
    # Check each service
    for service_name, service_url in SERVICE_URLS.items():
        try:
            response = await client.get(f"{service_url}/health", timeout=5.0)
            status["services"][service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            status["services"][service_name] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    # Determine overall status
    unhealthy_services = [name for name, info in status["services"].items() if info["status"] != "healthy"]
    if unhealthy_services:
        status["overall"] = "degraded"
        status["unhealthy_services"] = unhealthy_services
    else:
        status["overall"] = "healthy"
    
    return status


# Public routes (no authentication required)
@app.post("/token")
async def login(request: Request):
    """Login endpoint - forward to user service."""
    return await forward_request(request, "user")


@app.post("/register")
async def register(request: Request):
    """Registration endpoint - forward to user service."""
    return await forward_request(request, "user")


# Protected routes (authentication required)
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def route_request(request: Request, path: str, user: Dict[str, Any] = Depends(verify_token)):
    """Route authenticated requests to appropriate services."""
    service = router.get_service_for_path(f"/{path}")
    
    # Add user info to headers for downstream services
    headers = dict(request.headers)
    headers["X-User-ID"] = str(user.get("id"))
    headers["X-User-Email"] = user.get("email", "")
    headers["X-User-Admin"] = str(user.get("is_admin", False))
    
    # Update request headers
    request._headers = headers
    
    return await forward_request(request, service)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize gateway on startup."""
    logger.info("API Gateway starting up...")
    logger.info(f"Configured services: {list(SERVICE_URLS.keys())}")
    
    # Test connectivity to services
    for service_name, service_url in SERVICE_URLS.items():
        try:
            response = await client.get(f"{service_url}/health", timeout=5.0)
            logger.info(f"✅ {service_name} service is reachable")
        except Exception as e:
            logger.warning(f"⚠️ {service_name} service is not reachable: {e}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    await client.aclose()
    logger.info("API Gateway shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
