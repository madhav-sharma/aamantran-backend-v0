import os
from typing import Optional, Dict, Any
import aiohttp
import logging
from dotenv import load_dotenv
from fastapi import APIRouter, Request, Response, BackgroundTasks
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(dotenv_path='/Users/madhavsharma/dotenv/aamantran.env')

# WhatsApp API configuration
WHATSAPP_API_BASE_URL = "https://graph.facebook.com"
WHATSAPP_API_VERSION = "v23.0"
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN")

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


def create_template_message(
    recipient: str,
    template_name: str,
    language_code: str = "en_US",
    components: Optional[list] = None
) -> Dict[str, Any]:
    """
    Create a template message payload

    Args:
        recipient: Phone number in international format
        template_name: Name of the WhatsApp template
        language_code: Language code for the template (default: "en_US")
        components: Optional template components (parameters, buttons, etc.)

    Returns:
        Message payload dictionary
    """
    message = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": language_code
            }
        }
    }

    if components:
        message["template"]["components"] = components

    return message


async def send_whatsapp_message(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a message via WhatsApp Business API

    Args:
        data: The message payload as a dictionary

    Returns:
        Response from the WhatsApp API
    """
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
                    print(f"Message sent successfully: {response_data}")
                    return {"status": "success", "data": response_data}
                else:
                    print(f"Error sending message. Status: {response.status}")
                    print(f"Response: {response_data}")
                    return {"status": "error", "code": response.status, "data": response_data}

        except aiohttp.ClientConnectorError as e:
            print(f"Connection Error: {str(e)}")
            return {"status": "error", "message": f"Connection error: {str(e)}"}
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}


@router.get("/webhook")
async def verify_webhook(request: Request):
    """
    Webhook verification endpoint for WhatsApp
    """
    print(request)
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        print("Webhook verified successfully!")
        return Response(content=challenge, media_type="text/plain")
    else:
        print("Webhook verification failed!")
        return Response(content="Forbidden", status_code=403)


@router.post("/webhook")
async def handle_webhook(request: Request):
    """
    Handle WhatsApp webhook events
    """
    print(request)
    data = await request.json()
    print(data)
    return Response(content="OK", status_code=200)


@router.post("/test_whatsapp_api")
async def send_template_message_endpoint() -> Dict[str, Any]:
    """
    Send a template message to a WhatsApp number
    """
    recipient = "14373668209"
    template_name = "hello_world"
    language_code = "en_US"
    components = None

    message_data = create_template_message(recipient, template_name, language_code, components)
    return await send_whatsapp_message(message_data)


async def send_invite_to_guest(phone_number: str, guest_name: str):
    """
    Background task to send WhatsApp invite to a single guest
    """
    phone_number = phone_number[1:] # remove plus sign
    try:
        message_data = create_template_message(
            recipient=phone_number,
            template_name="wedding_pre_invite",
            language_code="en",
            components=[
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": guest_name}]
                }
            ] if guest_name else None
        )
        result = await send_whatsapp_message(message_data)
        logger.info(f"Sent invite to {phone_number}: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to send invite to {phone_number}: {str(e)}")
        raise


@router.post("/send-invites-to-ready-guests")
async def send_invites_to_ready_guests(background_tasks: BackgroundTasks):
    """
    Send WhatsApp invites to all guests marked as ready
    This endpoint triggers background tasks to send messages
    """
    try:
        from ..database import get_db
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get all ready guests who haven't been sent invites
            cursor.execute("""
                SELECT id, prefix, first_name, last_name, greeting_name, phone 
                FROM guests 
                WHERE ready = 1 AND sent_to_whatsapp = 'pending' AND phone IS NOT NULL
            """)
            
            guests_to_send = cursor.fetchall()
            
            if not guests_to_send:
                return {"message": "No ready guests to send invites to", "count": 0}
            
            # Queue background tasks for each guest
            for guest in guests_to_send:
                guest_id, prefix, first_name, last_name, greeting_name, phone = guest
                
                # Use greeting name if available, otherwise construct from prefix + first name
                if greeting_name:
                    name = greeting_name
                else:
                    # Combine prefix and first name if prefix exists
                    name_parts = [prefix, first_name] if prefix else [first_name]
                    name = " ".join(name_parts)
                
                # Add background task to send invite
                background_tasks.add_task(
                    send_invite_with_db_update,
                    guest_id=guest_id,
                    phone_number=phone,
                    guest_name=name
                )
            
            return {
                "message": "Invite sending initiated",
                "status": "processing",
                "queued_count": len(guests_to_send)
            }
            
    except Exception as e:
        logger.error(f"Error queuing invites: {e}")
        return {"status": "error", "message": str(e)}


async def send_invite_with_db_update(guest_id: int, phone_number: str, guest_name: str):
    """
    Send invite and update database status
    """
    from ..database import get_db
    from ..guests import log_api_interaction
    
    try:
        # Update api_call_at before making the call
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE guests 
                SET api_call_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (guest_id,))
            conn.commit()
        
        # Log the API interaction
        log_api_interaction(
            guest_id=guest_id,
            log_type="request",
            payload={"phone": phone_number, "name": guest_name},
            status="pending"
        )
        
        # Send the invite
        result = await send_invite_to_guest(phone_number, guest_name)
        
        # Extract message ID from response if available
        message_id = None
        if result.get("status") == "success":
            message_id = result.get("data", {}).get("messages", [{}])[0].get("id")
        
        # Update guest status based on result
        with get_db() as conn:
            cursor = conn.cursor()
            if result.get("status") == "success" and message_id:
                cursor.execute("""
                    UPDATE guests 
                    SET sent_to_whatsapp = 'succeeded', 
                        message_id = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (message_id, guest_id))
                logger.info(f"Successfully sent invite to guest {guest_id}")
            else:
                cursor.execute("""
                    UPDATE guests 
                    SET sent_to_whatsapp = 'failed',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (guest_id,))
                logger.error(f"Failed to send invite to guest {guest_id}")
            conn.commit()
        
        # Log the response
        log_api_interaction(
            guest_id=guest_id,
            log_type="response",
            payload=result,
            status="success" if result.get("status") == "success" else "failed"
        )
        
    except Exception as e:
        logger.error(f"Error sending invite to guest {guest_id}: {str(e)}")
        # Update guest status to failed
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE guests 
                SET sent_to_whatsapp = 'failed',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (guest_id,))
            conn.commit()
        
        # Log the error
        log_api_interaction(
            guest_id=guest_id,
            log_type="response",
            payload={"error": str(e)},
            status="error"
        ) 