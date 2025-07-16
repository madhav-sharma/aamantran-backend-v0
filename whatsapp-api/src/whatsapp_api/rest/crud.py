import os
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from ..db_operations import get_db_session
from ..models import GuestCreate, GuestUpdate, GuestResponse
from ..guests import get_all_guests, create_guest, update_guest
from ..db_models import Guest

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
        with get_db_session() as session:
            guest = session.query(Guest).filter(Guest.id == guest_id).first()
            if not guest:
                raise HTTPException(status_code=404, detail="Guest not found")
            
            guest_dict = {
                'id': guest.id,
                'prefix': guest.prefix,
                'first_name': guest.first_name,
                'last_name': guest.last_name,
                'greeting_name': guest.greeting_name,
                'phone': guest.phone,
                'group_id': guest.group_id,
                'is_group_primary': guest.is_group_primary,
                'ready': guest.ready,
                'sent_to_whatsapp': guest.sent_to_whatsapp,
                'api_call_at': guest.api_call_at,
                'sent_at': guest.sent_at,
                'delivered_at': guest.delivered_at,
                'read_at': guest.read_at,
                'responded_with_button': guest.responded_with_button,
                'message_id': guest.message_id,
                'created_at': guest.created_at,
                'updated_at': guest.updated_at
            }
            return {"guest": guest_dict}
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


@router.get("/ready-guests")
async def get_ready_guests():
    """
    Get all guests marked as ready for invitation
    """
    try:
        with get_db_session() as session:
            guests = session.query(Guest).filter(
                Guest.ready == True,
                Guest.sent_to_whatsapp == 'pending',
                Guest.phone.isnot(None)
            ).all()
            
            ready_guests = []
            for guest in guests:
                guest_dict = {
                    'id': guest.id,
                    'prefix': guest.prefix,
                    'first_name': guest.first_name,
                    'last_name': guest.last_name,
                    'greeting_name': guest.greeting_name,
                    'phone': guest.phone
                }
                ready_guests.append(guest_dict)
                
            return {"ready_guests": ready_guests, "count": len(ready_guests)}
    except Exception as e:
        logger.error(f"Error fetching ready guests: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ready guests")