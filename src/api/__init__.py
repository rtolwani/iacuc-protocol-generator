"""
IACUC Protocol Generator API.

FastAPI-based REST API for protocol generation and review.
"""

from src.api.app import create_app

__all__ = ["create_app"]
