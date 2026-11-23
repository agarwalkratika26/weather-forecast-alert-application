# Project guide

## 1. Request flow

```text
Streamlit dashboard → FastAPI /weather → geocoding → forecast + air quality
                                      ↘ alert rules → JSON response
Simulation switch ─────────────────────→ deterministic sample response
```

The UI calls the API over HTTP just like a separately deployed frontend would. FastAPI owns provider calls, response shaping, caching, and alert generation. The dashboard owns presentation only.

## 2. Main modules

- `main.py`: root ASGI entry point used to run the API with Uvicorn.
- `src/weather_app/main.py`: API metadata, health, simulation-location list, and weather endpoint.
- `src/weather_app/service.py`: geocoding, Open-Meteo requests, response normalization, short in-memory cache, and simulation scenarios.
- `src/weather_app/alerts.py`: pure rule evaluation. Each risk rule returns a consistent alert object.
- `src/weather_app/service.py`: also writes downloadable CSV report snapshots to `outputs/`.
- `src/dashboard/streamlit_app.py`: city search, metrics, risk notifications, Plotly charts, and a geographic map.

## 3. Data sources and resilience

Live mode resolves a city through Open-Meteo Geocoding, then uses Forecast and Air Quality endpoints. Requests have a timeout. A provider failure becomes an API error rather than silently showing stale or fake live data. AQI is optional: if the air endpoint does not provide it, the API returns `null` and AQI rules are skipped. The cache is in-process and expires after ten minutes by default; restarting the API clears it.

Simulation mode is a deterministic set of example conditions. It is useful for presentations and checking alert scenarios without depending on internet access. Keep the source label visible whenever sharing screenshots or exported output.

## 4. Extending the project

1. Move risk thresholds into a settings file and allow user profiles.
2. Add saved locations and user-configurable alert subscriptions.
3. Add persistent storage (SQLite/PostgreSQL) for alert history.
4. Add scheduled polling and email/web push notifications with opt-in controls.
5. Add API authentication, rate limiting, structured logs, and deployment configuration before exposing a public service.
6. Build automated unit and API tests for alert boundaries and provider failure cases before production use.

## 5. Learning outcomes

This project demonstrates Python modules, async HTTP integration, REST API design, data normalization, validation, cache basics, rule-based automation, charting, user-facing error handling, and reproducible demo data.
