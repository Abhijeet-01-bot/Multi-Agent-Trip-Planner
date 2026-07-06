import os
import requests
import certifi
from typing import Dict, Any, List
from datetime import datetime



def get_current_weather(destination: str) -> Dict[str, Any]:
    """
    Fetches current weather from OpenWeatherMap.
    """

    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        return {
            "success": False,
            "api_used": False,
            "message": "OPENWEATHER_API_KEY is missing."
        }

    if not destination:
        return {
            "success": False,
            "api_used": False,
            "message": "Destination is missing."
        }

    try:
        print("OpenWeather API Call: Current Weather")

        url = "https://api.openweathermap.org/data/2.5/weather"

        params = {
            "q": destination,
            "appid": api_key,
            "units": "metric"
        }

        response = requests.get(
    url,
    params=params,
    timeout=10,
    verify=certifi.where()
)

        if response.status_code != 200:
            return {
                "success": False,
                "api_used": True,
                "status_code": response.status_code,
                "message": response.text
            }

        data = response.json()

        weather = data.get("weather", [{}])[0]
        main = data.get("main", {})
        wind = data.get("wind", {})
        clouds = data.get("clouds", {})
        rain = data.get("rain", {})
        sys_data = data.get("sys", {})

        return {
            "success": True,
            "api_used": True,
            "location": data.get("name"),
            "country": sys_data.get("country"),
            "description": weather.get("description"),
            "main_condition": weather.get("main"),
            "temperature_c": main.get("temp"),
            "feels_like_c": main.get("feels_like"),
            "min_temp_c": main.get("temp_min"),
            "max_temp_c": main.get("temp_max"),
            "humidity_percent": main.get("humidity"),
            "pressure_hpa": main.get("pressure"),
            "wind_speed_mps": wind.get("speed"),
            "wind_direction_degree": wind.get("deg"),
            "cloudiness_percent": clouds.get("all"),
            "rain_last_1h_mm": rain.get("1h", 0),
            "visibility_m": data.get("visibility"),
            "timestamp": data.get("dt")
        }

    except Exception as e:
        return {
            "success": False,
            "api_used": True,
            "message": str(e)
        }


def get_5_day_forecast(destination: str) -> Dict[str, Any]:
    """
    Fetches 5-day / 3-hour forecast from OpenWeatherMap.
    """

    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        return {
            "success": False,
            "api_used": False,
            "message": "OPENWEATHER_API_KEY is missing.",
            "daily_summary": []
        }

    if not destination:
        return {
            "success": False,
            "api_used": False,
            "message": "Destination is missing.",
            "daily_summary": []
        }

    try:
        print("OpenWeather API Call: 5 Day Forecast")

        url = "https://api.openweathermap.org/data/2.5/forecast"

        params = {
            "q": destination,
            "appid": api_key,
            "units": "metric"
        }

        response = requests.get(
    url,
    params=params,
    timeout=10,
    verify=certifi.where()
)

        if response.status_code != 200:
            return {
                "success": False,
                "api_used": True,
                "status_code": response.status_code,
                "message": response.text,
                "daily_summary": []
            }

        data = response.json()
        forecast_list = data.get("list", [])

        grouped = {}

        for item in forecast_list:
            date_text = item.get("dt_txt", "")
            date_only = date_text.split(" ")[0]

            main = item.get("main", {})
            weather = item.get("weather", [{}])[0]
            wind = item.get("wind", {})
            clouds = item.get("clouds", {})
            rain = item.get("rain", {})

            if date_only not in grouped:
                grouped[date_only] = {
                    "date": date_only,
                    "temps": [],
                    "humidity": [],
                    "conditions": [],
                    "wind_speeds": [],
                    "cloudiness": [],
                    "rain_mm": []
                }

            grouped[date_only]["temps"].append(main.get("temp"))
            grouped[date_only]["humidity"].append(main.get("humidity"))
            grouped[date_only]["conditions"].append(weather.get("description"))
            grouped[date_only]["wind_speeds"].append(wind.get("speed"))
            grouped[date_only]["cloudiness"].append(clouds.get("all"))
            grouped[date_only]["rain_mm"].append(rain.get("3h", 0))

        daily_summary = []

        for date, values in grouped.items():
            temps = [x for x in values["temps"] if x is not None]
            humidity = [x for x in values["humidity"] if x is not None]
            wind_speeds = [x for x in values["wind_speeds"] if x is not None]
            cloudiness = [x for x in values["cloudiness"] if x is not None]
            rain_mm = [x for x in values["rain_mm"] if x is not None]

            most_common_condition = max(
                set(values["conditions"]),
                key=values["conditions"].count
            ) if values["conditions"] else "Not available"

            daily_summary.append(
                {
                    "date": date,
                    "avg_temp_c": round(sum(temps) / len(temps), 1) if temps else None,
                    "min_temp_c": round(min(temps), 1) if temps else None,
                    "max_temp_c": round(max(temps), 1) if temps else None,
                    "avg_humidity_percent": round(sum(humidity) / len(humidity), 1) if humidity else None,
                    "avg_wind_speed_mps": round(sum(wind_speeds) / len(wind_speeds), 1) if wind_speeds else None,
                    "avg_cloudiness_percent": round(sum(cloudiness) / len(cloudiness), 1) if cloudiness else None,
                    "total_rain_mm": round(sum(rain_mm), 1) if rain_mm else 0,
                    "dominant_condition": most_common_condition
                }
            )

        return {
            "success": True,
            "api_used": True,
            "city": data.get("city", {}).get("name"),
            "country": data.get("city", {}).get("country"),
            "daily_summary": daily_summary
        }

    except Exception as e:
        return {
            "success": False,
            "api_used": True,
            "message": str(e),
            "daily_summary": []
        }


