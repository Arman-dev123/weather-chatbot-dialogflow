# 🌤️ Weather Bot — FastAPI Webhook

FastAPI backend for the Dialogflow ES Weather Bot using OpenWeatherMap API.

---

## 📁 Project Structure

```
weather_bot/
├── .env                    # Your API keys (never commit this)
├── requirements.txt        # Python dependencies
├── main.py                 # FastAPI app & routes
├── webhook_handler.py      # Intent routing logic
├── weather_service.py      # OpenWeatherMap API calls
└── response_formatter.py   # Styled text formatting
```

---

## ⚙️ Setup Instructions

### 1. Prerequisites
- Python 3.10+
- pip
- ngrok (for local dev tunnel)

---

### 2. Clone / Create the project folder

```bash
mkdir weather_bot
cd weather_bot
# (copy all files here)
```

---

### 3. Create a virtual environment

```bash
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate
```

---

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 5. Configure your API key

Edit `.env`:
```
OPENWEATHER_API_KEY=your_actual_key_here
```

Get your free key at: https://openweathermap.org/api
- Register → My API Keys → Copy the default key


---

### 6. Run the FastAPI server

```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --port 8000
```

Server runs at: http://localhost:8000

---

### 7. Expose with ngrok

In a new terminal:
```bash
ngrok http 8000
```

Copy the HTTPS URL, e.g.: `https://abc123.ngrok.io`

---

### 8. Set Webhook in Dialogflow

1. Go to Dialogflow ES → **Fulfillment**
2. Enable **Webhook**
3. Set URL to: `https://abc123.ngrok.io/webhook`
4. Save

---

## 🤖 Intents Summary

| Intent | Example Input | Behavior |
|---|---|---|
| `weather.current` | "What's the weather in Karachi?" | Shows current weather |
| `weather.forecast` | "Forecast for London" | Shows 8-day forecast |
| `weather.forecast.specific-date` | "Weather in Toronto on April 27" | Shows that specific day only |
| `weather.forecast.days` | "Forecast for Karachi for next 3 days" | Shows N-day forecast |

---

## 📌 API Endpoints

| Method | Route | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/health` | Health check |
| POST | `/webhook` | Dialogflow webhook |

---

## 🔍 Test Locally

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "queryResult": {
      "intent": {"displayName": "weather.current"},
      "parameters": {"city": "Karachi"}
    }
  }'
```

---

## ⚠️ Notes

- Past dates return an error message (cannot show historical weather on free tier)
- Forecast is capped at 5 days
- Free tier of OpenWeatherMap gives 5-day/3-hour forecast; for full 8-day you need One Call 3.0
