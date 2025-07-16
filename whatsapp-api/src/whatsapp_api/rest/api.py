import os
from typing import Optional, Dict, Any

import aiohttp
from dotenv import load_dotenv

# Constants for WhatsApp Business API
WHATSAPP_API_BASE_URL = "https://graph.facebook.com"
WHATSAPP_API_VERSION = "v23.0"

# Load environment variables (falls back to hard-coded path used in the existing project)
load_dotenv(dotenv_path=os.getenv("DOTENV_PATH") or "/Users/madhavsharma/dotenv/aamantran.env")

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")


def create_template_message(
    recipient: str,
    template_name: str,
    language_code: str = "en_US",
    components: Optional[list] = None,
) -> Dict[str, Any]:
    """Create a template message payload for the WhatsApp Business API."""

    message: Dict[str, Any] = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
        },
    }

    if components:
        message["template"]["components"] = components

    return message


async def send_whatsapp_message(data: Dict[str, Any]) -> Dict[str, Any]:
    """Send a message via the WhatsApp Business API."""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    }

    url = f"{WHATSAPP_API_BASE_URL}/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data, headers=headers) as response:
                response_data = await response.json()

                if response.status == 200:
                    return {"status": "success", "data": response_data}

                return {
                    "status": "error",
                    "code": response.status,
                    "data": response_data,
                }

        except aiohttp.ClientConnectorError as exc:
            return {
                "status": "error",
                "message": f"Connection error: {exc}",
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "error",
                "message": f"Unexpected error: {exc}",
            }
