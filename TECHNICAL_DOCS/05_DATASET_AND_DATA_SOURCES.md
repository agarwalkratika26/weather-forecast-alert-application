# 05 — Dataset & Data Sources

## Overview

This project uses **no pre-trained dataset or ML model**.  
All data comes from **live external REST APIs** (or the built-in simulation for offline use).

---

## Primary Data Source: Open-Meteo

**Website:** https://open-meteo.com  
**License:** Free for non-commercial use, no API key required  
**Protocol:** HTTPS REST, JSON responses  
**Rate limit:** Generous — suitable for development use

### Why Open-Meteo?

| Reason | Detail |
|--------|--------|
| Free, no API key | No sign-up friction |
| Global coverage | Works for any city with coordinates |
| Accurate models | Uses NWP models (ECMWF, GFS, etc.) |
| Multiple endpoints | Geocoding + Forecast + Air Quality under one provider |

---

## Endpoint 1: Geocoding API

**URL:** `https://geocoding-api.open-meteo.com/v1/search`

| Query Param | Value | Purpose |
|------------|-------|---------|
| `name` | city string from user | City to look up |
| `count` | 1 | Return only the top match |
| `language` | en | English result names |
| `format` | json | Response format |

**Response fields used:**

```json
{
  "results": [{
    "name": "Mumbai",
    "country": "India",
    "latitude": 19.0760,
    "longitude": 72.8777,
    "timezone": "Asia/Kolkata"
  }]
}
```

---

## Endpoint 2: Forecast API

**URL:** `https://api.open-meteo.com/v1/forecast`

**Key parameters sent:**

| Parameter | Value |
|-----------|-------|
| `latitude` | from geocoding |
| `longitude` | from geocoding |
| `timezone` | from geocoding (e.g. "Asia/Kolkata") |
| `forecast_days` | 7 |
| `hourly` | `temperature_2m, precipitation_probability, precipitation, apparent_temperature, relative_humidity_2m, wind_speed_10m, wind_direction_10m, weather_code` |
| `daily` | `temperature_2m_max, temperature_2m_min, precipitation_probability_max, precipitation_sum` |
| `current` | `temperature_2m, apparent_temperature, relative_humidity_2m, precipitation, wind_speed_10m, wind_direction_10m, weather_code` |

**Hourly data returned:** 7 days × 24 hours = 168 data points per field  
**Daily data returned:** 7 rows  
**Current data returned:** 1 snapshot (most recent observation)

---

## Endpoint 3: Air Quality API

**URL:** `https://air-quality-api.open-meteo.com/v1/air-quality`

**Parameters:** `latitude`, `longitude`, `hourly=us_aqi`

**Field used:** `us_aqi` — the US Air Quality Index (0–500+)

| AQI Range | Category |
|-----------|---------|
| 0–50 | Good |
| 51–100 | Moderate |
| 101–150 | Unhealthy for sensitive groups |
| 151–200 | Unhealthy |
| 201–300 | Very unhealthy |
| 301+ | Hazardous |

**How the current AQI is extracted:**
1. Find current hour index by matching `hourly.time` array to current hour string
2. Read `hourly.us_aqi[current_hour_index]`
3. If unavailable or API fails → `us_aqi = None` (alerts engine handles gracefully)

---

## Built-In Simulation Dataset (DEMO_LOCATIONS)

**Location:** `src/weather_app/service.py`  
**Type:** Python dictionary — no file, no database  
**Purpose:** Offline / demo mode — 5 hardcoded cities

```python
DEMO_LOCATIONS = {
    "New Delhi": (28.6139, 77.2090, "Asia/Kolkata",    42, 31.4, 56, 78, 91),
    "London":    (51.5072, -0.1276, "Europe/London",   58, 18.2, 24,  8, 78),
    "Tokyo":     (35.6762, 139.6503, "Asia/Tokyo",     22, 27.1, 18, 42, 96),
    "New York":  (40.7128, -74.0060, "America/New_York",76, 24.0, 34, 22, 70),
    "Sydney":    (-33.8688, 151.2093, "Australia/Sydney",12, 21.7, 17, 11, 60),
}
# Tuple order: lat, lon, timezone, rain_chance%, temp_c, wind_kmh, AQI, humidity%
```

**How simulation data is generated from this dict:**

| Field | Formula |
|-------|---------|
| Hourly temperature | `base_temp + (i%5 - 2) * 1.2` |
| Hourly rain probability | `clamp(rain + (i%4-1)*9, 0, 100)` |
| Hourly precipitation | `2.4mm if i%3==0 else 0.0` |
| Daily max temp | `base_temp + i * 0.4` |
| Daily min temp | `base_temp - 7 + i * 0.2` |
| Daily rain probability | `clamp(rain + (i%3-1)*10, 0, 100)` |
| Daily precipitation sum | `i * 2.0 mm` |

**Characteristics of simulation data:**
- Fully deterministic — same city + same call time produces same hourly pattern
- Varies by hour index using modular arithmetic (not random, reproducible)
- Always triggers some alerts (New Delhi: AQI=78 → moderate; New York: rain=76% → high)

---

## No Machine Learning

> This project does **not train any ML model**.  
> Weather *prediction* is done by Open-Meteo's NWP (Numerical Weather Prediction) models on their servers.  
> This project only **fetches and displays** that pre-computed forecast data.

If ML were added in future it could include:
- Anomaly detection on historical AQI trends
- Local threshold auto-tuning from user feedback
- Time-series forecasting using LSTM on downloaded historical data

---

> **Updated:** 2026-11-24
