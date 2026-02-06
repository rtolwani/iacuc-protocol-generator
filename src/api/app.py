"""
FastAPI Application Factory.

Creates and configures the IACUC Protocol Generator API.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.review import router as review_router
from src.api.routes.protocols import router as protocols_router


def get_allowed_origins() -> list[str]:
    """
    Get list of allowed CORS origins based on environment.
    """
    # Always allow localhost for development
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # Add Render frontend URL (deployed)
    origins.extend([
        "https://iacuc-protocol-frontend.onrender.com",
        "https://iacuc-protocol-generator.onrender.com",
    ])
    
    # Add any custom domain from environment
    custom_origin = os.getenv("FRONTEND_URL")
    if custom_origin:
        origins.append(custom_origin)
    
    # In development, allow all origins
    if os.getenv("ENVIRONMENT") != "production":
        origins.append("*")
    
    return origins


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI app.
    """
    app = FastAPI(
        title="IACUC Protocol Generator API",
        description="AI-powered IACUC protocol generation with human-in-the-loop review",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Configure CORS with allowed origins
    allowed_origins = get_allowed_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(review_router, prefix="/api/v1")
    app.include_router(protocols_router, prefix="/api/v1")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": "1.0.0"}
    
    return app


# Create default app instance
app = create_app()


# Export
__all__ = ["create_app", "app"]
