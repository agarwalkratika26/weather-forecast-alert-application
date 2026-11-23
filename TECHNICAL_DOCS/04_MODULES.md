# 04 — Modules Reference

## Module Map

```
src/
├── __init__.py
└── weather_app/
    ├── __init__.py
    ├── config.py      ← Settings singleton
    ├── service.py     ← Orchestration, fetch, cache, CSV
    ├── alerts.py      ← Rule-based alert engine
    └── main.py        ← FastAPI app, routes
```

---

## `main.py` (root) — ASGI Entry Point

**File:** `main.py`  
**Purpose:** One-line shim that imports `app` from the service layer for Uvicorn.

```python
from src.weather_app.main import app
```

**Why it exists:** Uvicorn needs a top-level `main:app` reference. Keeps project root clean.

---

## `src/weather_app/config.py` — Settings

**Purpose:** Centralised configuration loaded once at startup.

### Class: `Settings(BaseModel)`

| Attribute | Type | Default | Source |
|-----------|------|---------|--------|
| `app_name` | str | `"Weather Forecast & Alert API"` | Hardcoded |
| `api_version` | str | `"1.0.0"` | Hardcoded |
| `cache_ttl_seconds` | int | `600` | Hardcoded (10 minutes) |
| `request_timeout_seconds` | float | `12.0` | Hardcoded |
| `openweather_api_key` | str \| None | `None` | `OPENWEATHER_API_KEY` env var |

**Key behaviour:**
- Uses Pydantic `BaseModel` for type validation
- Calls `load_dotenv()` at module level → reads `.env` file automatically
- `settings` is a **module-level singleton** — imported by other modules

**Why Pydantic:** Auto-validates types on startup; makes settings testable as a plain object.

---

## `src/weather_app/alerts.py` — Alert Engine

**Purpose:** Pure function that evaluates weather conditions against thresholds and returns a list of alert objects.

### Named Constants (module-level)

All thresholds are defined as named constants at the top of the file for transparency:

```python
RAIN_MODERATE_PCT  = 40    # %
RAIN_HIGH_PCT      = 70    # %
RAIN_HEAVY_MM      = 20    # mm
TEMP_MODERATE_C    = 35    # °C
TEMP_HIGH_C        = 40    # °C
HUMIDITY_MODERATE_PCT = 85  # %
HUMIDITY_HIGH_PCT     = 95  # %
WIND_MODERATE_KMH  = 40    # km/h
WIND_HIGH_KMH      = 60    # km/h
AQI_MODERATE       = 101   # US AQI
AQI_HIGH           = 151   # US AQI
```

### Function: `build_alerts(weather: dict) → list[dict]`

**Input:** `current` weather dictionary with numeric values  
**Output:** List of alert dicts, each with keys: `level`, `kind`, `title`, `message`

**Algorithm:**
```
for each category in [rain, rain_amount, temperature, humidity, wind, aqi, storm_code]:
    read the relevant field from weather dict
    if field is None → skip (safe, no crash)
    if value >= HIGH_THRESHOLD → add(level="high", ...)
    elif value >= MODERATE_THRESHOLD → add(level="moderate", ...)

if no alerts were added → add one "info" / "clear" alert
```

**Alert Categories (7 rules):**

| Category | Field | Moderate Threshold | High Threshold |
|---------|-------|-------------------|----------------|
| Rain probability | `precipitation_probability` | ≥ 40% | ≥ 70% |
| Rain amount | `precipitation_mm` | — | ≥ 20 mm |
| Temperature | `temperature_c` | ≥ 35°C | ≥ 40°C |
| Humidity | `relative_humidity_percent` | ≥ 85% | ≥ 95% |
| Wind | `wind_speed_kmh` | ≥ 40 km/h | ≥ 60 km/h |
| Air Quality | `us_aqi` | ≥ 101 AQI | ≥ 151 AQI |
| Storm (WMO codes) | `weather_code` | — | 95, 96, or 99 |

> **Storm detection:** Only WMO codes 95/96/99 trigger a storm alert.  
> Rain or wind alone is **never** labelled a storm — that would be inaccurate.

### Function: `threshold_summary() → dict`

Returns all threshold values as a dictionary — used by the `/thresholds` API endpoint so users can see exactly why alerts did or didn't fire.

**Key design choices:**
- No side effects, no global state → pure function, easy to test
- None-safe: every field is guarded with `if field is not None`
- Always returns at least one element (the "info" fallback)
- Named constants, not magic numbers

