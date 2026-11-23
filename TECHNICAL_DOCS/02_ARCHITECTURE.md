# 02 — System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BROWSER / USER                                 │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │  HTTP (port 8501 default)
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       LAYER 1 — STREAMLIT FRONTEND                          │
│   streamlit_app.py                                                          │
│   • Sidebar: city input, simulation toggle, "Get weather" button            │
│   • Session state caches last response                                      │
│   • Calls FastAPI backend over HTTP                                         │
│   • Renders metrics, alerts, Plotly charts, geo map                        │
│   • Download button triggers /weather/report endpoint                       │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │  HTTP GET /weather?city=...&simulation=...
                                  │  (port 8000 — localhost)
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       LAYER 2 — FASTAPI BACKEND                             │
│   src/weather_app/main.py                                                   │
│   • Route: GET /health                                                      │
│   • Route: GET /locations                                                   │
│   • Route: GET /weather                                                     │
│   • Route: GET /weather/report (returns CSV FileResponse)                   │
│   • Validates query params (Pydantic + FastAPI Query())                     │
│   • Calls service layer; maps ValueError→404, RuntimeError→502              │
└───────────────────┬─────────────────────────────┬───────────────────────────┘
                    │                             │
                    ▼  (simulation=false)         ▼  (simulation=true)
┌───────────────────────────────┐  ┌─────────────────────────────────────────┐
│   LAYER 3A — SERVICE LAYER    │  │   LAYER 3B — SIMULATION ENGINE          │
│   service.py (live path)      │  │   service.py → _demo()                  │
│   • geocode_city() — resolve  │  │   • DEMO_LOCATIONS dict (5 cities)      │
│     city name → lat/lon       │  │   • Applies modular arithmetic to       │
│   • asyncio.gather() fetches  │  │     produce variation in hourly/daily   │
│     forecast + air quality    │  │   • No network required                 │
│     simultaneously            │  │   • Returns identical structure as live │
│   • Normalises JSON           │  └─────────────────────────────────────────┘
│   • Checks in-memory cache    │
│   • Calls build_alerts()      │
│   • Returns unified dict      │
└───────────────────┬───────────┘
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
┌──────────────────┐  ┌────────────────────────────────────────────────────┐
│  OPEN-METEO APIs │  │   LAYER 4 — ALERT ENGINE                           │
│  (External)      │  │   alerts.py → build_alerts()                       │
│  • Geocoding API │  │   • Pure function: takes current weather dict      │
│  • Forecast API  │  │   • Applies threshold rules for 5 categories       │
│  • Air Quality   │  │   • Returns list of alert objects                  │
│    API           │  │   • No side effects, no state                      │
└──────────────────┘  └────────────────────────────────────────────────────┘
```

---

## Layer Responsibilities

| Layer | File(s) | Responsibility |
|-------|---------|---------------|
| **Frontend** | `streamlit_app.py` | UI, user input, HTTP calls, charts |
| **API Gateway** | `src/weather_app/main.py` | Routes, param validation, error mapping |
| **Config** | `src/weather_app/config.py` | Settings singleton, env var loading |
| **Service** | `src/weather_app/service.py` | Orchestration, geocoding, data fetch, cache, CSV |
| **Alert Engine** | `src/weather_app/alerts.py` | Rule evaluation, alert generation |
| **External APIs** | Open-Meteo (3 endpoints) | Raw weather, geocoding, air quality data |

---

## Communication Protocol

| Connection | Protocol | Port |
|-----------|---------|------|
| Browser ↔ Streamlit | HTTP | 8501 |
| Streamlit ↔ FastAPI | HTTP (REST) | 8000 |
| FastAPI ↔ Open-Meteo | HTTPS (async httpx) | 443 |

---

## Design Principles Applied

- **Separation of Concerns** — UI, API, business logic, and alerts are in separate files
- **Single Responsibility** — `alerts.py` only evaluates rules; `service.py` only fetches/caches
- **Dependency Injection via Settings** — config is centralised in `config.py` using Pydantic
- **Graceful Degradation** — missing optional fields (AQI) don't crash the system
- **Offline-First Option** — simulation mode allows full UI testing without network

---

> **Updated:** 2026-11-24
