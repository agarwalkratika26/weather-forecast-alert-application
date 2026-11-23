# Tech stack options

There are three reasonable ways to build a weather project. Choose based on the amount of Python and web development you want to demonstrate.

## Option A — Easy: Python command-line weather checker

| Area | Choice |
|---|---|
| Language and libraries | Python, `requests`, built-in `json` handling, `datetime`; optionally Pandas and Matplotlib |
| Data provider | OpenWeatherMap or WeatherAPI |
| Difficulty | Beginner |
| Expected output | A command-line report for one city: current conditions, a short forecast, and simple rain/heat warnings. Optional Matplotlib chart saved as an image. |

**How it works:** ask the user for a city, call the provider with `requests`, parse the JSON response, convert timestamps with `datetime`, and print selected values. Pandas and Matplotlib can summarize and plot forecast readings once the basic version works.

**Good fit when:** learning HTTP requests, JSON, conditions, loops, functions, and exception handling. It has the fewest moving parts, but does not demonstrate a web API or interactive dashboard.

## Option B — Intermediate: FastAPI service and Streamlit dashboard

| Area | Choice |
|---|---|
| Language and libraries | Python, FastAPI, `httpx` or `requests`, Pydantic, JSON, `datetime`, Pandas, Plotly or Matplotlib, Streamlit |
| Data provider | OpenWeatherMap, WeatherAPI, or Open-Meteo |
| Difficulty | Intermediate |
| Expected output | A documented REST API plus a browser dashboard with current weather, forecast charts, a location map, and risk notifications. Optional email alerts can be added after the core flow works. |

**How it works:** FastAPI receives a location, calls the weather provider, normalizes the response, calculates alerts, and returns JSON. Streamlit calls the backend and renders the results. Pandas is useful for shaping time-series data; Plotly or Matplotlib can chart it.

**Good fit when:** building a Python portfolio project that demonstrates API integration and a user interface without requiring a separate JavaScript frontend. This is the recommended student option: it is substantial enough to discuss in interviews while remaining approachable in small steps.

## Option C — Advanced: deployable monitoring platform

| Area | Choice |
|---|---|
| Language and libraries | FastAPI, Pydantic, async `httpx`, Pandas, SQLAlchemy, PostgreSQL, Redis, a background worker such as Celery, Docker, and a Next.js frontend |
| Data provider | OpenWeatherMap, WeatherAPI, or another provider with a plan suited to the deployment |
| Difficulty | Advanced |
| Expected output | A deployed web application with user accounts, saved locations and alert history, scheduled forecast checks, configurable notification channels, and a responsive map/chart dashboard. Email or SMS can be added through a mail service or messaging provider. |

**How it works:** background workers poll selected locations, store time-stamped observations and alert events, and enqueue notification jobs. FastAPI serves authenticated clients, while Next.js provides the web interface. Redis can coordinate caching and work queues; PostgreSQL stores durable data.

**Good fit when:** the core app already works and the developer wants to learn deployment, persistence, background processing, and operational concerns. This has more services to configure and maintain, so it is not the best starting point for a first Python course project.

## Recommendation for students

Start with **Option B**, and build it in this order:

1. Fetch one city's current weather and print a small report.
2. Parse provider JSON safely and handle missing or invalid values.
3. Add forecast data and simple alert rules.
4. Put the data and alert logic behind FastAPI endpoints.
5. Add the Streamlit dashboard, charts, and map.
6. Add offline sample data so the project can be demonstrated without a live provider call.
7. Consider email or SMS only after the API and dashboard work reliably.

Option A is a good first milestone if FastAPI is new. Option C is a possible later extension rather than a prerequisite for a strong student project.

## Mapping to this repository

This repository implements an Option B style project: Python/FastAPI, Open-Meteo, an offline simulation, rule-based alerts, and a Streamlit/Plotly dashboard. It uses `httpx` for the asynchronous provider calls. OpenWeatherMap or WeatherAPI could replace the provider integration in `src/weather_app/service.py`, subject to each provider's current account setup, plan, and terms. Email/SMS delivery and a persistent report history are future extensions, not current features.

The simpler building blocks—`requests`, JSON parsing, `datetime`, Pandas, and Matplotlib—are useful learning choices. This implementation uses `httpx` and Plotly for its current async service and dashboard charts, but the concepts transfer directly.
