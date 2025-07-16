import os
from typing import Optional, Dict, Any, List
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging

from .database import init_database, get_db
from .models import GuestCreate, GuestUpdate, GuestResponse
from .guests import get_all_guests, create_guest, update_guest, log_api_interaction
from .rest.whatsapp import send_template_message, process_webhook_data

# Initialize environment variables
load_dotenv()

# Retrieve environment variables
WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Wedding RSVP Management")

# Set up Jinja templates (points to "templates" folder)
templates = Jinja2Templates(directory="src/templates")

# Mount static files (CSS, JS, images, etc.)
app.mount("/static", StaticFiles(directory="src/static"), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()
    logger.info("Application started")


# Simple route for the homepage
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        return int(challenge)
    return Response(content="", status_code=403)


@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    """WhatsApp webhook endpoint"""
    webhook_data = await request.json()
    
    # Log the webhook
    log_api_interaction(
        guest_id=None,
        log_type="webhook",
        payload=webhook_data,
        status="received"
    )
    
    # Process webhook in background
    background_tasks.add_task(process_webhook_updates, webhook_data)
    
    return {"status": "ok"}


async def process_webhook_updates(webhook_data: Dict[str, Any]):
    """Process webhook updates in background"""
    try:
        statuses = process_webhook_data(webhook_data)
        
        if not statuses:
            return
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            for message_id, status_type, timestamp in statuses:
                # Find guest by message_id
                cursor.execute("SELECT id FROM guests WHERE message_id = ?", (message_id,))
                result = cursor.fetchone()
                
                if result:
                    guest_id = result[0]
                    
                    # Update based on status type
                    if status_type == "sent":
                        cursor.execute(
                            "UPDATE guests SET sent_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (guest_id,)
                        )
                    elif status_type == "delivered":
                        cursor.execute(
                            "UPDATE guests SET delivered_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (guest_id,)
                        )
                    elif status_type == "read":
                        cursor.execute(
                            "UPDATE guests SET read_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (guest_id,)
                        )
                    
                    conn.commit()
                    logger.info(f"Updated guest {guest_id} with status {status_type}")
                else:
                    logger.warning(f"No guest found for message_id {message_id}")
                    
    except Exception as e:
        logger.error(f"Error processing webhook updates: {e}")


@app.get("/guests", response_model=List[GuestResponse])
async def get_guests():
    """Get all guests"""
    try:
        guests = get_all_guests()
        return guests
    except Exception as e:
        logger.error(f"Error fetching guests: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch guests")


@app.post("/guests", response_model=GuestResponse, status_code=201)
async def create_guest_endpoint(guest: GuestCreate):
    """Create a new guest"""
    try:
        new_guest = create_guest(guest)
        return new_guest
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating guest: {e}")
        raise HTTPException(status_code=500, detail="Failed to create guest")


@app.patch("/guests/{guest_id}", response_model=GuestResponse)
async def update_guest_endpoint(guest_id: int, update_data: GuestUpdate):
    """Update a guest"""
    try:
        updated_guest = update_guest(guest_id, update_data)
        if not updated_guest:
            raise HTTPException(status_code=404, detail="Guest not found")
        return updated_guest
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating guest: {e}")
        raise HTTPException(status_code=500, detail="Failed to update guest")


@app.post("/send-invites")
async def send_invites():
    """Send invites to ready guests"""
    sent_count = 0
    failed_count = 0
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get all ready guests who haven't been sent invites
            cursor.execute("""
                SELECT id, prefix, first_name, last_name, greeting_name, phone 
                FROM guests 
                WHERE ready = 1 AND sent_to_whatsapp = 'pending' AND phone IS NOT NULL
            """)
            
            guests_to_send = cursor.fetchall()
            
            for guest in guests_to_send:
                guest_id, prefix, first_name, last_name, greeting_name, phone = guest
                
                # Use greeting name if available, otherwise construct from prefix + first name
                if greeting_name:
                    name = greeting_name
                else:
                    # Combine prefix and first name if prefix exists
                    name_parts = [prefix, first_name] if prefix else [first_name]
                    name = " ".join(name_parts)
                
                try:
                    # Update api_call_at before making the call
                    cursor.execute("""
                        UPDATE guests 
                        SET api_call_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (guest_id,))
                    conn.commit()
                    
                    # Send WhatsApp message
                    response = await send_template_message(phone, name, guest_id)
                    
                    # Extract message ID from response
                    message_id = response.get("messages", [{}])[0].get("id")
                    
                    if message_id:
                        # Update guest status
                        cursor.execute("""
                            UPDATE guests 
                            SET sent_to_whatsapp = 'succeeded', 
                                message_id = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (message_id, guest_id))
                        conn.commit()
                        sent_count += 1
                        logger.info(f"Successfully sent invite to guest {guest_id}")
                    else:
                        raise Exception("No message ID in response")
                        
                except Exception as e:
                    logger.error(f"Failed to send invite to guest {guest_id}: {e}")
                    # Update guest status to failed
                    cursor.execute("""
                        UPDATE guests 
                        SET sent_to_whatsapp = 'failed',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (guest_id,))
                    conn.commit()
                    failed_count += 1
        
        return {
            "message": f"Invites sent: {sent_count} succeeded, {failed_count} failed",
            "sent": sent_count,
            "failed": failed_count
        }
        
    except Exception as e:
        logger.error(f"Error in send_invites: {e}")
        raise HTTPException(status_code=500, detail="Failed to send invites")
