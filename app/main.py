from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import uvicorn
import time

from app.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import (
    BaseAPIException, 
    DocumentNotFoundError, 
    InvalidQueryError, 
    ScraperError, 
    OpenAIError
)
from app.api.errors import (
    validation_exception_handler,
    api_exception_handler,
    document_not_found_handler,
    invalid_query_handler,
    scraper_error_handler,
    openai_error_handler,
    general_exception_handler
)
from app.api.routes import search, documents

# Get settings
settings = get_settings()

# Setup logging
logger = setup_logging(name="bpk_api", level="INFO", json_format=True)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for searching and retrieving legal documents from peraturan.bpk.go.id",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify the allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(BaseAPIException, api_exception_handler)
app.add_exception_handler(DocumentNotFoundError, document_not_found_handler)
app.add_exception_handler(InvalidQueryError, invalid_query_handler)
app.add_exception_handler(ScraperError, scraper_error_handler)
app.add_exception_handler(OpenAIError, openai_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Add logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request information."""
    start_time = time.time()
    
    # Get request details
    method = request.method
    url = request.url.path
    query_params = str(request.query_params)
    client_host = request.client.host if request.client else "unknown"
    
    # Log the request
    logger.info(
        f"Request: {method} {url}",
        extra={
            "method": method,
            "url": url,
            "query_params": query_params,
            "client_host": client_host
        }
    )
    
    # Process the request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log the response
    logger.info(
        f"Response: {response.status_code} in {process_time:.4f}s",
        extra={
            "status_code": response.status_code,
            "process_time": process_time
        }
    )
    
    return response

# Include API routes
app.include_router(search.router, prefix=settings.API_V1_STR)
app.include_router(documents.router, prefix=settings.API_V1_STR)

# Add root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "description": "API for searching and retrieving legal documents from peraturan.bpk.go.id",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "api_prefix": settings.API_V1_STR
    }

# Add health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }

# Run the application if executed directly
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)