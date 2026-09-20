from __future__ import annotations

import re
from datetime import datetime

import requests


def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def evaluate_expression(question: str) -> str:
    expr = question.replace("x", "*")
    expr = expr.replace("÷", "/")
    expr = expr.replace("^", "**")
    try:
        result = eval(expr, {"__builtins__": {}}, {})
        return str(result)
    except Exception:
        return "I can do the arithmetic, but the expression is not valid."


def extract_location(question: str) -> str:
    q = question.strip().lower()

    patterns = [
        r"\b(?:in|for|at|near)\s+([a-z][a-z\s'-]+?)(?:\s+today|\s+now|\s+tomorrow|$)",
        r"\b(?:weather|forecast)\s+(?:in|for|at|near)\s+([a-z][a-z\s'-]+?)(?:\s+today|\s+now|\s+tomorrow|$)",
        r"\b(?:what's|what is|what's the|what is the)\s+(?:weather|forecast)\s+(?:in|for|at|near)\s+([a-z][a-z\s'-]+?)(?:\s+today|\s+now|\s+tomorrow|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, q, flags=re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            if location:
                return location.title()

    if re.search(r"\bweather\b|\bforecast\b", q, flags=re.IGNORECASE):
        return "London"

    return "London"


def get_weather_for_location(question: str, latitude: float | None = None, longitude: float | None = None) -> str:
    if latitude is not None and longitude is not None:
        try:
            forecast_resp = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m,relative_humidity_2m",
                    "timezone": "auto",
                },
                timeout=20,
            )
            forecast_resp.raise_for_status()
            forecast = forecast_resp.json()
            current = forecast.get("current", {})
            temp = current.get("temperature_2m")
            feels_like = current.get("apparent_temperature")
            humidity = current.get("relative_humidity_2m")
            wind = current.get("wind_speed_10m")
            weather_code = current.get("weather_code")

            weather_map = {
                0: "clear sky",
                1: "mainly clear",
                2: "partly cloudy",
                3: "overcast",
                45: "foggy",
                48: "depositing rime fog",
                51: "light drizzle",
                53: "moderate drizzle",
                55: "dense drizzle",
                56: "light freezing drizzle",
                57: "dense freezing drizzle",
                61: "slight rain",
                63: "moderate rain",
                65: "heavy rain",
                66: "light freezing rain",
                67: "heavy freezing rain",
                71: "slight snow",
                73: "moderate snow",
                75: "heavy snow",
                77: "snow grains",
                80: "light rain showers",
                81: "moderate rain showers",
                82: "violent rain showers",
                85: "light snow showers",
                86: "heavy snow showers",
                95: "thunderstorm",
                96: "thunderstorm with slight hail",
                99: "thunderstorm with heavy hail",
            }

            condition = weather_map.get(weather_code, "unknown conditions")
            return (
                f"The current weather at your location is {condition}. "
                f"Temperature is {temp}°C (feels like {feels_like}°C), humidity is {humidity}%, and wind speed is {wind} km/h."
            )
        except requests.RequestException:
            return "I couldn't fetch the live weather for your current location right now. Please try again in a moment."

    location = extract_location(question)

    try:
        geo_resp = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": location,
                "count": 1,
                "language": "en",
                "format": "json",
            },
            timeout=20,
        )
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()

        if not geo_data.get("results"):
            return f"I couldn't find weather data for '{location}'. Please specify a city or town."

        result = geo_data["results"][0]
        lat = result["latitude"]
        lon = result["longitude"]
        city_name = result.get("name", location)
        country = result.get("country", "")

        forecast_resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m,relative_humidity_2m",
                "timezone": "auto",
            },
            timeout=20,
        )
        forecast_resp.raise_for_status()
        forecast = forecast_resp.json()

        current = forecast.get("current", {})
        temp = current.get("temperature_2m")
        feels_like = current.get("apparent_temperature")
        humidity = current.get("relative_humidity_2m")
        wind = current.get("wind_speed_10m")
        weather_code = current.get("weather_code")

        weather_map = {
            0: "clear sky",
            1: "mainly clear",
            2: "partly cloudy",
            3: "overcast",
            45: "foggy",
            48: "depositing rime fog",
            51: "light drizzle",
            53: "moderate drizzle",
            55: "dense drizzle",
            56: "light freezing drizzle",
            57: "dense freezing drizzle",
            61: "slight rain",
            63: "moderate rain",
            65: "heavy rain",
            66: "light freezing rain",
            67: "heavy freezing rain",
            71: "slight snow",
            73: "moderate snow",
            75: "heavy snow",
            77: "snow grains",
            80: "light rain showers",
            81: "moderate rain showers",
            82: "violent rain showers",
            85: "light snow showers",
            86: "heavy snow showers",
            95: "thunderstorm",
            96: "thunderstorm with slight hail",
            99: "thunderstorm with heavy hail",
        }

        condition = weather_map.get(weather_code, "unknown conditions")
        return (
            f"The current weather in {city_name}, {country} is {condition}. "
            f"Temperature is {temp}°C (feels like {feels_like}°C), humidity is {humidity}%, and wind speed is {wind} km/h."
        )
    except requests.RequestException:
        return f"I couldn't fetch the live weather for '{location}' right now. Please try again in a moment."
