"""
alerts.py — Rule-based weather risk alerts.

Design goals:
  • Pure function: build_alerts() has no side-effects and no global state.
  • None-safe: missing or null measurements are silently skipped (no crash).
  • Transparent: every alert carries the measured value so the user can see
    why the rule fired.
  • Educational: thresholds are clearly documented and are NOT official
    government warnings. Follow your local meteorological service.

Alert levels:
  "high"     — Colour red in the dashboard. Strongly consider action.
  "moderate" — Colour orange/yellow. Worth monitoring.
  "info"     — Colour green. All measurements below alert thresholds.

Alert kinds (categories):
  rain, rain_amount, heat, humidity, wind, air_quality, clear
"""

from typing import Any


# ---------------------------------------------------------------------------
# Threshold constants — change these to customise the project.
# Units are noted after each value.
# ---------------------------------------------------------------------------

# Rain probability (%)
RAIN_MODERATE_PCT = 40
RAIN_HIGH_PCT = 70

# Precipitation amount (mm in the current observation period)
RAIN_HEAVY_MM = 20

# Temperature (°C)
TEMP_MODERATE_C = 35
TEMP_HIGH_C = 40

# Relative humidity (%)
HUMIDITY_MODERATE_PCT = 85
HUMIDITY_HIGH_PCT = 95

# Wind speed (km/h)
WIND_MODERATE_KMH = 40
WIND_HIGH_KMH = 60

# US Air Quality Index (dimensionless, 0–500+)
AQI_MODERATE = 101   # "Unhealthy for Sensitive Groups" boundary
AQI_HIGH = 151       # "Unhealthy" boundary

# WMO present-weather codes for thunderstorm observations
STORM_WMO_CODES = frozenset({95, 96, 99})


