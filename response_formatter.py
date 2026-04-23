from datetime import date, datetime
from typing import Optional


WEATHER_EMOJI_MAP = {
    "clear": "☀️",
    "sun": "☀️",
    "cloud": "☁️",
    "overcast": "☁️",
    "rain": "🌧️",
    "drizzle": "🌦️",
    "thunder": "⛈️",
    "storm": "⛈️",
    "snow": "❄️",
    "mist": "🌫️",
    "fog": "🌫️",
    "haze": "🌫️",
    "smoke": "🌫️",
    "wind": "💨",
    "tornado": "🌪️",
    "default": "🌡️",
}


def get_weather_emoji(description: str) -> str:
    desc_lower = description.lower()
    for keyword, emoji in WEATHER_EMOJI_MAP.items():
        if keyword in desc_lower:
            return emoji
    return WEATHER_EMOJI_MAP["default"]


def format_date_header(city: str) -> str:
    city_upper = city.upper()
    title = f"📍 {city_upper} — WEATHER FORECAST"
    width = max(len(title) + 2, 32)
    top = "╔" + "═" * width + "╗"
    mid = "║ " + title + " " * (width - len(title) - 1) + "║"
    bot = "╚" + "═" * width + "╝"
    return f"{top}\n{mid}\n{bot}"


def format_single_day(day_data: dict) -> str:
    """Format a single day weather block."""
    day_date = day_data["date"]
    if isinstance(day_date, str):
        day_date = datetime.strptime(day_date, "%Y-%m-%d").date()

    date_str = day_date.strftime("%d %b %Y")
    weekday = day_date.strftime("%A")
    description = day_data.get("description", "N/A")
    emoji = get_weather_emoji(description)

    temp_max = day_data.get("temp_max", day_data.get("temp"))
    temp_min = day_data.get("temp_min", day_data.get("temp"))
    temp_avg = day_data.get("temp_avg", day_data.get("temp"))

    humidity = day_data.get("humidity", "N/A")
    wind = day_data.get("wind_speed", "N/A")
    rain_chance = day_data.get("rain_chance")

    lines = [
        f"🗓️  {date_str}",
        "─" * 38,
        f"📅 {weekday}, {date_str}",
        f"{emoji} {description}",
    ]

    if temp_max is not None and temp_min is not None:
        avg_str = f" | Avg: {temp_avg}°C" if temp_avg is not None else ""
        lines.append(f"🌡️  High: {temp_max}°C | Low: {temp_min}°C{avg_str}")
    elif day_data.get("temp") is not None:
        lines.append(f"🌡️  Temp: {day_data['temp']}°C")

    if rain_chance is not None:
        lines.append(f"🌧️  Rain chance: {rain_chance}%")

    if humidity != "N/A":
        lines.append(f"💧 Humidity: {humidity}%")

    if wind != "N/A":
        lines.append(f"💨 Wind: {wind} km/h")

    return "\n".join(lines)


def format_current_weather_response(weather: dict) -> str:
    """Format current weather response."""
    city = weather.get("city", "Unknown")
    header = format_header_simple(city, "CURRENT WEATHER")
    body = format_single_day(weather)
    return f"{header}\n{body}"


def format_header_simple(city: str, label: str) -> str:
    city_upper = city.upper()
    title = f"📍 {city_upper} — {label}"
    width = max(len(title) + 2, 32)
    top = "╔" + "═" * width + "╗"
    mid = "║ " + title + " " * (width - len(title) - 1) + "║"
    bot = "╚" + "═" * width + "╝"
    return f"{top}\n{mid}\n{bot}"


def format_specific_date_response(weather: dict) -> str:
    """Format response for a specific date query."""
    city = weather.get("city", "Unknown")
    header = format_header_simple(city, "WEATHER FORECAST")
    body = format_single_day(weather)
    return f"{header}\n{body}"


def format_forecast_response(forecast_list: list, days: Optional[int] = None) -> str:
    """Format multi-day forecast response."""
    if not forecast_list:
        return "No forecast data available."

    city = forecast_list[0].get("city", "Unknown")
    data = forecast_list[:days] if days else forecast_list

    label = f"{len(data)}-DAY FORECAST"
    header = format_header_simple(city, label)

    day_blocks = []
    for day in data:
        day_blocks.append(format_single_day(day))

    separator = "\n\n" + "━" * 38 + "\n\n"
    body = separator.join(day_blocks)

    return f"{header}\n\n{body}"


def format_past_date_error(city: str, requested_date: date) -> str:
    date_str = requested_date.strftime("%d %b %Y") if requested_date else "that date"
    return (
        f"⚠️ Sorry! I cannot show weather for {date_str} because it's in the past.\n"
        f"I can only provide:\n"
        f"  • Current weather 🌤️\n"
        f"  • Forecast for today and up to 8 days ahead 📅\n\n"
        f"Try asking: \"What's the weather in {city} today?\" or "
        f"\"Forecast for {city} for next 5 days\""
    )


def format_city_not_found_error(city: str) -> str:
    return (
        f"⚠️ I couldn't find weather data for \"{city}\".\n"
        f"Please check the city name and try again.\n"
        f"Example: \"Weather in London\" or \"Forecast for New York\""
    )


def format_date_out_of_range_error(city: str) -> str:
    return (
        f"⚠️ The requested date is too far ahead.\n"
        f"I can only provide forecasts up to 5 days from today for {city}.\n"
        f"Try a date within the next 5 days!"
        f"Note: Forecast is limited to the next 5 days due to free API limitations."
    )