---

## `src/weather_app/service.py` — Business Logic

**Purpose:** Coordinates geocoding, data fetching, caching, simulation, and CSV export.

### Module-Level State

```python
FORECAST_URL   = "https://api.open-meteo.com/v1/forecast"
GEOCODING_URL  = "https://geocoding-api.open-meteo.com/v1/search"
AIR_URL        = "https://air-quality-api.open-meteo.com/v1/air-quality"
_cache: dict[str, tuple[float, dict]]  # in-memory TTL cache
DEMO_LOCATIONS: dict[str, tuple]        # 5 hardcoded cities
```

### Function: `geocode_city(city: str) → dict` (async)

**Purpose:** Convert a city name string into geographic coordinates.

**Flow:**
1. HTTP GET to Open-Meteo Geocoding API
2. Parse JSON → `results[0]`
3. Return `{name, country, latitude, longitude, timezone}`
4. Raises `RuntimeError` on HTTP failure, `ValueError` if no results

### Function: `_demo(city: str) → dict` (private, sync)

**Purpose:** Generate a complete weather response dict entirely from local data.

**Algorithm:**
- Looks up city in `DEMO_LOCATIONS` (case-insensitive), falls back to "New Delhi"
- Applies simple math formulas to seed hourly variation:
  ```
  hourly[i].temperature_c = base_temp + (i % 5 - 2) * 1.2
  hourly[i].precipitation_probability = clamp(rain + (i%4-1)*9, 0, 100)
  daily[i].temperature_max_c = base_temp + i * 0.4
  ```
- Calls `build_alerts()` on the current dict
- Returns identical structure to live mode (source = "simulation")

### Function: `get_weather(city, latitude, longitude, simulation) → dict` (async)

**Purpose:** Main orchestrator — dispatches to demo or live path, handles caching.

**Flow:**
```
cache_key = f"{city}|{latitude}|{longitude}"
if cache_key in _cache and age < TTL:
    return cached
if simulation:
    return _demo(city)
location = await geocode_city(city)
forecast, air_quality = await asyncio.gather(
    _fetch_forecast(lat, lon, tz),
    _fetch_air_quality(lat, lon)
)
current = _normalise(forecast, air_quality)
data = { location, source, current, hourly, daily, alerts: build_alerts(current) }
_cache[key] = (time.time(), data)
return data
```

### Function: `save_csv_report(weather: dict) → Path`

**Purpose:** Persist a weather snapshot as a structured CSV file.

**Output file naming:** `weather_report_{safe_city}_{YYYYmmdd_HHMMSS_microseconds}.csv`  
**Output directory:** `outputs/` (auto-created if missing)  
**Encoding:** `utf-8-sig` (BOM for Excel compatibility)

---

## `src/weather_app/main.py` — FastAPI Routes

**Purpose:** Define REST API endpoints, validate inputs, map errors to HTTP status codes.

### Routes

| Method | Path | Query Params | Returns |
|--------|------|-------------|---------|
| GET | `/health` | — | `{status, service, version}` |
| GET | `/locations` | — | `{locations: [str]}` |
| GET | `/thresholds` | — | Alert thresholds and storm-code list |
| GET | `/weather` | city, latitude, longitude, simulation | Full weather dict |
| GET | `/weather/report` | city, latitude, longitude, simulation | CSV FileResponse |

**Error Mapping:**

| Exception | HTTP Status | Meaning |
|-----------|------------|---------|
| `ValueError` | 404 | City not found |
| `RuntimeError` | 502 | External API failure |
| `OSError` | 500 | Could not write CSV file |

---

## `src/dashboard/streamlit_app.py` — Streamlit Frontend

**Purpose:** Interactive web UI that calls the FastAPI backend and renders results.

**Key state:** `st.session_state.weather_result` — caches the last API response across re-renders

**Components rendered:**
1. Sidebar: city input, simulation toggle, "Get weather" button
2. Caption: data source + timestamp + timezone
3. "Generate CSV report" button → download button
4. 6 metric cards: Temperature, Feels Like, Humidity, Rain%, Wind, AQI
5. Alert boxes: `st.error` (high) / `st.warning` (moderate) / `st.success` (info)
6. Left column: 7-day temp line chart + 7-day rain bar chart
7. Right column: 24h temp line chart + geo scatter map
8. Expandable: raw forecast DataFrame

---

> **Updated:** 2026-11-24
