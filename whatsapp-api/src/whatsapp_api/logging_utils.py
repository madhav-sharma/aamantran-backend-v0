import json
import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime
import aiosqlite

logger = logging.getLogger(__name__)


async def log_whatsapp_api_call(
    db_path: str,
    guest_id: int,
    direction: str,
    method: str,
    url: str,
    headers: Dict[str, Any],
    payload: Optional[Dict[str, Any]],
    status_code: Optional[int] = None,
    response_time_ms: Optional[int] = None,
    error_message: Optional[str] = None
):
    """
    Log WhatsApp API calls to the database
    """
    try:
        from .db_operations import WhatsAppAPICallOperations
        
        # Remove sensitive data from headers before logging
        safe_headers = headers.copy()
        if 'Authorization' in safe_headers:
            safe_headers['Authorization'] = 'Bearer [REDACTED]'
        
        await WhatsAppAPICallOperations.create_api_call(
            guest_id=guest_id,
            direction=direction,
            method=method,
            url=url,
            headers=json.dumps(safe_headers, indent=2),
            payload=json.dumps(payload, indent=2) if payload else None,
            status_code=status_code,
            response_time_ms=response_time_ms,
            error_message=error_message
        )
            
        # Also log to Python logger for immediate visibility
        log_message = f"WhatsApp API {direction} - Method: {method}, URL: {url}"
        if status_code:
            log_message += f", Status: {status_code}"
        if response_time_ms:
            log_message += f", Response Time: {response_time_ms}ms"
        if error_message:
            log_message += f", Error: {error_message}"
            
        logger.info(log_message)
        if payload:
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
            
    except Exception as e:
        logger.error(f"Failed to log WhatsApp API call: {str(e)}", exc_info=True)


async def log_webhook_payload(
    db_path: str,
    event_type: str,
    payload: Dict[str, Any],
    headers: Dict[str, Any],
    guest_id: Optional[int] = None,
    is_multiple: bool = False
):
    """
    Log webhook payloads to the database
    """
    try:
        from .db_operations import WebhookPayloadOperations
        
        # Remove sensitive headers
        safe_headers = headers.copy()
        if 'X-Hub-Signature-256' in safe_headers:
            safe_headers['X-Hub-Signature-256'] = '[REDACTED]'
            
        await WebhookPayloadOperations.create_webhook_payload(
            event_type=event_type,
            payload=json.dumps(payload, indent=2),
            headers=json.dumps(safe_headers, indent=2),
            guest_id=guest_id,
            is_multiple=is_multiple
        )
            
        # Log to Python logger
        log_msg = f"Webhook received - Event Type: {event_type}"
        if guest_id:
            log_msg += f", Guest ID: {guest_id}"
        if is_multiple:
            log_msg += " (Multiple guests)"
        logger.info(log_msg)
        logger.debug(f"Webhook Payload: {json.dumps(payload, indent=2)}")
        
    except Exception as e:
        logger.error(f"Failed to log webhook payload: {str(e)}", exc_info=True)


def extract_webhook_event_type(payload: Dict[str, Any]) -> str:
    """
    Extract the event type from a WhatsApp webhook payload
    """
    try:
        # WhatsApp webhook structure: entry[0].changes[0].value.statuses[0].status
        if 'entry' in payload and payload['entry']:
            changes = payload['entry'][0].get('changes', [])
            if changes:
                value = changes[0].get('value', {})
                
                # Check for message status updates
                if 'statuses' in value and value['statuses']:
                    return value['statuses'][0].get('status', 'unknown_status')
                
                # Check for incoming messages
                if 'messages' in value and value['messages']:
                    return 'incoming_message'
                    
                # Check for other event types
                if 'contacts' in value:
                    return 'contact_update'
                    
        return 'unknown'
    except Exception as e:
        logger.error(f"Failed to extract webhook event type: {str(e)}", exc_info=True)
        return 'error'


async def extract_guest_info_from_webhook(db_path: str, payload: Dict[str, Any]) -> tuple[Optional[int], bool]:
    """
    Extract guest_id from webhook payload by looking up message_id or phone number
    Returns (guest_id, is_multiple)
    """
    try:
        from .db_operations import GuestOperations
        
        guest_ids = set()
        
        # Extract message IDs and phone numbers from the webhook
        if 'entry' in payload and payload['entry']:
            for entry in payload['entry']:
                changes = entry.get('changes', [])
                for change in changes:
                    value = change.get('value', {})
                    
                    # Check for status updates (sent/delivered/read)
                    statuses = value.get('statuses', [])
                    for status in statuses:
                        message_id = status.get('id')
                        if message_id:
                            guest = await GuestOperations.get_guest_by_message_id(message_id)
                            if guest:
                                guest_ids.add(guest.id)
                    
                    # Check for incoming messages
                    messages = value.get('messages', [])
                    for message in messages:
                        # Get phone number from incoming message
                        from_number = message.get('from')
                        if from_number:
                            guest = await GuestOperations.get_guest_by_phone(from_number)
                            if guest:
                                guest_ids.add(guest.id)
        
        # Determine if multiple guests
        if len(guest_ids) == 0:
            return (None, False)
        elif len(guest_ids) == 1:
            return (list(guest_ids)[0], False)
        else:
            # Multiple guests - return None for guest_id
            return (None, True)
            
    except Exception as e:
        logger.error(f"Failed to extract guest info from webhook: {str(e)}", exc_info=True)
        return (None, False)


class APICallTimer:
    """Context manager to time API calls"""
    
    def __init__(self):
        self.start_time = None
        self.response_time_ms = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            self.response_time_ms = int((time.time() - self.start_time) * 1000)