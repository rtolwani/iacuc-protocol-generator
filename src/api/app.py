"""
FastAPI Application Factory.

Creates and configures the IACUC Protocol Generator API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.review import router as review_router


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
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(review_router, prefix="/api/v1")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": "1.0.0"}
    
    return app


# Create default app instance
app = create_app()


# Export
__all__ = ["create_app", "app"]
