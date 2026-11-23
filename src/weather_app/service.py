"""
service.py — Weather data fetching, normalisation, caching, simulation, and CSV export.

Responsibilities
----------------
1. Geocoding  : city name  → latitude / longitude / timezone
2. Live fetch : Open-Meteo forecast + air-quality APIs (concurrent, async)
3. Simulation : deterministic offline data for 5 preset cities
4. Normalise  : map provider field names to our internal schema
5. Cache      : in-memory TTL cache to avoid redundant API calls
6. CSV export : write a human-readable snapshot to outputs/

External APIs used (all free, no key required)
-----------------------------------------------
- Geocoding  : https://geocoding-api.open-meteo.com/v1/search
- Forecast   : https://api.open-meteo.com/v1/forecast
- Air quality: https://air-quality-api.open-meteo.com/v1/air-quality
"""

from __future__ import annotations

import asyncio
import csv
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from .alerts import build_alerts
from .config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Provider URLs
# ---------------------------------------------------------------------------
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# ---------------------------------------------------------------------------
# In-memory response cache:  key → (stored_at_timestamp, response_dict)
# ---------------------------------------------------------------------------
_cache: dict[str, tuple[float, dict[str, Any]]] = {}

# ---------------------------------------------------------------------------
# Offline simulation scenarios
# Tuple order: latitude, longitude, timezone,
#              rain_chance_pct, base_temp_c, wind_kmh, us_aqi, humidity_pct
# ---------------------------------------------------------------------------
DEMO_LOCATIONS: dict[str, tuple[float, float, str, int, float, int, int, int]] = {
    "New Delhi": (28.6139, 77.2090, "Asia/Kolkata",     42, 31.4, 56, 78,  91),
    "London":    (51.5072, -0.1276,  "Europe/London",   58, 18.2, 24,  8,  78),
    "Tokyo":     (35.6762, 139.6503, "Asia/Tokyo",      22, 27.1, 18, 42,  96),
    "New York":  (40.7128, -74.0060, "America/New_York",76, 24.0, 34, 22,  70),
    "Sydney":    (-33.8688, 151.2093,"Australia/Sydney", 12, 21.7, 17, 11,  60),
}


# ---------------------------------------------------------------------------
# Geocoding
# ---------------------------------------------------------------------------

async def geocode_city(city: str) -> dict[str, Any]:
    """
    Convert a city name into geographic coordinates using the Open-Meteo
    geocoding API.

    Returns a dict with keys: name, country, latitude, longitude, timezone.

    Raises
    ------
    ValueError
        When the provider returns no matches for the city name.
    RuntimeError
        On any network error, timeout, or unexpected response format.
    """
    params = {"name": city.strip(), "count": 1, "language": "en", "format": "json"}
    try:
        async with httpx.AsyncClient(
            timeout=settings.request_timeout_seconds
        ) as client:
            resp = await client.get(GEOCODING_URL, params=params)
            resp.raise_for_status()
            payload = resp.json()
            if not isinstance(payload, dict):
                raise ValueError("Expected a JSON object")
            results = payload.get("results") or []
            if not isinstance(results, list):
                raise ValueError("Expected a results list")
    except httpx.TimeoutException as exc:
        raise RuntimeError(
            f"Geocoding request timed out after {settings.request_timeout_seconds}s. "
            "Check your connection or try again."
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Geocoding API returned HTTP {exc.response.status_code}. "
            "The provider may be temporarily unavailable."
        ) from exc
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Geocoding network error: {exc}") from exc
    except (ValueError, KeyError) as exc:
        raise RuntimeError(
            "Geocoding provider returned an unexpected response format."
        ) from exc

    if not results:
        raise ValueError(
            f"No location found for '{city}'. "
            "Try a larger nearby city, check the spelling, or use simulation mode."
        )

    item = results[0]
    return {
        "name":      item["name"],
        "country":   item.get("country", ""),
        "latitude":  item["latitude"],
        "longitude": item["longitude"],
        "timezone":  item.get("timezone", "UTC"),
    }


# ---------------------------------------------------------------------------
# Live data fetch helpers
# ---------------------------------------------------------------------------

