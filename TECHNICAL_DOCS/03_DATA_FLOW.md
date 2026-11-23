# 03 — Data Flow

## End-to-End Flow: Live Mode

```
USER types city name → clicks "Get Weather"
         │
         ▼
[Streamlit] requests.get("http://localhost:8000/weather?city=Mumbai&simulation=false")
         │
         ▼
[FastAPI Route] GET /weather
   • Validates: city length 2–100 chars
   • Validates: latitude ∈ [-90,90], longitude ∈ [-180,180] (optional)
   • Calls: await get_weather("Mumbai", None, None, simulation=False)
         │
         ▼
[service.py → get_weather()]
   Step 1: Build cache key = "Mumbai|None|None"
   Step 2: Check _cache dict
     ├── HIT (age < 600s) → return cached dict immediately
     └── MISS → continue
         │
         ▼
   Step 3: await geocode_city("Mumbai")
     → GET https://geocoding-api.open-meteo.com/v1/search?name=Mumbai&count=1
     ← Response: { name, country, latitude, longitude, timezone }
         │
         ▼
   Step 4: asyncio.gather(
     fetch_forecast(lat, lon, tz),
     fetch_air_quality(lat, lon)
   )  ← BOTH happen simultaneously
         │
         ├── Forecast call: GET https://api.open-meteo.com/v1/forecast
         │     Params: latitude, longitude, timezone,
         │             hourly=[temperature_2m, precipitation_probability,
         │                     precipitation, apparent_temperature,
         │                     relative_humidity_2m, wind_speed_10m,
         │                     wind_direction_10m, weather_code],
         │             daily=[temperature_2m_max, temperature_2m_min,
         │                    precipitation_probability_max,
         │                    precipitation_sum],
         │             current=[temperature_2m, apparent_temperature,
         │                      relative_humidity_2m, precipitation,
         │                      wind_speed_10m, wind_direction_10m,
         │                      weather_code],
         │             forecast_days=7
         │
         └── Air Quality call: GET https://air-quality-api.open-meteo.com/v1/air-quality
               Params: latitude, longitude, hourly=us_aqi
         │
         ▼
   Step 5: Normalise JSON
     • Extract current hour index from hourly time array
     • Map provider field names → internal field names (e.g. temperature_2m → temperature_c)
     • Extract us_aqi for the current hour from air quality response
     • If AQI unavailable → us_aqi = None (safe default)
         │
         ▼
   Step 6: build_alerts(current_dict) → list of alert objects
         │
         ▼
   Step 7: Assemble unified response dict:
     {
       "location": { name, country, latitude, longitude, timezone },
       "source": "Open-Meteo",
       "fetched_at": "2026-11-24T...",
       "current": { temperature_c, apparent_temperature_c,
                    relative_humidity_percent, precipitation_mm,
                    precipitation_probability, wind_speed_kmh,
                    wind_direction_degrees, weather_code, us_aqi },
       "hourly": [ { time, temperature_c, precipitation_probability,
                     precipitation_mm } × 24 ],
       "daily":  [ { date, temperature_max_c, temperature_min_c,
                     precipitation_probability_max, precipitation_sum_mm } × 7 ],
       "alerts": [ { level, kind, title, message } ]
     }
         │
         ▼
   Step 8: Store in _cache[key] = (time.time(), response_dict)
         │
         ▼
[FastAPI] Returns JSON 200 to Streamlit
         │
         ▼
[Streamlit] Stores in st.session_state.weather_result
   • Renders metric cards (temperature, humidity, etc.)
   • Renders alert boxes (error/warning/success)
   • Renders Plotly line chart (daily temp max/min)
   • Renders Plotly bar chart (daily rain probability)
   • Renders Plotly hourly line chart (24h temp)
   • Renders Plotly scatter_geo map (city pin)
```

---

## Data Flow: Simulation Mode

```
USER toggles "Simulation mode ON" → clicks "Get Weather"
         │
         ▼
[FastAPI] → get_weather(city, None, None, simulation=True)
         │
         ▼
[service.py → _demo(city)]
   • Looks up city in DEMO_LOCATIONS dict (case-insensitive)
   • Falls back to "New Delhi" if city not found
   • Reads: (lat, lon, tz, rain_chance, temp, wind, aqi, humidity)
   • Generates 24 hourly records using:
       temperature_c = temp + (i % 5 - 2) * 1.2
       precipitation_probability = clamp(rain + (i%4-1)*9, 0, 100)
   • Generates 7 daily records using:
       temperature_max_c = temp + i * 0.4
   • Builds current dict from base values
   • Calls build_alerts(current) → same alert engine
   • Returns same dict structure as live mode (source = "simulation")
         │
         ▼
[Streamlit] renders the same components, while the source caption clearly labels
   the response as "simulation" so users can distinguish it from live data
```

---

## Data Flow: CSV Report Generation

```
USER clicks "Generate CSV report"
         │
         ▼
[Streamlit] → GET http://localhost:8000/weather/report?city=...
         │
         ▼
[FastAPI /weather/report] → get_weather() (may hit cache)
                          → save_csv_report(weather_dict)
         │
         ▼
[service.py → save_csv_report()]
   • Creates outputs/ directory if missing
   • Sanitises city name for filesystem safety
   • Generates filename: weather_report_{city}_{YYYYMMDD_HHMMSS_microseconds}.csv
   • Writes CSV rows:
       Section 1: report_info (source, fetched_at, country, lat, lon, tz)
       Section 2: current (all current metrics with units)
       Section 3: hourly (24 rows × metric per row)
       Section 4: daily (7 days × metric per row)
       Section 5: alerts (level, kind, title, message)
         │
         ▼
[FastAPI] Returns FileResponse (Content-Type: text/csv)
         │
         ▼
[Streamlit] Shows st.download_button → browser downloads .csv file
```

---

## Field Name Mapping (Provider → Internal)

| Open-Meteo Field | Internal Field | Unit |
|-----------------|---------------|------|
| `temperature_2m` | `temperature_c` | °C |
| `apparent_temperature` | `apparent_temperature_c` | °C |
| `relative_humidity_2m` | `relative_humidity_percent` | % |
| `precipitation` | `precipitation_mm` | mm |
| `precipitation_probability` | `precipitation_probability` | % |
| `wind_speed_10m` | `wind_speed_kmh` | km/h |
| `wind_direction_10m` | `wind_direction_degrees` | degrees |
| `weather_code` | `weather_code` | WMO code |
| `us_aqi` (air quality API) | `us_aqi` | US AQI index |

---

> **Updated:** 2026-11-24
