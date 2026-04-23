import httpx
from datetime import date, datetime
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org"


async def get_coordinates(city: str) -> Optional[dict]:
    """Get lat/lon for a city using Geocoding API."""
    url = f"{BASE_URL}/geo/1.0/direct"
    params = {
        "q": city,
        "limit": 1,
        "appid": OPENWEATHER_API_KEY,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
        if not data:
            return None
        return {"lat": data[0]["lat"], "lon": data[0]["lon"], "name": data[0]["name"]}


async def get_current_weather(city: str) -> Optional[dict]:
    """Fetch current weather for a city."""
    coords = await get_coordinates(city)
    if not coords:
        return None

    url = f"{BASE_URL}/data/2.5/weather"
    params = {
        "lat": coords["lat"],
        "lon": coords["lon"],
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()

    if response.status_code != 200:
        return None

    return {
        "city": coords["name"],
        "date": date.today(),
        "description": data["weather"][0]["description"].capitalize(),
        "temp": data["main"]["temp"],
        "temp_max": data["main"]["temp_max"],
        "temp_min": data["main"]["temp_min"],
        "humidity": data["main"]["humidity"],
        "wind_speed": round(data["wind"]["speed"] * 3.6, 1),  # m/s to km/h
        "rain_chance": None,  # not available in current endpoint
    }


async def get_forecast(city: str, days: int = 8) -> Optional[list]:
    """
    Fetch forecast for up to 8 days.
    Uses the /data/2.5/forecast endpoint (free tier - 5 day / 3hr intervals)
    then aggregates per day.
    """
    coords = await get_coordinates(city)
    if not coords:
        return None

    url = f"{BASE_URL}/data/2.5/forecast"
    params = {
        "lat": coords["lat"],
        "lon": coords["lon"],
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "cnt": 40,  # max 40 items = ~5 days on free tier
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()

    if response.status_code != 200:
        return None

    # Try One Call API (requires paid plan or One Call 3.0 subscription)
    # If you have access, use this for full 8-day forecast:
    one_call_url = f"{BASE_URL}/data/3.0/onecall"
    one_call_params = {
        "lat": coords["lat"],
        "lon": coords["lon"],
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "exclude": "current,minutely,hourly,alerts",
    }
    async with httpx.AsyncClient() as client:
        oc_response = await client.get(one_call_url, params=one_call_params)

    if oc_response.status_code == 200:
        oc_data = oc_response.json()
        # One Call 3.0 gives up to 8 days of daily forecast
        daily = oc_data.get("daily", [])
        result = []
        for day_data in daily[:days]:
            dt = datetime.fromtimestamp(day_data["dt"])
            pop = round(day_data.get("pop", 0) * 100)  # probability of precipitation
            result.append({
                "city": coords["name"],
                "date": dt.date(),
                "description": day_data["weather"][0]["description"].capitalize(),
                "temp_max": round(day_data["temp"]["max"], 1),
                "temp_min": round(day_data["temp"]["min"], 1),
                "temp_avg": round((day_data["temp"]["max"] + day_data["temp"]["min"]) / 2, 1),
                "humidity": day_data["humidity"],
                "wind_speed": round(day_data["wind_speed"] * 3.6, 1),
                "rain_chance": pop,
            })
        return result

    # Fallback: aggregate free-tier 3-hourly forecast by day (up to 5 days)
    daily_map = {}
    for item in data["list"]:
        dt = datetime.fromtimestamp(item["dt"])
        day_key = dt.date()
        if day_key not in daily_map:
            daily_map[day_key] = {
                "temps": [],
                "descriptions": [],
                "humidity": [],
                "wind": [],
                "pop": [],
            }
        daily_map[day_key]["temps"].append(item["main"]["temp"])
        daily_map[day_key]["descriptions"].append(item["weather"][0]["description"])
        daily_map[day_key]["humidity"].append(item["main"]["humidity"])
        daily_map[day_key]["wind"].append(item["wind"]["speed"])
        daily_map[day_key]["pop"].append(item.get("pop", 0) * 100)

    result = []
    for day_key in sorted(daily_map.keys())[:days]:
        d = daily_map[day_key]
        temps = d["temps"]
        result.append({
            "city": coords["name"],
            "date": day_key,
            "description": max(set(d["descriptions"]), key=d["descriptions"].count).capitalize(),
            "temp_max": round(max(temps), 1),
            "temp_min": round(min(temps), 1),
            "temp_avg": round(sum(temps) / len(temps), 1),
            "humidity": round(sum(d["humidity"]) / len(d["humidity"])),
            "wind_speed": round((sum(d["wind"]) / len(d["wind"])) * 3.6, 1),
            "rain_chance": round(max(d["pop"])),
        })

    return result


async def get_weather_for_specific_date(city: str, target_date: date) -> Optional[dict]:
    """
    Get weather for a specific date.
    - If date == today: use current weather
    - If date > today (up to 8 days ahead): use forecast
    - If date < today: return None (past date)
    """
    today = date.today()

    if target_date < today:
        return {"error": "past_date"}

    if target_date == today:
        return await get_current_weather(city)

    # Future date - pull from forecast
    days_ahead = (target_date - today).days + 1  # +1 to ensure we include target day
    forecast = await get_forecast(city, days=min(days_ahead, 8))

    if not forecast:
        return None

    for day in forecast:
        if day["date"] == target_date:
            return day

    return {"error": "date_out_of_range"}