def build_alerts(weather: dict[str, Any]) -> list[dict[str, str]]:
    """
    Evaluate current weather measurements and return a list of alert dicts.

    Parameters
    ----------
    weather : dict
        A current-conditions dictionary.  Keys that may be present:
        precipitation_probability (%), precipitation_mm (mm),
        temperature_c (°C), apparent_temperature_c (°C),
        relative_humidity_percent (%), wind_speed_kmh (km/h),
        wind_direction_degrees (°), us_aqi (US AQI index).

    Returns
    -------
    list[dict]
        Each dict has keys: level, kind, title, message.
        Always contains at least one element.
    """
    alerts: list[dict[str, str]] = []

    # Helper so callers never forget a key ---------------------------------
    def add(level: str, kind: str, title: str, message: str) -> None:
        alerts.append(
            {"level": level, "kind": kind, "title": title, "message": message}
        )

    # ------------------------------------------------------------------
    # Rule 1: Rain probability
    # We use the word "rain" rather than "storm" because probability
    # alone does not confirm a storm — that requires storm codes.
    # ------------------------------------------------------------------
    rain = weather.get("precipitation_probability")
    if rain is not None:
        if rain >= RAIN_HIGH_PCT:
            add(
                "high", "rain",
                "High chance of rain",
                f"Precipitation probability is {rain:.0f}% — carry a waterproof layer.",
            )
        elif rain >= RAIN_MODERATE_PCT:
            add(
                "moderate", "rain",
                "Rain possible",
                f"Precipitation probability is {rain:.0f}% — an umbrella may be useful.",
            )

    # ------------------------------------------------------------------
    # Rule 2: Precipitation amount (current observation period)
    # ------------------------------------------------------------------
    rain_mm = weather.get("precipitation_mm")
    if rain_mm is not None and rain_mm >= RAIN_HEAVY_MM:
        add(
            "high", "rain_amount",
            "Heavy precipitation",
            f"Current precipitation is {rain_mm:.1f} mm — expect reduced visibility and possible surface flooding.",
        )

    # ------------------------------------------------------------------
    # Rule 3: Temperature (heat)
    # ------------------------------------------------------------------
    temp = weather.get("temperature_c")
    if temp is not None:
        if temp >= TEMP_HIGH_C:
            add(
                "high", "heat",
                "Extreme heat",
                f"Temperature is {temp:.1f} °C — limit strenuous outdoor activity and stay hydrated.",
            )
        elif temp >= TEMP_MODERATE_C:
            add(
                "moderate", "heat",
                "High temperature",
                f"Temperature is {temp:.1f} °C — stay hydrated and seek shade during peak hours.",
            )

    # ------------------------------------------------------------------
    # Rule 4: Relative humidity
    # ------------------------------------------------------------------
    humidity = weather.get("relative_humidity_percent")
    if humidity is not None:
        if humidity >= HUMIDITY_HIGH_PCT:
            add(
                "high", "humidity",
                "Very high humidity",
                f"Relative humidity is {humidity:.0f}% — heat feels significantly worse; limit exertion.",
            )
        elif humidity >= HUMIDITY_MODERATE_PCT:
            add(
                "moderate", "humidity",
                "High humidity",
                f"Relative humidity is {humidity:.0f}% — the air may feel muggy.",
            )

    # ------------------------------------------------------------------
    # Rule 5: Wind speed
    # We do NOT label this a storm — WMO weather codes would be needed
    # for that classification. High wind alone can still be dangerous.
    # ------------------------------------------------------------------
    wind = weather.get("wind_speed_kmh")
    if wind is not None:
        if wind >= WIND_HIGH_KMH:
            add(
                "high", "wind",
                "Very strong wind",
                f"Wind speed is {wind:.0f} km/h — secure loose outdoor objects; difficult cycling/walking.",
            )
        elif wind >= WIND_MODERATE_KMH:
            add(
                "moderate", "wind",
                "Strong wind",
                f"Wind speed is {wind:.0f} km/h — hold on to lightweight items outdoors.",
            )

    # ------------------------------------------------------------------
    # Rule 6: Air quality (US AQI) — only when the value is available
    # ------------------------------------------------------------------
    aqi = weather.get("us_aqi")
    if aqi is not None:
        if aqi >= AQI_HIGH:
            add(
                "high", "air_quality",
                "Unhealthy air quality",
                f"US AQI is {aqi:.0f} — sensitive groups and healthy adults should limit prolonged outdoor exposure.",
            )
        elif aqi >= AQI_MODERATE:
            add(
                "moderate", "air_quality",
                "Elevated AQI — sensitive groups affected",
                f"US AQI is {aqi:.0f} — people with respiratory or heart conditions should reduce strenuous outdoor activity.",
            )

    # ------------------------------------------------------------------
    # Rule 7: Storm-code detection (WMO codes from Open-Meteo)
    # Codes 95, 96, 99 indicate thunderstorm observations, not forecasts.
    # We only flag this when the provider explicitly reports a storm code.
    # ------------------------------------------------------------------
    wmo = weather.get("weather_code")
    try:
        is_thunderstorm = wmo is not None and int(wmo) in STORM_WMO_CODES
    except (TypeError, ValueError):
        is_thunderstorm = False
    if is_thunderstorm:
        add(
            "high", "storm",
            "Thunderstorm reported",
            f"WMO weather code {wmo} indicates a thunderstorm is currently occurring. Avoid open areas.",
        )

    # ------------------------------------------------------------------
    # Fallback: everything is fine
    # ------------------------------------------------------------------
    if not alerts:
        add(
            "info", "clear",
            "No elevated risks detected",
            "All current measurements are below this project's alert thresholds.",
        )

    return alerts


def threshold_summary() -> dict[str, Any]:
    """Return the current threshold constants as a dict (for the /thresholds endpoint)."""
    return {
        "rain_moderate_pct": RAIN_MODERATE_PCT,
        "rain_high_pct": RAIN_HIGH_PCT,
        "rain_heavy_mm": RAIN_HEAVY_MM,
        "temp_moderate_c": TEMP_MODERATE_C,
        "temp_high_c": TEMP_HIGH_C,
        "humidity_moderate_pct": HUMIDITY_MODERATE_PCT,
        "humidity_high_pct": HUMIDITY_HIGH_PCT,
        "wind_moderate_kmh": WIND_MODERATE_KMH,
        "wind_high_kmh": WIND_HIGH_KMH,
        "aqi_moderate": AQI_MODERATE,
        "aqi_high": AQI_HIGH,
        "storm_wmo_codes": sorted(STORM_WMO_CODES),
        "note": (
            "These are educational project defaults, not official warning thresholds. "
            "Follow your local meteorological service for authoritative guidance."
        ),
    }
