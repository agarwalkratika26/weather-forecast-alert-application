"""
streamlit_app.py — Interactive Streamlit dashboard for the Weather Forecast & Alert API.

How it works
------------
1. The user types a city name and optionally toggles simulation mode.
2. The dashboard makes an HTTP GET to the FastAPI backend at /weather.
3. The returned JSON is rendered as metric cards, alert boxes, Plotly charts,
   a geo map, and an optional CSV download.

Prerequisites
-------------
- The FastAPI backend must be running (default: http://localhost:8000).
- Run with:  py -m streamlit run src/dashboard/streamlit_app.py
"""

import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from dotenv import load_dotenv

# Load .env so the WEATHER_API_URL variable is available
load_dotenv()

# ---------------------------------------------------------------------------
# Page config — MUST be the first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Weather & Risk Monitor",
    page_icon="🌦️",
    layout="wide",
)

st.title("🌦️ Weather Forecast & Alert Application")
st.caption(
    "Live forecasts, location maps, and transparent rule-based risk alerts  ·  "
    "[API Docs](http://localhost:8000/docs)"
)

# ---------------------------------------------------------------------------
# Backend URL — from .env or fallback
# ---------------------------------------------------------------------------
api_url: str = os.getenv("WEATHER_API_URL", "http://localhost:8000").rstrip("/")

# ---------------------------------------------------------------------------
# Sidebar — user inputs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("🔍 Search")
    city = st.text_input(
        "City or location",
        value="New Delhi",
        help="Type any city name. In simulation mode, only 5 preset cities are available.",
    )
    simulation = st.toggle(
        "Simulation mode (works offline)",
        value=False,
        help=(
            "Uses hardcoded demo data via the local API — no external weather "
            "provider calls required. Note: the local FastAPI backend must still be running."
        ),
    )
    refresh = st.button("Get weather", type="primary", use_container_width=True)

    st.divider()

    # Provide quick links to try the preset cities when simulation is on
    if simulation:
        st.markdown(
            "**Demo cities:** New Delhi · London · Tokyo · New York · Sydney"
        )

    st.caption(
        "Live mode uses public [Open-Meteo](https://open-meteo.com/) data. "
        "Forecasts and risk levels are informational — follow your local weather "
        "service for official warnings."
    )

# ---------------------------------------------------------------------------
# Data fetch
# ---------------------------------------------------------------------------
if "weather_result" not in st.session_state or refresh:
    try:
        with st.spinner("Fetching weather data…"):
            resp = requests.get(
                f"{api_url}/weather",
                params={"city": city, "simulation": simulation},
                timeout=25,
            )
            resp.raise_for_status()
            st.session_state.weather_result = resp.json()
            st.session_state.fetch_error = None
    except requests.ConnectionError:
        # Graceful fallback for single-container / Streamlit Community Cloud deployments
        try:
            import asyncio
            from src.weather_app.service import get_weather

            with st.spinner("Connecting via internal weather service…"):
                data = asyncio.run(
                    get_weather(city=city, latitude=None, longitude=None, simulation=simulation)
                )
                st.session_state.weather_result = data
                st.session_state.fetch_error = None
        except Exception as fallback_exc:
            st.session_state.fetch_error = (
                f"**Cannot reach the API server** at `{api_url}` and direct fallback failed: {fallback_exc}\n\n"
                "Start the backend locally with:\n"
                "```\npy -m uvicorn main:app --reload\n```"
            )
    except requests.Timeout:
        st.session_state.fetch_error = (
            "**Request timed out.** The backend is running but did not respond "
            "within 25 seconds. Try again or enable simulation mode."
        )
    except requests.HTTPError as exc:
        try:
            detail = exc.response.json().get("detail", str(exc))
        except Exception:
            detail = str(exc)
        st.session_state.fetch_error = (
            f"**API error ({exc.response.status_code}):** {detail}"
        )
    except requests.RequestException as exc:
        st.session_state.fetch_error = f"**Unexpected error:** {exc}"

# Show error state if the fetch failed
if st.session_state.get("fetch_error"):
    st.error(st.session_state["fetch_error"])
    st.info(
        "💡 **Tip:** Enable *Simulation mode* in the sidebar and click "
        "*Get weather* to test the dashboard without a connection to Open-Meteo. "
        "The local FastAPI backend must still be running; simulation removes only "
        "the external weather-provider dependency."
    )
    st.stop()

# If we still have no data at all, stop (first load with backend down)
if "weather_result" not in st.session_state:
    st.info("Click **Get weather** in the sidebar to load data.")
    st.stop()

# ---------------------------------------------------------------------------
# Unpack response
# ---------------------------------------------------------------------------
data = st.session_state.weather_result
place = data["location"]
current = data["current"]
source = data["source"]
fetched_at = data["fetched_at"]

# ---------------------------------------------------------------------------
# Top banner — source label & match info
# ---------------------------------------------------------------------------
# If the matched city name differs from what the user typed, let them know
if (
    not simulation
    and city
    and place["name"].casefold() != city.strip().casefold()
):
    st.caption(
        f"Showing best location match: **{place['name']}, "
        f"{place.get('country', '')}**"
    )

source_label = "🟢 Open-Meteo (live)" if source != "simulation" else "🟡 Simulation (offline demo)"
st.caption(
    f"Data source: **{source_label}**  ·  "
    f"Updated: `{fetched_at}`  ·  "
    f"Timezone: `{place['timezone']}`"
)