async def _fetch_forecast(
    lat: float, lon: float, tz: str
) -> dict[str, Any]:
    """
    Fetch current conditions + hourly + daily forecast from Open-Meteo.

    Returns the raw provider JSON (not yet normalised).

    Raises RuntimeError on any failure so callers can handle it uniformly.
    """
    params = {
        "latitude":     lat,
        "longitude":    lon,
        "timezone":     tz,
        "forecast_days": 7,
        "hourly": ",".join([
            "temperature_2m",
            "apparent_temperature",
            "precipitation_probability",
            "precipitation",
            "relative_humidity_2m",
            "wind_speed_10m",
            "wind_direction_10m",
            "weather_code",
        ]),
        "daily": ",".join([
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
            "precipitation_sum",
            "weather_code",
        ]),
        "current": ",".join([
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "precipitation",
            "wind_speed_10m",
            "wind_direction_10m",
            "weather_code",
            "is_day",
        ]),
    }
    try:
        async with httpx.AsyncClient(
            timeout=settings.request_timeout_seconds
        ) as client:
            resp = await client.get(FORECAST_URL, params=params)
            resp.raise_for_status()
            payload = resp.json()
            if not isinstance(payload, dict):
                raise ValueError("Expected a JSON object")
            return payload
    except httpx.TimeoutException as exc:
        raise RuntimeError(
            "Forecast request timed out. Check your connection."
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Forecast API returned HTTP {exc.response.status_code}."
        ) from exc
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Forecast network error: {exc}") from exc
    except (ValueError, KeyError) as exc:
        raise RuntimeError(
            "Forecast provider returned an unexpected response format."
        ) from exc


async def _fetch_air_quality(lat: float, lon: float) -> dict[str, Any] | None:
    """
    Fetch hourly US AQI from the Open-Meteo air quality API.

    Returns the raw JSON on success, or None on any failure.
    Air quality is optional — a None return does not block the main response.
    """
    params = {"latitude": lat, "longitude": lon, "hourly": "us_aqi"}
    try:
        async with httpx.AsyncClient(
            timeout=settings.request_timeout_seconds
        ) as client:
            resp = await client.get(AIR_URL, params=params)
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Air quality fetch failed (non-fatal): %s", exc)
        return None


def _extract_current_aqi(
    air_data: dict[str, Any] | None, current_time_str: str
) -> int | None:
    """
    Pull the US AQI value that matches the current observation hour.

    Parameters
    ----------
    air_data : dict or None
        Raw JSON from _fetch_air_quality, or None if the fetch failed.
    current_time_str : str
        The 'time' field from the forecast current block, e.g. "2026-11-24T01:00".

    Returns
    -------
    int or None
        The AQI integer, or None if unavailable.
    """
    if not air_data:
        return None
    try:
        times = air_data["hourly"]["time"]
        values = air_data["hourly"]["us_aqi"]
        # Match the first 13 characters (YYYY-MM-DDTHH) to find the current hour
        prefix = current_time_str[:13]
        for i, t in enumerate(times):
            if str(t).startswith(prefix):
                raw = values[i]
                return int(raw) if raw is not None else None
    except (KeyError, IndexError, TypeError, ValueError):
        pass
    return None


