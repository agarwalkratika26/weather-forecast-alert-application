# 08 — Tech Stack

## Runtime

| Component | Technology | Version | Why chosen |
|-----------|-----------|---------|-----------|
| Language | Python | 3.11+ | Async support, rich ecosystem, beginner-friendly |
| ASGI Server | Uvicorn (standard) | ≥0.30 | Fast async server, pairs perfectly with FastAPI |
| Web Framework | FastAPI | ≥0.115 | Auto OpenAPI docs, async-native, Pydantic validation |
| HTTP Client (async) | httpx | ≥0.27 | Async-first, modern API, works with asyncio.gather |
| HTTP Client (sync) | requests | ≥2.32 | Used by Streamlit frontend to call FastAPI |
| Data Validation | Pydantic v2 | ≥2.8 | Settings model validation, FastAPI integration |
| Env Management | python-dotenv | ≥1.0 | Load `.env` files automatically |

## Frontend & Visualisation

| Component | Technology | Version | Why chosen |
|-----------|-----------|---------|-----------|
| Dashboard | Streamlit | ≥1.38 | Zero-HTML dashboard in pure Python |
| Charts | Plotly | ≥5.24 | Interactive charts; native Streamlit integration |
| Data manipulation | Pandas | ≥2.2 | DataFrame from API JSON for Plotly rendering |

## External APIs (No SDK — raw HTTP)

| API | URL | Purpose | Auth |
|-----|-----|---------|------|
| Open-Meteo Geocoding | geocoding-api.open-meteo.com | City name → coordinates | None required |
| Open-Meteo Forecast | api.open-meteo.com/v1/forecast | Current + hourly + daily weather | None required |
| Open-Meteo Air Quality | air-quality-api.open-meteo.com | US AQI hourly | None required |

## Development Tooling

| Tool | Purpose |
|------|---------|
| `.env` / `.env.example` | Manage env vars without hardcoding secrets |
| `.gitignore` | Exclude `.env`, `.venv`, `__pycache__`, `outputs/` from VCS |
| `requirements.txt` | Pinned dependency ranges for reproducible installs |

---

## Dependency Graph

```
main.py (root)
   └── src.weather_app.main (FastAPI app)
         ├── src.weather_app.config (Settings singleton)
         ├── src.weather_app.service
         │     ├── httpx (async HTTP)
         │     ├── src.weather_app.alerts
         │     └── src.weather_app.config
         └── fastapi, pydantic

src.dashboard.streamlit_app
   ├── streamlit
   ├── plotly.express
   ├── pandas
   └── requests (sync HTTP → localhost:8000)
```

---

## Why asyncio.gather() for Parallel Fetching?

The service fetches the **Forecast API** and **Air Quality API** simultaneously:

```python
forecast, air_quality = await asyncio.gather(
    _fetch_forecast(lat, lon, tz),
    _fetch_air_quality(lat, lon)
)
```

- Both are I/O-bound (network calls)
- Running them concurrently saves ~50% of total latency compared to sequential calls
- If air quality fails → returns None gracefully (no crash)

---

## Why Requests (sync) in Streamlit?

Streamlit's execution model runs the entire script on each re-render.  
Using `asyncio` within Streamlit is complex (event loop conflicts).  
Since the Streamlit → FastAPI call is a local HTTP call and not in the critical path of the async backend, synchronous `requests` is simpler and safe here.

---

> **Updated:** 2026-11-24
