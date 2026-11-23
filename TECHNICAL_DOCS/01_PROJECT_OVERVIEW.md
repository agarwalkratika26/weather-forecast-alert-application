# 01 — Project Overview

## What is This Project?

A **two-tier web application** that:
1. Fetches real-time weather data for any city in the world from the free **Open-Meteo** API
2. Applies a **rule-based alert engine** to flag heat, rain, wind, humidity, and air quality risks
3. Exposes the results through a **FastAPI REST backend**
4. Visualises everything on a **Streamlit dashboard** with charts, metrics, and a location map

---

## Project Goals

| Goal | Detail |
|------|--------|
| **Live Forecasts** | Retrieve current conditions + 24-hour hourly + 7-day daily forecast |
| **Risk Alerts** | Classify weather conditions into `info / moderate / high` levels |
| **Offline Mode** | Work without internet via deterministic simulation for 5 preset cities |
| **Downloadable Reports** | Generate a timestamped CSV snapshot of current conditions and alerts |
| **Clean API** | RESTful FastAPI backend with OpenAPI docs auto-generated |
| **Interactive Dashboard** | Streamlit frontend with Plotly charts and a geo map |

---

## What This Project is NOT

- ❌ Not a machine-learning forecasting model (no model training happens)
- ❌ Not a real official warning system (thresholds are educational defaults)
- ❌ Not a database-persisted application (reports are file-based; cache is in-memory)
- ❌ Not a real-time streaming application (data is polled on user request)

---

## Two Operating Modes

```
┌─────────────────────────────────────────────────────────────┐
│                        USER REQUEST                         │
└────────────────────────────┬────────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │  simulation=false (default)  │  simulation=true
              │  LIVE MODE                   │  DEMO MODE
              │  → Geocoding API             │  → Hardcoded dict
              │  → Forecast API (async)      │  → Math formula
              │  → Air Quality API (async)   │  → No network needed
              └──────────────────────────────┘
```

**Live Mode:** Real HTTP calls to Open-Meteo public APIs. Requires internet.  
**Demo/Simulation Mode:** Pure Python computation from a hardcoded `DEMO_LOCATIONS` dictionary. No network, fully deterministic.

---

## Stakeholders / Audience

- Student developer building & learning the project
- Technical interviewer evaluating the design
- End user checking weather for a city

---

> **Status:** Pre-execution — code exists, not yet run.  
> **Updated:** 2026-11-24