def _normalise_forecast(
    forecast_json: dict[str, Any],
    aqi: int | None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Convert raw Open-Meteo forecast JSON into our internal schema.

    Returns
    -------
    current : dict
        Current-conditions dict with our field names.
    hourly : list[dict]
        24-entry list of hourly records.
    daily : list[dict]
        7-entry list of daily records.
    """
    # --- Current -------------------------------------------------------
    raw_cur = forecast_json.get("current", {})
    current: dict[str, Any] = {
        "time":                     raw_cur.get("time"),
        "temperature_c":            raw_cur.get("temperature_2m"),
        "apparent_temperature_c":   raw_cur.get("apparent_temperature"),
        "relative_humidity_percent":raw_cur.get("relative_humidity_2m"),
        "precipitation_mm":         raw_cur.get("precipitation"),
        # precipitation_probability is NOT in the current block from Open-Meteo;
        # it is filled from the hourly record matching the current observation.
        "precipitation_probability": None,
        "wind_speed_kmh":           raw_cur.get("wind_speed_10m"),
        "wind_direction_degrees":   raw_cur.get("wind_direction_10m"),
        "weather_code":             raw_cur.get("weather_code"),
        "is_day":                   raw_cur.get("is_day"),
        "us_aqi":                   aqi,
    }

    # --- Hourly (24 entries starting at the current observation) -------
    raw_hourly = forecast_json.get("hourly", {})
    h_times   = raw_hourly.get("time", [])
    h_temp    = raw_hourly.get("temperature_2m", [])
    h_rain_p  = raw_hourly.get("precipitation_probability", [])
    h_rain_mm = raw_hourly.get("precipitation", [])
    h_humid   = raw_hourly.get("relative_humidity_2m", [])
    h_wind    = raw_hourly.get("wind_speed_10m", [])
    h_wcode   = raw_hourly.get("weather_code", [])

    # Open-Meteo hourly arrays can start at local midnight, not at "now".
    # Find the current hour so current rain risk and the next-24-hour chart
    # use matching timestamps instead of accidentally showing the morning.
    current_time = str(raw_cur.get("time") or "")[:13]
    start_index = next(
        (i for i, value in enumerate(h_times) if str(value)[:13] == current_time),
        None,
    )
    if start_index is None and current_time:
        start_index = next(
            (i for i, value in enumerate(h_times) if str(value)[:13] >= current_time),
            0,
        )
    if start_index is None:
        start_index = 0

    # Use the rain probability for the same hour as the current observation.
    current["precipitation_probability"] = _safe_get(h_rain_p, start_index)

    hourly: list[dict[str, Any]] = []
    end_index = min(start_index + 24, len(h_times))
    for i in range(start_index, end_index):
        hourly.append({
            "time":                      _safe_get(h_times, i),
            "temperature_c":             _safe_get(h_temp,   i),
            "precipitation_probability": _safe_get(h_rain_p, i),
            "precipitation_mm":          _safe_get(h_rain_mm,i),
            "relative_humidity_percent": _safe_get(h_humid,  i),
            "wind_speed_kmh":            _safe_get(h_wind,   i),
            "weather_code":              _safe_get(h_wcode,  i),
        })

    # --- Daily (7 days) -----------------------------------------------
    raw_daily = forecast_json.get("daily", {})
    d_dates  = raw_daily.get("time", [])
    d_tmax   = raw_daily.get("temperature_2m_max", [])
    d_tmin   = raw_daily.get("temperature_2m_min", [])
    d_rain_p = raw_daily.get("precipitation_probability_max", [])
    d_rain_s = raw_daily.get("precipitation_sum", [])
    d_wcode  = raw_daily.get("weather_code", [])

    daily: list[dict[str, Any]] = []
    for i in range(min(7, len(d_dates))):
        daily.append({
            "date":                        _safe_get(d_dates, i),
            "temperature_max_c":           _safe_get(d_tmax,  i),
            "temperature_min_c":           _safe_get(d_tmin,  i),
            "precipitation_probability_max": _safe_get(d_rain_p, i),
            "precipitation_sum_mm":        _safe_get(d_rain_s, i),
            "weather_code":                _safe_get(d_wcode, i),
        })

    return current, hourly, daily


def _safe_get(lst: list, index: int) -> Any:
    """Return lst[index] or None if the list is too short."""
    try:
        return lst[index]
    except IndexError:
        return None


# ---------------------------------------------------------------------------
# Offline simulation
# ---------------------------------------------------------------------------

def _demo(city: str) -> dict[str, Any]:
    """
    Return a fully-formed weather response dict built from hardcoded data.

    This path is chosen when simulation=True.  It never makes network calls.
    The returned dict is structurally identical to the live response so the
    dashboard and alert engine work without any special-casing.

    The source field is set to "simulation" so it is always distinguishable
    from real data.  It will NEVER be substituted silently for a failed live
    call — that substitution is explicitly forbidden in get_weather().
    """
    # Case-insensitive match; fall back to New Delhi if city not recognised
    matched = next(
        (name for name in DEMO_LOCATIONS if name.casefold() == city.casefold()),
        "New Delhi",
    )
    lat, lon, tz, rain, temp, wind, aqi, humidity = DEMO_LOCATIONS[matched]

    now_str = time.strftime("%Y-%m-%dT%H:00", time.gmtime())

    # Hourly: 24 entries with simple variation so the chart is interesting
    hourly: list[dict[str, Any]] = []
    for i in range(24):
        hourly.append({
            "time":                      f"{now_str}+{i:02d}h",
            "temperature_c":             round(temp + (i % 5 - 2) * 1.2, 1),
            "precipitation_probability": max(0, min(100, rain + (i % 4 - 1) * 9)),
            "precipitation_mm":          2.4 if i % 3 == 0 else 0.0,
            "relative_humidity_percent": max(10, min(100, humidity + (i % 3 - 1) * 3)),
            "wind_speed_kmh":            max(0, wind + (i % 5 - 2) * 4),
            "weather_code":              3,
        })

    # Daily: 7 days
    daily: list[dict[str, Any]] = []
    for i in range(7):
        daily.append({
            "date":                          f"Day {i + 1}",
            "temperature_max_c":             round(temp + i * 0.4, 1),
            "temperature_min_c":             round(temp - 7 + i * 0.2, 1),
            "precipitation_probability_max": max(0, min(100, rain + (i % 3 - 1) * 10)),
            "precipitation_sum_mm":          float(i * 2),
            "weather_code":                  3,
        })

    current: dict[str, Any] = {
        "time":                     now_str,
        "temperature_c":            temp,
        "apparent_temperature_c":   round(temp + 1.5, 1),
        "relative_humidity_percent": humidity,
        "precipitation_mm":         1.2 if rain >= 70 else 0.0,
        "precipitation_probability": rain,
        "wind_speed_kmh":           wind,
        "wind_direction_degrees":   240,
        "weather_code":             3,
        "is_day":                   1,
        "us_aqi":                   aqi,
    }

    return {
        "location": {
            "name":      matched,
            "country":   "Demo data — not a real observation",
            "latitude":  lat,
            "longitude": lon,
            "timezone":  tz,
        },
        "source":     "simulation",
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "current":    current,
        "hourly":     hourly,
        "daily":      daily,
        "alerts":     build_alerts(current),
    }


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

async def get_weather(
    city: str,
    latitude: float | None,
    longitude: float | None,
    simulation: bool,
) -> dict[str, Any]:
    """
    Return a normalised weather dict for the requested city.

    Parameters
    ----------
    city : str
        Human-readable city name.
    latitude, longitude : float or None
        When both are supplied the geocoding step is skipped.
    simulation : bool
        When True, return deterministic offline data.  Simulation is NEVER
        used as a silent fallback for live failures — a live failure raises.

    Raises
    ------
    ValueError
        City not found by geocoding.
    RuntimeError
        External API unreachable, timed out, or returned an error.
    """
    # --- Simulation path (explicit, clearly labelled) ------------------
    if simulation:
        return _demo(city)

    # --- Cache check ---------------------------------------------------
    cache_key = f"{city.strip().casefold()}|{latitude}|{longitude}"
    if settings.cache_ttl_seconds > 0 and cache_key in _cache:
        stored_at, cached_data = _cache[cache_key]
        age = time.time() - stored_at
        if age < settings.cache_ttl_seconds:
            logger.debug("Cache hit for '%s' (age %.0fs)", city, age)
            return cached_data

    # --- Geocoding (unless explicit coordinates were provided) ---------
    if latitude is not None and longitude is not None:
        location = {
            "name":      city,
            "country":   "",
            "latitude":  latitude,
            "longitude": longitude,
            # Let Open-Meteo resolve the local timezone from the coordinates.
            "timezone":  "auto",
        }
    else:
        location = await geocode_city(city)

    lat = location["latitude"]
    lon = location["longitude"]
    tz = location["timezone"]

    # --- Concurrent fetch (forecast + air quality) ---------------------
    forecast_task = _fetch_forecast(lat, lon, tz)
    air_task = _fetch_air_quality(lat, lon)
    forecast_json, air_json = await asyncio.gather(forecast_task, air_task)
    # The provider resolves `timezone=auto`; keep that local timezone in output.
    location["timezone"] = forecast_json.get("timezone", tz)

    # --- Normalise -----------------------------------------------------
    current_time_str = (forecast_json.get("current") or {}).get("time", "")
    aqi = _extract_current_aqi(air_json, current_time_str)
    current, hourly, daily = _normalise_forecast(forecast_json, aqi)

    # --- Assemble response --------------------------------------------
    data: dict[str, Any] = {
        "location":   location,
        "source":     "Open-Meteo",
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "current":    current,
        "hourly":     hourly,
        "daily":      daily,
        "alerts":     build_alerts(current),
    }

    # --- Store in cache -----------------------------------------------
    if settings.cache_ttl_seconds > 0:
        _cache[cache_key] = (time.time(), data)

    return data


# ---------------------------------------------------------------------------
# CSV report
# ---------------------------------------------------------------------------

# Units for display in the CSV
_CURRENT_UNITS: dict[str, str] = {
    "temperature_c":             "°C",
    "apparent_temperature_c":    "°C",
    "relative_humidity_percent": "%",
    "precipitation_mm":          "mm",
    "precipitation_probability": "%",
    "wind_speed_kmh":            "km/h",
    "wind_direction_degrees":    "degrees",
    "weather_code":              "WMO code",
    "us_aqi":                    "US AQI",
    "is_day":                    "1=day 0=night",
}

_HOURLY_UNITS: dict[str, str] = {
    "temperature_c":             "°C",
    "precipitation_probability": "%",
    "precipitation_mm":          "mm",
    "relative_humidity_percent": "%",
    "wind_speed_kmh":            "km/h",
    "weather_code":              "WMO code",
}

_DAILY_UNITS: dict[str, str] = {
    "temperature_max_c":             "°C",
    "temperature_min_c":             "°C",
    "precipitation_probability_max": "%",
    "precipitation_sum_mm":          "mm",
    "weather_code":                  "WMO code",
}


def save_csv_report(weather: dict[str, Any]) -> Path:
    """
    Write a snapshot of the weather response to a CSV file under outputs/.

    The CSV uses a tidy long format: one measurement per row.  Sections are:
      report_info — metadata (source, fetch time, coordinates)
      current     — current-conditions measurements
      hourly      — 24 hourly forecast rows (one metric per row)
      daily       — 7 daily forecast rows (one metric per row)
      alert       — triggered alert records

    Returns the Path of the written file.

    Raises OSError if the file cannot be created.
    """
    output_dir = Path(__file__).resolve().parents[2] / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    location = weather.get("location", {})
    city_name = location.get("name", "weather")
    safe_city = re.sub(r"[^A-Za-z0-9_-]+", "_", city_name).strip("_") or "weather"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    report_path = output_dir / f"weather_report_{safe_city}_{timestamp}.csv"

    fetched_at = weather.get("fetched_at", "")
    source = weather.get("source", "")

    with report_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        # Header
        writer.writerow(["record_type", "location", "timestamp",
                          "metric", "value", "unit", "notes"])

        # --- report_info section ---
        meta = {
            "source":    source,
            "fetched_at": fetched_at,
            "country":   location.get("country", ""),
            "timezone":  location.get("timezone", ""),
            "latitude":  location.get("latitude", ""),
            "longitude": location.get("longitude", ""),
            "simulation": "yes" if source == "simulation" else "no",
        }
        for metric, value in meta.items():
            if value != "" and value is not None:
                writer.writerow(["report_info", city_name, fetched_at,
                                  metric, value, "", ""])

        # --- current section ---
        current = weather.get("current", {})
        cur_time = current.get("time", fetched_at)
        for metric, value in current.items():
            if metric == "time" or value is None:
                continue
            writer.writerow([
                "current", city_name, cur_time,
                metric, value, _CURRENT_UNITS.get(metric, ""), "",
            ])

        # --- hourly section ---
        for entry in weather.get("hourly", []):
            h_time = entry.get("time", "")
            for metric, value in entry.items():
                if metric == "time" or value is None:
                    continue
                writer.writerow([
                    "hourly", city_name, h_time,
                    metric, value, _HOURLY_UNITS.get(metric, ""), "",
                ])

        # --- daily section ---
        for entry in weather.get("daily", []):
            d_date = entry.get("date", "")
            for metric, value in entry.items():
                if metric == "date" or value is None:
                    continue
                writer.writerow([
                    "daily", city_name, d_date,
                    metric, value, _DAILY_UNITS.get(metric, ""), "",
                ])

        # --- alerts section ---
        for alert in weather.get("alerts", []):
            writer.writerow([
                "alert", city_name, fetched_at,
                alert.get("kind", ""),
                alert.get("level", ""),
                alert.get("title", ""),
                alert.get("message", ""),
            ])

    logger.info("CSV report saved: %s", report_path)
    return report_path
