"""Root ASGI entry point — run the backend with: uvicorn main:app --reload"""

from src.weather_app.main import app  # noqa: F401

__all__ = ["app"]
