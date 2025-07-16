"""Webhook endpoints for WhatsApp Business API.

These are isolated in their own router so they can be mounted easily from
``main.py`` without cluttering the root module.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import APIRouter, Request, Response

# ---------------------------------------------------------------------------
# Environment & constants
# ---------------------------------------------------------------------------

WHATSAPP_API_BASE_URL = "https://graph.facebook.com"
WHATSAPP_API_VERSION = "v23.0"

# Load env variables; keep fall-back path identical to the existing project
load_dotenv(dotenv_path=os.getenv("DOTENV_PATH") or "/Users/madhavsharma/dotenv/aamantran.env")

WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN")

# ---------------------------------------------------------------------------
# Router definition
# ---------------------------------------------------------------------------

router = APIRouter()


@router.get("/webhook")
async def verify_webhook(request: Request) -> Response:  # noqa: D401
    """Verify WhatsApp webhook subscription."""

    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")

    return Response(content="Forbidden", status_code=403)


@router.post("/webhook")
async def handle_webhook(request: Request) -> Response:  # noqa: D401
    """Handle incoming webhook callbacks from WhatsApp."""

    data = await request.json()
    # For now we simply log / echo – adjust as needed.
    print("WhatsApp Webhook Payload:", data)
    return Response(content="OK", status_code=200)
