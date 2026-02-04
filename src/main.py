"""
IACUC Protocol Generator - Main Application Entry Point

A multi-agent AI system for generating IACUC protocol drafts.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Runs startup and shutdown logic.
    """
    # Startup
    print(f"Starting IACUC Protocol Generator in {settings.environment} mode")
    print(f"API Keys configured: {settings.validate_api_keys()}")

    yield

    # Shutdown
    print("Shutting down IACUC Protocol Generator")


# Create FastAPI application
app = FastAPI(
    title="IACUC Protocol Generator",
    description="Multi-agent AI system for generating IACUC protocol drafts",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns basic status information about the application.
    """
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "0.1.0",
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "IACUC Protocol Generator",
        "version": "0.1.0",
        "description": "Multi-agent AI system for IACUC protocol generation",
        "docs": "/docs",
        "health": "/health",
    }


# Import and include routers
from src.api.routes import protocols, review
app.include_router(protocols.router, prefix="/api/v1", tags=["protocols"])
app.include_router(review.router, prefix="/api/v1", tags=["review"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