def analyze_weather_for_trip(current_weather: Dict[str, Any], forecast: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts OpenWeather data into travel planning recommendations.
    """

    risks = []
    recommendations = []
    activities_to_avoid = []

    if current_weather.get("success"):
        temp = current_weather.get("temperature_c")
        humidity = current_weather.get("humidity_percent")
        wind_speed = current_weather.get("wind_speed_mps")
        rain = current_weather.get("rain_last_1h_mm", 0)
        condition = (current_weather.get("description") or "").lower()

        if temp is not None and temp >= 35:
            risks.append("High temperature may cause discomfort during afternoon outdoor activities.")
            recommendations.append("Prefer sightseeing in the morning and evening.")
            recommendations.append("Keep indoor or shaded activities during afternoon.")

        if humidity is not None and humidity >= 80:
            risks.append("High humidity may make outdoor activities tiring.")
            recommendations.append("Add breaks, hydration time, and avoid overpacked schedules.")

        if wind_speed is not None and wind_speed >= 8:
            risks.append("Wind speed is relatively high.")
            recommendations.append("Avoid risky sea or adventure activities if local advisories warn against them.")
            activities_to_avoid.append("Risky water activities")

        if rain and rain > 0:
            risks.append("Recent rain detected.")
            recommendations.append("Keep flexible slots and carry rain protection.")
            activities_to_avoid.append("Long outdoor-only plans")

        if "rain" in condition or "storm" in condition:
            risks.append("Rain or storm-like condition detected.")
            recommendations.append("Prefer cafes, museums, indoor attractions, and flexible sightseeing.")
            activities_to_avoid.extend(["Water sports", "Island trips", "Long exposed outdoor plans"])

    if forecast.get("success"):
        for day in forecast.get("daily_summary", []):
            if day.get("total_rain_mm", 0) > 5:
                risks.append(f"Rain expected on {day.get('date')}.")
                recommendations.append("Keep backup indoor activities for rainy days.")
                activities_to_avoid.append("Outdoor-heavy schedule")

            if day.get("max_temp_c") and day.get("max_temp_c") >= 35:
                risks.append(f"High temperature expected on {day.get('date')}.")
                recommendations.append("Avoid afternoon outdoor sightseeing on hot days.")

            condition = (day.get("dominant_condition") or "").lower()

            if "rain" in condition or "storm" in condition:
                risks.append(f"Rain-prone weather expected on {day.get('date')}.")
                recommendations.append("Plan flexible travel buffers and indoor alternatives.")

    if not risks:
        risks.append("No major weather risk detected from OpenWeather data.")
        recommendations.append("Proceed with a balanced itinerary.")

    return {
        "risk_level": "Medium to High" if len(risks) >= 3 else "Low to Medium",
        "risks": list(set(risks)),
        "recommendations": list(set(recommendations)),
        "activities_to_avoid": list(set(activities_to_avoid))
    }