# ---------------------------------------------------------------------------
# CSV report download
# ---------------------------------------------------------------------------
col_report, _ = st.columns([1, 3])
with col_report:
    if st.button("📄 Generate CSV report"):
        report_bytes = None
        safe_name = place["name"].replace(" ", "_")
        try:
            report_resp = requests.get(
                f"{api_url}/weather/report",
                params={"city": city, "simulation": simulation},
                timeout=25,
            )
            report_resp.raise_for_status()
            report_bytes = report_resp.content
        except requests.RequestException:
            # Fallback to direct in-process report generation (Streamlit Cloud)
            try:
                from src.weather_app.service import save_csv_report
                report_path = save_csv_report(st.session_state.weather_result)
                with open(report_path, "rb") as fh:
                    report_bytes = fh.read()
            except Exception as report_exc:
                st.error(f"Could not generate the CSV report: {report_exc}")

        if report_bytes:
            st.download_button(
                "⬇️ Download weather report",
                data=report_bytes,
                file_name=f"weather_report_{safe_name}.csv",
                mime="text/csv",
            )

# ---------------------------------------------------------------------------
# Metric cards — 6 columns
# ---------------------------------------------------------------------------
st.subheader("Current Conditions")
cols = st.columns(6)
metrics = [
    ("🌡️ Temperature", current.get("temperature_c"), "°C"),
    ("🤒 Feels Like",  current.get("apparent_temperature_c"), "°C"),
    ("💧 Humidity",     current.get("relative_humidity_percent"), "%"),
    ("🌧️ Rain Chance",  current.get("precipitation_probability"), "%"),
    ("💨 Wind",         current.get("wind_speed_kmh"), "km/h"),
    ("🏭 US AQI",       current.get("us_aqi"), ""),
]
for column, (label, value, suffix) in zip(cols, metrics):
    display = f"{value}{suffix}" if value is not None else "—"
    column.metric(label, display)

# ---------------------------------------------------------------------------
# Risk alerts
# ---------------------------------------------------------------------------
st.subheader("⚠️ Risk Notifications")
alerts = data.get("alerts", [])
if alerts and alerts[0].get("level") == "info":
    st.success(f"✅ {alerts[0]['title']} — {alerts[0]['message']}")
else:
    for alert in alerts:
        msg = f"**{alert['title']}** — {alert['message']}"
        if alert["level"] == "high":
            st.error(f"🔴 {msg}")
        else:
            st.warning(f"🟡 {msg}")

# ---------------------------------------------------------------------------
# Charts — two columns
# ---------------------------------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("📅 7-Day Forecast")
    daily_df = pd.DataFrame(data["daily"])
    if not daily_df.empty:
        # Temperature line chart
        fig_temp = px.line(
            daily_df,
            x="date",
            y=["temperature_max_c", "temperature_min_c"],
            markers=True,
            labels={"value": "Temperature (°C)", "variable": "Metric", "date": "Date"},
            title="Daily High / Low Temperature",
        )
        fig_temp.update_layout(legend_title_text="")
        st.plotly_chart(fig_temp, use_container_width=True)

        # Precipitation probability bar chart
        fig_rain = px.bar(
            daily_df,
            x="date",
            y="precipitation_probability_max",
            labels={
                "precipitation_probability_max": "Rain Chance (%)",
                "date": "Date",
            },
            title="Daily Rain Probability",
        )
        fig_rain.update_traces(marker_color="#4a90d9")
        st.plotly_chart(fig_rain, use_container_width=True)

with right:
    st.subheader("⏰ Next 24 Hours")
    hourly_df = pd.DataFrame(data["hourly"])
    if not hourly_df.empty:
        # Hourly temperature line chart
        fig_hourly = px.line(
            hourly_df,
            x="time",
            y="temperature_c",
            markers=True,
            labels={"temperature_c": "Temperature (°C)", "time": "Time"},
            title="Hourly Temperature",
        )
        st.plotly_chart(fig_hourly, use_container_width=True)

    # Location map
    st.subheader("📍 Location Map")
    map_df = pd.DataFrame([{
        "City":             place["name"],
        "Latitude":         place["latitude"],
        "Longitude":        place["longitude"],
        "Temperature (°C)": current.get("temperature_c"),
    }])
    fig_map = px.scatter_geo(
        map_df,
        lat="Latitude",
        lon="Longitude",
        hover_name="City",
        hover_data={
            "Temperature (°C)": True,
            "Latitude": False,
            "Longitude": False,
        },
        projection="natural earth",
        title=f"{place['name']} · current conditions",
    )
    fig_map.update_traces(marker={"size": 14, "color": "#e45756"})
    fig_map.update_geos(
        showland=True,     landcolor="#edf2f4",
        showcountries=True, countrycolor="#b8c4cc",
        showocean=True,    oceancolor="#e9f3f8",
    )
    st.plotly_chart(fig_map, use_container_width=True)

# ---------------------------------------------------------------------------
# Expandable raw data view
# ---------------------------------------------------------------------------
with st.expander("📊 View raw forecast data"):
    tab_daily, tab_hourly = st.tabs(["Daily", "Hourly"])
    with tab_daily:
        st.dataframe(
            pd.DataFrame(data["daily"]),
            use_container_width=True,
            hide_index=True,
        )
    with tab_hourly:
        st.dataframe(
            pd.DataFrame(data["hourly"]),
            use_container_width=True,
            hide_index=True,
        )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "Risk levels use educational project thresholds — they are **not official "
    "government warnings**. Follow your local weather service for authoritative "
    "guidance.  ·  Data: [Open-Meteo](https://open-meteo.com/)"
)
