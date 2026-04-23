# from datetime import datetime, date, timezone
# from typing import Optional
# import logging

# from weather_service import (
#     get_current_weather,
#     get_forecast,
#     get_weather_for_specific_date,
# )
# from response_formatter import (
#     format_current_weather_response,
#     format_forecast_response,
#     format_specific_date_response,
#     format_past_date_error,
#     format_city_not_found_error,
#     format_date_out_of_range_error,
# )

# logger = logging.getLogger(__name__)


# def extract_city(parameters: dict) -> Optional[str]:
#     """Extract city from Dialogflow parameters. Handles geo-city object or string."""
#     city = parameters.get("city") or parameters.get("geo-city")
#     if isinstance(city, dict):
#         # Dialogflow sometimes returns {"city": "Toronto", "country": "Canada"}
#         return city.get("city") or city.get("name")
#     return city if city else None


# def extract_date(parameters: dict) -> Optional[date]:
#     """Extract and parse date from Dialogflow parameters."""
#     raw_date = parameters.get("date") or parameters.get("date-time")
#     if not raw_date:
#         return None
#     try:
#         if isinstance(raw_date, str):
#             # Dialogflow sends ISO 8601: "2026-04-27T12:00:00+05:00"
#             dt = datetime.fromisoformat(raw_date)
#             return dt.date()
#     except (ValueError, TypeError):
#         pass
#     return None


# def extract_session_date(session_info: dict) -> date:
#     """
#     Extract date from Dialogflow session parameters.
#     Falls back to today's date (UTC).
#     """
#     try:
#         # Dialogflow sends time in queryResult.queryText context
#         # The session timezone can be in originalDetectIntentRequest
#         time_zone = session_info.get("timeZone", "UTC")
#         # We just use today as the session date
#     except Exception:
#         pass
#     return date.today()


# def extract_days_number(parameters: dict) -> Optional[int]:
#     """Extract number of days from parameters."""
#     number = parameters.get("number") or parameters.get("days")
#     if number is not None:
#         try:
#             return int(float(str(number)))
#         except (ValueError, TypeError):
#             pass
#     return None


# def build_fulfillment_response(text: str) -> dict:
#     """Build a Dialogflow-compatible fulfillment response."""
#     return {
#         "fulfillmentText": text,
#         "fulfillmentMessages": [
#             {
#                 "text": {
#                     "text": [text]
#                 }
#             }
#         ]
#     }


# async def handle_webhook(body: dict) -> dict:
#     """
#     Main webhook handler. Routes based on Dialogflow intent.
    
#     Supported intents:
#     - weather.current
#     - weather.forecast
#     - weather.forecast.specific-date
#     - weather.forecast.days
#     """
#     try:
#         query_result = body.get("queryResult", {})
#         intent_name = query_result.get("intent", {}).get("displayName", "")
#         parameters = query_result.get("parameters", {})

#         # Extract session date info from originalDetectIntentRequest
#         original_request = body.get("originalDetectIntentRequest", {})
#         session_info = original_request.get("payload", {})
#         session_date = extract_session_date(session_info)

#         logger.info(f"Intent: {intent_name}, Parameters: {parameters}")

#         # ─── Route to correct handler ──────────────────────────────────────

#         if intent_name == "weather.current":
#             return await handle_current_weather(parameters)

#         elif intent_name == "weather.forecast":
#             return await handle_forecast(parameters, session_date)

#         elif intent_name == "weather.forecast.specific-date":
#             return await handle_specific_date_weather(parameters)

#         elif intent_name == "weather.forecast.days":
#             return await handle_forecast_n_days(parameters)

#         else:
#             return build_fulfillment_response(
#                 "I'm not sure how to help with that. Try asking about current weather or a forecast!"
#             )

#     except Exception as e:
#         logger.error(f"Webhook error: {e}", exc_info=True)
#         return build_fulfillment_response(
#             "Sorry, I encountered an error fetching weather data. Please try again."
#         )


# # ─── Intent Handlers ──────────────────────────────────────────────────────────

# async def handle_current_weather(parameters: dict) -> dict:
#     """Handle weather.current intent."""
#     city = extract_city(parameters)
#     if not city:
#         return build_fulfillment_response("Please tell me which city you'd like the weather for.")

#     weather = await get_current_weather(city)

#     if not weather:
#         return build_fulfillment_response(format_city_not_found_error(city))

#     response_text = format_current_weather_response(weather)
#     return build_fulfillment_response(response_text)


# async def handle_forecast(parameters: dict, session_date: date) -> dict:
#     """
#     Handle weather.forecast intent.
#     - No date = full 8-day forecast
#     - Date provided = treat as specific date request
#     """
#     city = extract_city(parameters)
#     if not city:
#         return build_fulfillment_response("Please tell me which city you'd like the forecast for.")

