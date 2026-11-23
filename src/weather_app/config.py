"""
config.py — Application settings.

All tuneable values live here so there is one place to change them.
Environment variables are loaded from a .env file when the server starts.
"""

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load .env automatically so the developer doesn't need to export variables
# manually. If the file doesn't exist, os.getenv() falls back to None.
load_dotenv()


class Settings(BaseModel):
    """Centralised application configuration validated by Pydantic."""

    # -------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------
    app_name: str = "Weather Forecast & Alert API"
    api_version: str = "1.0.0"

    # -------------------------------------------------------------------
    # Caching
    # Responses are stored in-memory for cache_ttl_seconds so that
    # repeated requests for the same city don't hammer the provider.
    # -------------------------------------------------------------------
    cache_ttl_seconds: int = Field(default=600, ge=0)   # 0 = disable cache

    # -------------------------------------------------------------------
    # HTTP behaviour
    # -------------------------------------------------------------------
    request_timeout_seconds: float = Field(default=12.0, gt=0)

    # -------------------------------------------------------------------
    # Optional provider key
    # Open-Meteo does not need a key; this slot is here if the student
    # switches to a provider that requires one (e.g. OpenWeatherMap).
    # NEVER hard-code a real key in this file.
    # -------------------------------------------------------------------
    openweather_api_key: str | None = Field(
        default_factory=lambda: os.getenv("OPENWEATHER_API_KEY")
    )


# Module-level singleton — imported by service.py and main.py
settings = Settings()
