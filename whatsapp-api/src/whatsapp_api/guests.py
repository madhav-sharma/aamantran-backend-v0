from typing import List, Optional, Dict
from datetime import datetime
import json
from .database import get_db
from .models import GuestCreate, GuestUpdate, GuestResponse


# Country code to CSS class mapping
COUNTRY_CODE_COLORS = {
    '1': 'cc-usacan',    # USA/Canada
    '971': 'cc-uae',     # UAE
    '44': 'cc-uk',       # UK
    '91': 'cc-in',       # India
}


def get_phone_class(phone: Optional[str]) -> str:
    """Get CSS class based on phone country code"""
    if not phone or not phone.startswith('+'):
        return 'cc-other'
    
    # Extract country code (1-3 digits after +)
    for length in [3, 2, 1]:
        if len(phone) > length:
            prefix = phone[1:length+1]
            if prefix in COUNTRY_CODE_COLORS:
                return COUNTRY_CODE_COLORS[prefix]
    
    return 'cc-other'


def validate_group_rules(group_id: str, is_primary: bool, conn) -> Optional[str]:
    """Validate group rules for adding a guest"""
    cursor = conn.cursor()
    
    # Check if group exists
    cursor.execute("SELECT COUNT(*), SUM(is_group_primary) FROM guests WHERE group_id = ?", (group_id,))
    count, primary_count = cursor.fetchone()
    
    if count == 0:
        # New group must start with primary
        if not is_primary:
            return "First member of a group must be the primary contact"
    else:
        # Existing group
        if is_primary:
            if primary_count > 0:
                return "Group already has a primary contact"
        # Non-primary is always allowed for existing groups
    
    return None


def validate_phone_uniqueness(phone: str, conn, exclude_id: Optional[int] = None) -> bool:
    """Check if phone number is unique"""
    if not phone:
        return True
    
    cursor = conn.cursor()
    if exclude_id:
        cursor.execute("SELECT COUNT(*) FROM guests WHERE phone = ? AND id != ?", (phone, exclude_id))
    else:
        cursor.execute("SELECT COUNT(*) FROM guests WHERE phone = ?", (phone,))
    count = cursor.fetchone()[0]
    return count == 0


def get_all_guests() -> List[Dict]:
    """Get all guests from database"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM guests 
            ORDER BY group_id, is_group_primary DESC
        """)
        
        guests = []
        for row in cursor.fetchall():
            guest = dict(row)
            guest['phone_class'] = get_phone_class(guest['phone'])
            guests.append(guest)
        
        return guests


def create_guest(guest_data: GuestCreate) -> Dict:
    """Create a new guest"""
    with get_db() as conn:
        # Validate group rules
        error = validate_group_rules(guest_data.group_id, guest_data.is_group_primary, conn)
        if error:
            raise ValueError(error)
        
        # Validate phone uniqueness
        if guest_data.phone and not validate_phone_uniqueness(guest_data.phone, conn):
            raise ValueError("Phone number already exists for another guest")
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO guests (prefix, first_name, last_name, greeting_name, phone, 
                              group_id, is_group_primary, ready)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            guest_data.prefix,
            guest_data.first_name,
            guest_data.last_name,
            guest_data.greeting_name,
            guest_data.phone,
            guest_data.group_id,
            guest_data.is_group_primary,
            guest_data.ready
        ))
        
        conn.commit()
        guest_id = cursor.lastrowid
        
        # Fetch the created guest
        cursor.execute("SELECT * FROM guests WHERE id = ?", (guest_id,))
        guest = dict(cursor.fetchone())
        guest['phone_class'] = get_phone_class(guest['phone'])
        
        return guest


def update_guest(guest_id: int, update_data: GuestUpdate) -> Optional[Dict]:
    """Update a guest"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if guest exists
        cursor.execute("SELECT * FROM guests WHERE id = ?", (guest_id,))
        existing = cursor.fetchone()
        if not existing:
            return None
        
        # Only ready field can be updated (as per design document)
        if update_data.ready is not None:
            cursor.execute("""
                UPDATE guests 
                SET ready = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (update_data.ready, guest_id))
            conn.commit()
        
        # Return updated guest
        cursor.execute("SELECT * FROM guests WHERE id = ?", (guest_id,))
        guest = dict(cursor.fetchone())
        guest['phone_class'] = get_phone_class(guest['phone'])
        
        return guest


def log_api_interaction(guest_id: Optional[int], log_type: str, payload: dict, 
                       status: Optional[str] = None, is_multiple: bool = False):
    """Log WhatsApp API interactions"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO logs (guest_id, type, payload, status, is_multiple)
            VALUES (?, ?, ?, ?, ?)
        """, (
            guest_id,
            log_type,
            json.dumps(payload),
            status,
            is_multiple
        ))
        conn.commit() 