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
    # Allow all origins for now - can restrict in production later
    return ["*"]


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
    
    # Configure CORS - allow all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # Must be False when using wildcard origins
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