#     # Check if a specific date was also provided
#     specific_date = extract_date(parameters)

#     if specific_date:
#         return await handle_specific_date_weather(parameters)

#     # Default: 8-day forecast
#     forecast = await get_forecast(city, days=8)
#     if not forecast:
#         return build_fulfillment_response(format_city_not_found_error(city))

#     response_text = format_forecast_response(forecast)
#     return build_fulfillment_response(response_text)


# async def handle_specific_date_weather(parameters: dict) -> dict:
#     """Handle weather.forecast.specific-date intent."""
#     city = extract_city(parameters)
#     target_date = extract_date(parameters)

#     if not city:
#         return build_fulfillment_response("Please tell me which city you'd like the weather for.")

#     if not target_date:
#         # No date given, fall back to current weather
#         weather = await get_current_weather(city)
#         if not weather:
#             return build_fulfillment_response(format_city_not_found_error(city))
#         response_text = format_current_weather_response(weather)
#         return build_fulfillment_response(response_text)

#     today = date.today()

#     # ── Past date check ──
#     if target_date < today:
#         return build_fulfillment_response(format_past_date_error(city, target_date))

#     # ── Fetch weather for the specific date ──
#     weather = await get_weather_for_specific_date(city, target_date)

#     if not weather:
#         return build_fulfillment_response(format_city_not_found_error(city))

#     if isinstance(weather, dict) and weather.get("error") == "past_date":
#         return build_fulfillment_response(format_past_date_error(city, target_date))

#     if isinstance(weather, dict) and weather.get("error") == "date_out_of_range":
#         return build_fulfillment_response(format_date_out_of_range_error(city))

#     response_text = format_specific_date_response(weather)
#     return build_fulfillment_response(response_text)


# async def handle_forecast_n_days(parameters: dict) -> dict:
#     """Handle weather.forecast.days intent — e.g., 'Forecast for Karachi for next 3 days'."""
#     city = extract_city(parameters)
#     days = extract_days_number(parameters)

#     if not city:
#         return build_fulfillment_response("Please tell me which city you'd like the forecast for.")

#     if not days or days < 1:
#         days = 8  # default

#     if days > 8:
#         days = 8  # cap at 8

#     forecast = await get_forecast(city, days=days)

#     if not forecast:
#         return build_fulfillment_response(format_city_not_found_error(city))

#     response_text = format_forecast_response(forecast, days=days)
#     return build_fulfillment_response(response_text)




from datetime import datetime, date, timezone
from typing import Optional
import logging

from weather_service import (
    get_current_weather,
    get_forecast,
    get_weather_for_specific_date,
)
from response_formatter import (
    format_current_weather_response,
    format_forecast_response,
    format_specific_date_response,
    format_past_date_error,
    format_city_not_found_error,
    format_date_out_of_range_error,
)

logger = logging.getLogger(__name__)


def extract_city(parameters: dict) -> Optional[str]:
    """Extract city from Dialogflow parameters. Handles geo-city object or string."""
    city = parameters.get("city") or parameters.get("geo-city")
    if isinstance(city, dict):
        # Dialogflow sometimes returns {"city": "Toronto", "country": "Canada"}
        return city.get("city") or city.get("name")
    return city if city else None


def extract_date(parameters: dict) -> Optional[date]:
    """Extract and parse date from Dialogflow parameters."""
    
    # ✅ Try direct date first
    raw_date = parameters.get("date") or parameters.get("date-time")
    
    if raw_date:
        try:
            if isinstance(raw_date, str) and raw_date.strip():
                dt = datetime.fromisoformat(raw_date)
                return dt.date()
        except (ValueError, TypeError):
            pass

    # ✅ NEW: handle date-period (use startDate)
    date_period = parameters.get("date-period")
    if isinstance(date_period, dict):
        start_date = date_period.get("startDate")
        if start_date:
            try:
                dt = datetime.fromisoformat(start_date)
                return dt.date()
            except (ValueError, TypeError):
                pass

    return None


def extract_session_date(session_info: dict) -> date:
    """
    Extract date from Dialogflow session parameters.
    Falls back to today's date (UTC).
    """
    try:
        # Dialogflow sends time in queryResult.queryText context
        # The session timezone can be in originalDetectIntentRequest
        time_zone = session_info.get("timeZone", "UTC")
        # We just use today as the session date
    except Exception:
        pass
    return date.today()


def extract_days_number(parameters: dict) -> Optional[int]:
    """Extract number of days from parameters."""
    number = parameters.get("number") or parameters.get("days")
    if number is not None:
        try:
            return int(float(str(number)))
        except (ValueError, TypeError):
            pass
    return None


def build_fulfillment_response(text: str) -> dict:
    """Build a Dialogflow-compatible fulfillment response."""
    return {
        "fulfillmentText": text,
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [text]
                }
            }
        ]
    }


