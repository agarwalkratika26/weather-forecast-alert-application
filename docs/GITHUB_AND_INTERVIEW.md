# GitHub and interview guide

## Publish the project

1. Create a new public GitHub repository named `weather-forecast-alert-application` (do not initialize it with a README, since this project already has one).
2. In a terminal opened at this project folder, run:

   ```powershell
   git init
   git add .
   git commit -m "Build weather forecast and alert application"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/weather-forecast-alert-application.git
   git push -u origin main
   ```

3. Replace `YOUR-USERNAME` with your GitHub username. Review the repository after pushing; make sure `.venv`, credentials, and local secrets were not added.
4. Run the app in simulation mode, capture a clear dashboard image, and save it as `images/dashboard-overview.png`. Add the screenshot embed shown in the README.
5. Add a short repository description such as “FastAPI weather service with Open-Meteo forecasts, explainable risk alerts, and a Streamlit dashboard.” Add topics: `python`, `fastapi`, `streamlit`, `weather-api`, `data-visualization`.

## Suggested portfolio walkthrough

"I built a weather risk dashboard with a Python FastAPI backend and Streamlit frontend. The API looks up a city, retrieves current and forecast data from Open-Meteo, optionally adds AQI, normalizes the provider response, and applies transparent rain, heat, humidity, wind, and AQI rules. It also generates downloadable CSV reports. Deterministic simulation scenarios make the demo work without network access. The dashboard shows location, forecasts, alerts, charts, and a map, and the API is browsable through OpenAPI docs."

## Interview questions and answer points

**Why separate the API and dashboard?** The API owns weather-provider integration and alert rules, so another client could reuse the same JSON contract. The dashboard can focus on visualization.

**How do you handle missing AQI?** AQI is nullable and optional. If the provider has no value or the request fails, the app omits AQI alerts instead of inventing a value.

**Why have a simulation mode?** It makes the project reproducible for demos, works offline, and gives predictable conditions for showing risk scenarios. The response is clearly labeled so it cannot be mistaken for live observations.

**How would you make alerts production ready?** Validate thresholds against local official guidance, add persisted subscriptions and alert history, deduplicate notifications, schedule polling, collect delivery failures, and document the limits of the data source.

**What are the current limitations?** Thresholds are educational defaults, the cache is per-process memory, simulation scenarios are static, and no authentication or notification delivery is included. Provider terms and reliability should be reviewed before public deployment.

## Resume bullet

Built a Python weather monitoring application with FastAPI, Open-Meteo integration, simulated offline scenarios, configurable rain/heat/wind/AQI risk rules, and a Streamlit dashboard with interactive forecasts and geographic visualization.
