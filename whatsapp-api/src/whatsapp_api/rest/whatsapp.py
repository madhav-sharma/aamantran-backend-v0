import os
from typing import Optional, Dict, Any
import httpx
import logging
from ..guests import log_api_interaction

logger = logging.getLogger(__name__)

# WhatsApp API configuration
WHATSAPP_API_BASE_URL = "https://graph.facebook.com"
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v18.0")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_TEMPLATE_NAME = os.getenv("WHATSAPP_TEMPLATE_NAME")
WHATSAPP_LANGUAGE_CODE = os.getenv("WHATSAPP_LANGUAGE_CODE", "en")


def create_template_message(
    phone_number: str,
    name: str,
    template_name: str = None,
    language_code: str = None,
) -> Dict[str, Any]:
    """
    Create a template message payload.
    """
    template_name = template_name or WHATSAPP_TEMPLATE_NAME
    language_code = language_code or WHATSAPP_LANGUAGE_CODE

    return {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
            "components": [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": name}],
                }
            ],
        },
    }


async def send_whatsapp_message(
    message_data: Dict[str, Any], guest_id: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Send a message via WhatsApp API.
    """
    url = f"{WHATSAPP_API_BASE_URL}/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    # Log the request
    log_api_interaction(
        guest_id=guest_id,
        log_type="request",
        payload=message_data,
        status="pending"
    )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=message_data)
            response_data = response.json()
            
            # Log the response
            log_api_interaction(
                guest_id=guest_id,
                log_type="response",
                payload=response_data,
                status=str(response.status_code)
            )
            
            response.raise_for_status()
            return response_data
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        # Log the error
        log_api_interaction(
            guest_id=guest_id,
            log_type="response",
            payload={"error": str(e)},
            status="error"
        )
        raise


async def send_template_message(
    phone_number: str, name: str, guest_id: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Send a template message to a phone number.
    """
    message_data = create_template_message(phone_number, name)
    return await send_whatsapp_message(message_data, guest_id)


def process_webhook_data(webhook_data: Dict[str, Any]) -> list:
    """
    Process WhatsApp webhook data and extract message statuses.
    Returns a list of (message_id, status, timestamp) tuples.
    """
    statuses = []
    
    try:
        # Handle status updates
        if "entry" in webhook_data:
            for entry in webhook_data["entry"]:
                if "changes" in entry:
                    for change in entry["changes"]:
                        if change.get("field") == "messages" and "value" in change:
                            value = change["value"]
                            
                            # Handle message status updates
                            if "statuses" in value:
                                for status in value["statuses"]:
                                    message_id = status.get("id")
                                    status_type = status.get("status")
                                    timestamp = status.get("timestamp")
                                    
                                    if message_id and status_type:
                                        statuses.append((message_id, status_type, timestamp))
    except Exception as e:
        logger.error(f"Error processing webhook data: {e}")
    
    return statuses 