"""
FastAPI main application.
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import settings
from .database import create_tables
from .api.v1 import auth, files, analysis, data, labels, users

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Chime Dashboard API",
    description="奇美食品客服語音分析系統 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    # Clean up errors to remove non-serializable objects
    clean_errors = []
    for error in exc.errors():
        clean_error = {
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", "")
        }
        # Only include input if it's serializable
        if "input" in error and error["input"] is not None:
            try:
                # Test if input is JSON serializable
                import json
                json.dumps(error["input"])
                clean_error["input"] = error["input"]
            except (TypeError, ValueError):
                # Skip non-serializable inputs
                pass
        clean_errors.append(clean_error)
    
    logger.error(f"Validation error: {clean_errors}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": clean_errors}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("Starting Chime Dashboard API...")
    
    # Create database tables
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    logger.info("Chime Dashboard API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down Chime Dashboard API...")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Chime Dashboard API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["認證"])
app.include_router(users.router, prefix="/api/users", tags=["用戶管理"])
app.include_router(files.router, prefix="/api/files", tags=["文件管理"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["AI分析"])
app.include_router(data.router, prefix="/api/data", tags=["數據查詢"])
app.include_router(labels.router, prefix="/api/labels", tags=["標籤管理"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )