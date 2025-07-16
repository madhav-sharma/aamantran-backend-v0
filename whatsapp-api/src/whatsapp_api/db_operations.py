from sqlalchemy import create_engine, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager, contextmanager

from .db_models import Base, Guest, WhatsAppAPICall, WebhookPayload
from .models import GuestCreate, GuestUpdate, GuestResponse

# Database configuration
DB_PATH = Path("wedding.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"
ASYNC_DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# Create engines
engine = create_engine(DATABASE_URL, echo=False)
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)

# Create session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


def init_database():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db_session():
    """Get synchronous database session"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@asynccontextmanager
async def get_async_db_session():
    """Get asynchronous database session"""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


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


class GuestOperations:
    """Database operations for guests"""
    
    @staticmethod
    def get_all_guests() -> List[Dict[str, Any]]:
        """Get all guests from database"""
        with get_db_session() as session:
            guests = session.query(Guest).order_by(Guest.group_id, Guest.is_group_primary.desc()).all()
            
            result = []
            for guest in guests:
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
                    'updated_at': guest.updated_at,
                    'phone_class': get_phone_class(guest.phone)
                }
                result.append(guest_dict)
            
            return result
    
    @staticmethod
    def validate_group_rules(group_id: str, is_primary: bool, session: Session) -> Optional[str]:
        """Validate group rules for adding a guest"""
        # Check if group exists
        existing_guests = session.query(Guest).filter(Guest.group_id == group_id).all()
        
        if not existing_guests:
            # New group must start with primary
            if not is_primary:
                return "First member of a group must be the primary contact"
        else:
            # Existing group
            if is_primary:
                primary_count = sum(1 for guest in existing_guests if guest.is_group_primary)
                if primary_count > 0:
                    return "Group already has a primary contact"
            # Non-primary is always allowed for existing groups
        
        return None
    
    @staticmethod
    def create_guest(guest_data: GuestCreate) -> Dict[str, Any]:
        """Create a new guest"""
        with get_db_session() as session:
            # Validate group rules
            error = GuestOperations.validate_group_rules(
                guest_data.group_id, 
                guest_data.is_group_primary, 
                session
            )
            if error:
                raise ValueError(error)
            
            # Create guest
            guest = Guest(
                prefix=guest_data.prefix,
                first_name=guest_data.first_name,
                last_name=guest_data.last_name,
                greeting_name=guest_data.greeting_name,
                phone=guest_data.phone,
                group_id=guest_data.group_id,
                is_group_primary=guest_data.is_group_primary,
                ready=guest_data.ready
            )
            
            try:
                session.add(guest)
                session.flush()  # Get the ID
                
                # Return guest data
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
                    'updated_at': guest.updated_at,
                    'phone_class': get_phone_class(guest.phone)
                }
                
                return guest_dict
                
            except IntegrityError as e:
                if "UNIQUE constraint failed: guests.phone" in str(e):
                    raise ValueError("Phone number already exists for another guest")
                raise
    
    @staticmethod
    def update_guest(guest_id: int, update_data: GuestUpdate) -> Optional[Dict[str, Any]]:
        """Update a guest"""
        with get_db_session() as session:
            guest = session.query(Guest).filter(Guest.id == guest_id).first()
            if not guest:
                return None
            
            # Only ready field can be updated (as per design document)
            if update_data.ready is not None:
                guest.ready = update_data.ready
            
            session.flush()
            
            # Return updated guest
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
                'updated_at': guest.updated_at,
                'phone_class': get_phone_class(guest.phone)
            }
            
            return guest_dict
    
    @staticmethod
    async def get_guest_by_phone(phone: str) -> Optional[Guest]:
        """Get guest by phone number (async)"""
        async with get_async_db_session() as session:
            result = await session.execute(
                select(Guest).where(Guest.phone == phone)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_guest_by_message_id(message_id: str) -> Optional[Guest]:
        """Get guest by message ID (async)"""
        async with get_async_db_session() as session:
            result = await session.execute(
                select(Guest).where(Guest.message_id == message_id)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    def get_ready_guests_for_whatsapp():
        """Get all ready guests who haven't been sent invites"""
        with get_db_session() as session:
            guests = session.query(Guest).filter(
                Guest.ready == True,
                Guest.sent_to_whatsapp == 'pending',
                Guest.phone.isnot(None)
            ).all()
            
            result = []
            for guest in guests:
                guest_dict = {
                    'id': guest.id,
                    'prefix': guest.prefix,
                    'first_name': guest.first_name,
                    'last_name': guest.last_name,
                    'greeting_name': guest.greeting_name,
                    'phone': guest.phone
                }
                result.append(guest_dict)
            
            return result
    
    @staticmethod
    def update_guest_api_call_time(guest_id: int):
        """Update api_call_at timestamp for a guest"""
        with get_db_session() as session:
            guest = session.query(Guest).filter(Guest.id == guest_id).first()
            if guest:
                guest.api_call_at = func.now()
                session.flush()
    
    @staticmethod
    def update_guest_whatsapp_status(guest_id: int, status: str, message_id: Optional[str] = None):
        """Update guest's WhatsApp send status"""
        with get_db_session() as session:
            guest = session.query(Guest).filter(Guest.id == guest_id).first()
            if guest:
                guest.sent_to_whatsapp = status
                if message_id:
                    guest.message_id = message_id
                session.flush()


class WhatsAppAPICallOperations:
    """Database operations for WhatsApp API calls"""
    
    @staticmethod
    async def create_api_call(
        guest_id: int,
        direction: str,
        method: str,
        url: str,
        headers: str,
        payload: Optional[str] = None,
        status_code: Optional[int] = None,
        response_time_ms: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> WhatsAppAPICall:
        """Create a new API call record"""
        async with get_async_db_session() as session:
            api_call = WhatsAppAPICall(
                guest_id=guest_id,
                direction=direction,
                method=method,
                url=url,
                headers=headers,
                payload=payload,
                status_code=status_code,
                response_time_ms=response_time_ms,
                error_message=error_message
            )
            
            session.add(api_call)
            await session.flush()
            return api_call


class WebhookPayloadOperations:
    """Database operations for webhook payloads"""
    
    @staticmethod
    async def create_webhook_payload(
        event_type: str,
        payload: str,
        headers: str,
        guest_id: Optional[int] = None,
        is_multiple: bool = False
    ) -> WebhookPayload:
        """Create a new webhook payload record"""
        async with get_async_db_session() as session:
            webhook = WebhookPayload(
                guest_id=guest_id,
                event_type=event_type,
                payload=payload,
                headers=headers,
                processed=False,
                is_multiple=is_multiple
            )
            
            session.add(webhook)
            await session.flush()
            return webhook


# Legacy compatibility functions
def get_db_path():
    """Get the database path as a string (for backward compatibility)"""
    return str(DB_PATH)