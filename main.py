from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
import uvicorn

from webhook_handler import handle_webhook

# ─── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Weather Bot Webhook",
    description="FastAPI backend for Dialogflow ES Weather Bot using OpenWeatherMap API",
    version="1.0.0",
)


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Weather Bot Webhook is running 🌤️"}


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}


@app.post("/webhook")
async def webhook(request: Request):
    """
    Main Dialogflow ES webhook endpoint.
    Receives WebhookRequest and returns WebhookResponse.
    """
    try:
        body = await request.json()
        logger.info(f"Received webhook request: {body.get('queryResult', {}).get('queryText', '')}")

        response = await handle_webhook(body)

        logger.info(f"Sending response: {str(response)[:200]}")
        return JSONResponse(content=response)

    except Exception as e:
        logger.error(f"Webhook endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
