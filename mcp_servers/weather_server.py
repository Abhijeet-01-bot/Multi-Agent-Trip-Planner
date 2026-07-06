import os
import requests
from collections import defaultdict

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger_config import setup_logger


load_dotenv()

logger = setup_logger(__name__)

mcp = FastMCP("WeatherServer")


def get_api_key():
    """
    Reads OpenWeather API key from .env file.
    """

    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        logger.warning("OPENWEATHER_API_KEY is missing in .env")
        return None

    return api_key.strip().replace('"', "").replace("'", "")


def summarize_forecast(forecast_items):
    """
    Summarizes OpenWeather 5-day / 3-hour forecast into day-wise forecast.
    """

    logger.info("Summarizing forecast data")

    daily = defaultdict(list)

    for item in forecast_items:
        dt_txt = item.get("dt_txt", "")
        date_only = dt_txt.split(" ")[0] if dt_txt else "unknown"

        main = item.get("main", {})
        weather = item.get("weather", [{}])[0]
        wind = item.get("wind", {})
        rain = item.get("rain", {})

        daily[date_only].append(
            {
                "time": dt_txt,
                "temperature_c": main.get("temp"),
                "humidity_percent": main.get("humidity"),
                "description": weather.get("description"),
                "wind_speed": wind.get("speed"),
                "rain_3h_mm": rain.get("3h", 0),
            }
        )

    output = []

    for date_value, entries in daily.items():
        temps = [
            item["temperature_c"]
            for item in entries
            if item.get("temperature_c") is not None
        ]

        humidities = [
            item["humidity_percent"]
            for item in entries
            if item.get("humidity_percent") is not None
        ]

        descriptions = [
            item["description"]
            for item in entries
            if item.get("description")
        ]

        rain_total = sum(
            item.get("rain_3h_mm", 0)
            for item in entries
        )

        probable_condition = None

        if descriptions:
            probable_condition = max(
                set(descriptions),
                key=descriptions.count
            )

        output.append(
            {
                "date": date_value,
                "min_temperature_c": min(temps) if temps else None,
                "max_temperature_c": max(temps) if temps else None,
                "avg_humidity_percent": (
                    round(sum(humidities) / len(humidities), 2)
                    if humidities
                    else None
                ),
                "probable_condition": probable_condition,
                "rain_expected": rain_total > 0,
                "total_rain_3h_mm": round(rain_total, 2),
            }
        )

    logger.info("Forecast summarized successfully")

    return output


def build_advice(description, temperature, humidity, wind_speed):
    """
    Builds travel advice based on weather condition.
    """

    logger.info(
        "Building weather advice using description=%s, temperature=%s, humidity=%s, wind_speed=%s",
        description,
        temperature,
        humidity,
        wind_speed,
    )

    description = str(description).lower()
    advice = []

    if "rain" in description or "storm" in description:
        advice.append(
            "Rain risk detected. Carry umbrella/raincoat and avoid risky outdoor activities."
        )

    if temperature is not None and temperature >= 35:
        advice.append(
            "High temperature detected. Avoid afternoon outdoor sightseeing."
        )

    if humidity is not None and humidity >= 80:
        advice.append(
            "High humidity expected. Stay hydrated."
        )

    if wind_speed is not None and wind_speed >= 10:
        advice.append(
            "High wind speed detected. Avoid boating or water activities."
        )

    if not advice:
        advice.append(
            "Weather looks manageable for normal sightseeing with basic precautions."
        )

    final_advice = " ".join(advice)

    logger.info("Weather advice generated: %s", final_advice)

    return final_advice


