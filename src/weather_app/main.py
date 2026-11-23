"""
main.py (src/weather_app/main.py) — FastAPI application and routes.

Endpoints
---------
GET /health           — Liveness check
GET /locations        — Simulation city list
GET /thresholds       — Alert threshold constants
GET /weather          — Full weather + forecast + alerts
GET /weather/report   — Same data as a downloadable CSV
"""

import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from .alerts import threshold_summary
from .config import settings
from .service import DEMO_LOCATIONS, get_weather, save_csv_report

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description=(
        "Educational weather forecast and risk-alert API. "
        "Uses Open-Meteo public endpoints — no paid API key required. "
        "Alerts are project defaults, not official warnings."
    ),
)


# ---------------------------------------------------------------------------
# Shared query parameter descriptions (avoid repeating in every route)
# ---------------------------------------------------------------------------
_CITY_Q = Query(
    default="New Delhi",
    min_length=2,
    max_length=100,
    description="City name to look up. Must be at least 2 characters.",
)
_LAT_Q = Query(
    default=None,
    ge=-90.0,
    le=90.0,
    description=(
        "Optional latitude (-90 to 90). "
        "When both latitude and longitude are provided, geocoding is skipped."
    ),
)
_LON_Q = Query(
    default=None,
    ge=-180.0,
    le=180.0,
    description=(
        "Optional longitude (-180 to 180). "
        "When both latitude and longitude are provided, geocoding is skipped."
    ),
)
_SIM_Q = Query(
    default=False,
    description=(
        "Set to true to use deterministic offline simulation data. "
        "Simulation results are clearly labelled and never substituted "
        "silently for a failed live request."
    ),
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get(
    "/health",
    tags=["system"],
    summary="Liveness check",
    response_description="Service name and status.",
)
async def health() -> dict[str, str]:
    """Return `ok` when the API is running. Use this to confirm the server started."""
    return {"status": "ok", "service": settings.app_name, "version": settings.api_version}


@app.get(
    "/locations",
    tags=["weather"],
    summary="Simulation city list",
    response_description="Cities with built-in offline scenarios.",
)
async def locations() -> dict[str, list[str]]:
    """
    Return the city names that have a built-in offline simulation scenario.
    Pass one of these names with `simulation=true` for a fully offline demo.
    """
    return {"locations": list(DEMO_LOCATIONS.keys())}


@app.get(
    "/thresholds",
    tags=["alerts"],
    summary="Alert threshold constants",
    response_description="Current threshold values for all alert categories.",
)
async def thresholds() -> dict:
    """
    Return the numeric thresholds used by the alert engine.
    Useful for understanding why a particular alert was or wasn't triggered.
    """
    return threshold_summary()


@app.get(
    "/weather",
    tags=["weather"],
    summary="Current weather, forecast, and alerts",
    response_description=(
        "Full weather response: location, source, current conditions, "
        "24-hour hourly forecast, 7-day daily forecast, and risk alerts."
    ),
)
async def weather(
    city: str = _CITY_Q,
    latitude: float | None = _LAT_Q,
    longitude: float | None = _LON_Q,
    simulation: bool = _SIM_Q,
) -> dict:
    """
    Fetch current conditions, a 24-hour hourly forecast, a 7-day daily forecast,
    the current US AQI (when available), and risk alerts for the given city.

    **Live mode** (default): geocodes the city name, then fetches from Open-Meteo.
    Missing optional values such as AQI are returned as `null`, never guessed.

    **Simulation mode** (`simulation=true`): returns deterministic offline data
    labelled `source: "simulation"`. Simulation is never used as a silent
    fallback if the live request fails.

    **Error codes**
    - 404: city not found by geocoding
    - 422: invalid query parameter (e.g. city too short, latitude out of range)
    - 502: upstream provider unreachable or returned an error
    """
    try:
        return await get_weather(city, latitude, longitude, simulation)
    except ValueError as exc:
        # City not found — user error, not a server error
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        # Network, timeout, or provider error
        logger.warning("Weather fetch failed for '%s': %s", city, exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get(
    "/weather/report",
    tags=["reports"],
    summary="Download a CSV weather report",
    response_description=(
        "A CSV file containing location metadata, current conditions, "
        "hourly forecast, daily forecast, and triggered alerts."
    ),
)
async def weather_report(
    city: str = _CITY_Q,
    latitude: float | None = _LAT_Q,
    longitude: float | None = _LON_Q,
    simulation: bool = _SIM_Q,
) -> FileResponse:
    """
    Fetch weather data (identical to the `/weather` endpoint) and return it
    as a downloadable CSV file.  A local copy is also saved to `outputs/`.

    **CSV sections** (tidy long format, one measurement per row):
    - `report_info`: location metadata and data source
    - `current`: current-conditions readings with units
    - `hourly`: 24 hourly forecast measurements
    - `daily`: 7 daily forecast measurements
    - `alert`: triggered alert records
    """
    try:
        data = await get_weather(city, latitude, longitude, simulation)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.warning("Weather fetch failed for report '%s': %s", city, exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        path = save_csv_report(data)
    except OSError as exc:
        logger.error("Could not save CSV report: %s", exc)
        raise HTTPException(
            status_code=500, detail="Could not write the CSV report to disk."
        ) from exc

    return FileResponse(
        path=path,
        media_type="text/csv; charset=utf-8",
        filename=path.name,
        headers={"Content-Disposition": f'attachment; filename="{path.name}"'},
    )
