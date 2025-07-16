from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re


class GuestBase(BaseModel):
    prefix: Optional[str] = None
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    greeting_name: Optional[str] = None
    phone: Optional[str] = None
    group_id: str = Field(..., min_length=1)
    is_group_primary: bool
    ready: bool = False


class GuestCreate(GuestBase):
    @validator('phone')
    def validate_phone(cls, v, values):
        # Only check if primary requires phone - this is business logic, not format validation
        if values.get('is_group_primary') and not v:
            raise ValueError('Phone is required for primary contacts')
        return v


class GuestUpdate(BaseModel):
    ready: Optional[bool] = None


class GuestResponse(GuestBase):
    id: int
    sent_to_whatsapp: str
    api_call_at: Optional[datetime]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    responded_with_button: Optional[datetime]
    message_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    phone_class: Optional[str] = None
    
    class Config:
        from_attributes = True