@mcp.tool()
def get_weather(city):
    """
    MCP tool that fetches current weather and forecast for a city
    using OpenWeather API.
    """

    logger.info("MCP Weather Server called for city: %s", city)

    api_key = get_api_key()

    if not api_key:
        logger.error("Weather data unavailable because OPENWEATHER_API_KEY is missing")

        return {
            "weather_source": "MCP Weather Server + OpenWeatherMap",
            "current_weather": {
                "success": False,
                "error": "OPENWEATHER_API_KEY missing in .env"
            },
            "forecast": {
                "success": False,
                "daily_forecast": []
            },
            "weather_analysis": {
                "travel_advice": "Weather data unavailable because API key is missing."
            }
        }

    current_url = "https://api.openweathermap.org/data/2.5/weather"
    forecast_url = "https://api.openweathermap.org/data/2.5/forecast"

    try:
        logger.info("Calling OpenWeather current weather API for city: %s", city)

        current_response = requests.get(
            current_url,
            params={
                "q": city,
                "appid": api_key,
                "units": "metric",
            },
            timeout=15,
        )

        logger.info(
            "OpenWeather current API status code: %s",
            current_response.status_code,
        )

        logger.info("Calling OpenWeather forecast API for city: %s", city)

        forecast_response = requests.get(
            forecast_url,
            params={
                "q": city,
                "appid": api_key,
                "units": "metric",
            },
            timeout=15,
        )

        logger.info(
            "OpenWeather forecast API status code: %s",
            forecast_response.status_code,
        )

        current_weather = {
            "success": False,
            "api_used": "OpenWeatherMap Current Weather API",
            "error": current_response.text,
        }

        forecast = {
            "success": False,
            "api_used": "OpenWeatherMap 5 Day Forecast API",
            "error": forecast_response.text,
            "daily_forecast": [],
        }

        travel_advice = "Weather data could not be analyzed."

        if current_response.status_code == 200:
            logger.info("OpenWeather current weather API call successful")

            data = current_response.json()

            main = data.get("main", {})
            weather = data.get("weather", [{}])[0]
            wind = data.get("wind", {})
            clouds = data.get("clouds", {})
            rain = data.get("rain", {})

            temperature = main.get("temp")
            humidity = main.get("humidity")
            wind_speed = wind.get("speed")
            description = weather.get("description")

            current_weather = {
                "success": True,
                "api_used": "OpenWeatherMap Current Weather API",
                "city": data.get("name", city),
                "country": data.get("sys", {}).get("country"),
                "temperature_c": temperature,
                "feels_like_c": main.get("feels_like"),
                "humidity_percent": humidity,
                "pressure_hpa": main.get("pressure"),
                "wind_speed": wind_speed,
                "cloudiness_percent": clouds.get("all"),
                "rain_1h_mm": rain.get("1h", 0),
                "condition": weather.get("main"),
                "description": description,
            }

            travel_advice = build_advice(
                description,
                temperature,
                humidity,
                wind_speed,
            )

        else:
            logger.warning(
                "OpenWeather current weather API failed: %s",
                current_response.text,
            )

        if forecast_response.status_code == 200:
            logger.info("OpenWeather forecast API call successful")

            forecast_data = forecast_response.json()
            forecast_items = forecast_data.get("list", [])

            forecast = {
                "success": True,
                "api_used": "OpenWeatherMap 5 Day / 3 Hour Forecast API",
                "city": forecast_data.get("city", {}).get("name", city),
                "country": forecast_data.get("city", {}).get("country"),
                "daily_forecast": summarize_forecast(forecast_items),
            }

        else:
            logger.warning(
                "OpenWeather forecast API failed: %s",
                forecast_response.text,
            )

        weather_result = {
            "weather_source": "MCP Weather Server + OpenWeatherMap",
            "current_weather": current_weather,
            "forecast": forecast,
            "weather_analysis": {
                "travel_advice": travel_advice,
                "used_for_planning": True,
            },
        }

        logger.info("Weather result generated successfully for city: %s", city)

        return weather_result

    except Exception as e:
        logger.error("Weather MCP Server exception: %s", str(e))

        return {
            "weather_source": "MCP Weather Server + OpenWeatherMap",
            "current_weather": {
                "success": False,
                "error": str(e),
            },
            "forecast": {
                "success": False,
                "daily_forecast": [],
                "error": str(e),
            },
            "weather_analysis": {
                "travel_advice": "Weather data could not be fetched due to an exception.",
            },
        }


if __name__ == "__main__":
    logger.info("Starting Weather MCP Server")
    mcp.run()
