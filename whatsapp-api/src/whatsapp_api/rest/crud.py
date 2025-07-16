import os
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from ..database import get_db
from ..models import GuestCreate, GuestUpdate, GuestResponse
from ..guests import get_all_guests, create_guest, update_guest

# Load environment variables
load_dotenv(dotenv_path='/Users/madhavsharma/dotenv/aamantran.env')

AIRTABLE_API_TOKEN = os.getenv("AIRTABLE_API_TOKEN")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("TABLE_NAME")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["crud"])


@router.get("/guests", response_model=List[GuestResponse])
async def get_guests_endpoint():
    """Get all guests"""
    try:
        guests = get_all_guests()
        return guests
    except Exception as e:
        logger.error(f"Error fetching guests: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch guests")


@router.get("/guests/{guest_id}")
async def get_guest(guest_id: int):
    """
    Get a specific guest by ID
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM guests WHERE id = ?", (guest_id,))
            guest = cursor.fetchone()
            if not guest:
                raise HTTPException(status_code=404, detail="Guest not found")
            return {"guest": guest}
    except Exception as e:
        logger.error(f"Error fetching guest: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch guest")


@router.post("/guests", response_model=GuestResponse, status_code=201)
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


@router.patch("/guests/{guest_id}", response_model=GuestResponse)
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


@router.delete("/guests/{guest_id}")
async def delete_guest(guest_id: int):
    """
    Delete a guest
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM guests WHERE id = ?", (guest_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Guest not found")
            conn.commit()
            return {"message": "Guest deleted", "guest_id": guest_id}
    except Exception as e:
        logger.error(f"Error deleting guest: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete guest")


@router.get("/ready-guests")
async def get_ready_guests():
    """
    Get all guests marked as ready for invitation
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, prefix, first_name, last_name, greeting_name, phone 
                FROM guests 
                WHERE ready = 1 AND sent_to_whatsapp = 'pending' AND phone IS NOT NULL
            """)
            ready_guests = cursor.fetchall()
            return {"ready_guests": ready_guests, "count": len(ready_guests)}
    except Exception as e:
        logger.error(f"Error fetching ready guests: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ready guests")