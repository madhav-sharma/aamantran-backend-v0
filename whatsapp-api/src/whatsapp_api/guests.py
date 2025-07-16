from typing import List, Optional, Dict
from .db_operations import GuestOperations
from .models import GuestCreate, GuestUpdate, GuestResponse


def get_all_guests() -> List[Dict]:
    """Get all guests from database"""
    return GuestOperations.get_all_guests()


def create_guest(guest_data: GuestCreate) -> Dict:
    """Create a new guest"""
    return GuestOperations.create_guest(guest_data)


def update_guest(guest_id: int, update_data: GuestUpdate) -> Optional[Dict]:
    """Update a guest"""
    return GuestOperations.update_guest(guest_id, update_data)


 