async def handle_webhook(body: dict) -> dict:
    """
    Main webhook handler. Routes based on Dialogflow intent.
    
    Supported intents:
    - weather.current
    - weather.forecast
    - weather.forecast.specific-date
    - weather.forecast.days
    """
    try:
        query_result = body.get("queryResult", {})
        intent_name = query_result.get("intent", {}).get("displayName", "")
        parameters = query_result.get("parameters", {})
        logger.info(f"PARAMETERS FULL: {parameters}")

        # Extract session date info from originalDetectIntentRequest
        original_request = body.get("originalDetectIntentRequest", {})
        session_info = original_request.get("payload", {})
        session_date = extract_session_date(session_info)

        logger.info(f"Intent: {intent_name}, Parameters: {parameters}")

        # ─── Route to correct handler ──────────────────────────────────────

        if intent_name == "weather.current":
            return await handle_current_weather(parameters)

        elif intent_name == "weather.forecast":
            return await handle_forecast(parameters, session_date)

        elif intent_name == "weather.forecast.specific-date":
            return await handle_specific_date_weather(parameters)

        elif intent_name == "weather.forecast.days":
            return await handle_forecast_n_days(parameters)

        else:
            return build_fulfillment_response(
                "I'm not sure how to help with that. Try asking about current weather or a forecast!"
            )

    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return build_fulfillment_response(
            "Sorry, I encountered an error fetching weather data. Please try again."
        )


# ─── Intent Handlers ──────────────────────────────────────────────────────────

async def handle_current_weather(parameters: dict) -> dict:
    """Handle weather.current intent."""
    city = extract_city(parameters)
    if not city:
        return build_fulfillment_response("Please tell me which city you'd like the weather for.")

    weather = await get_current_weather(city)

    if not weather:
        return build_fulfillment_response(format_city_not_found_error(city))

    response_text = format_current_weather_response(weather)
    return build_fulfillment_response(response_text)


async def handle_forecast(parameters: dict, session_date: date) -> dict:
    """
    Handle weather.forecast intent.
    - No date = full 8-day forecast
    - Date provided = filter forecast from that date onward
    """
    city = extract_city(parameters)
    if not city:
        return build_fulfillment_response("Please tell me which city you'd like the forecast for.")

    # Check if a specific date was also provided
    specific_date = extract_date(parameters)

    forecast = await get_forecast(city, days=8)
    if not forecast:
        return build_fulfillment_response(format_city_not_found_error(city))

    # ✅ If user gave a start date → filter forecast
    if specific_date:
        filtered = [day for day in forecast if day["date"] >= specific_date]

        if not filtered:
            return build_fulfillment_response(format_date_out_of_range_error(city))

        response_text = format_forecast_response(filtered)
        return build_fulfillment_response(response_text)

    # default behavior
    response_text = format_forecast_response(forecast)
    return build_fulfillment_response(response_text)


async def handle_specific_date_weather(parameters: dict) -> dict:
    """Handle weather.forecast.specific-date intent."""
    city = extract_city(parameters)
    target_date = extract_date(parameters)

    if not city:
        return build_fulfillment_response("Please tell me which city you'd like the weather for.")

    if not target_date:
        # No date given, fall back to current weather
        weather = await get_current_weather(city)
        if not weather:
            return build_fulfillment_response(format_city_not_found_error(city))
        response_text = format_current_weather_response(weather)
        return build_fulfillment_response(response_text)

    today = date.today()

    # ── Past date check ──
    if target_date < today:
        return build_fulfillment_response(format_past_date_error(city, target_date))

    # ── Fetch weather for the specific date ──
    weather = await get_weather_for_specific_date(city, target_date)

    if not weather:
        return build_fulfillment_response(format_city_not_found_error(city))

    if isinstance(weather, dict) and weather.get("error") == "past_date":
        return build_fulfillment_response(format_past_date_error(city, target_date))

    if isinstance(weather, dict) and weather.get("error") == "date_out_of_range":
        return build_fulfillment_response(format_date_out_of_range_error(city))

    response_text = format_specific_date_response(weather)
    return build_fulfillment_response(response_text)


async def handle_forecast_n_days(parameters: dict) -> dict:
    """Handle weather.forecast.days intent — e.g., 'Forecast for Karachi for next 3 days'."""
    city = extract_city(parameters)
    days = extract_days_number(parameters)

    if not city:
        return build_fulfillment_response("Please tell me which city you'd like the forecast for.")

    if not days or days < 1:
        days = 8  # default

    if days > 8:
        days = 8  # cap at 8

    forecast = await get_forecast(city, days=days)

    if not forecast:
        return build_fulfillment_response(format_city_not_found_error(city))

    response_text = format_forecast_response(forecast, days=days)
    return build_fulfillment_response(response_text)