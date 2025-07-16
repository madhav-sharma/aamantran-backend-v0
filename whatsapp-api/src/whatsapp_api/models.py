from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re


class GuestBase(BaseModel):
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
        if values.get('is_group_primary') and not v:
            raise ValueError('Phone is required for primary contacts')
        
        if v:
            # Strip any formatting
            clean_phone = re.sub(r'[^\d+]', '', v)
            
            # Check E.164 format for India (+91) or UAE (+971)
            if not (
                (clean_phone.startswith('+91') and len(clean_phone) == 13) or
                (clean_phone.startswith('+971') and len(clean_phone) == 13)
            ):
                raise ValueError('Phone must be Indian (+91 with 10 digits) or UAE (+971 with 9 digits)')
            
            return clean_phone
        return v
    
    @validator('group_id')
    def clean_group_id(cls, v):
        return v.strip()


class GuestUpdate(BaseModel):
    ready: Optional[bool] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    greeting_name: Optional[str] = None
    phone: Optional[str] = None


class GuestResponse(GuestBase):
    id: int
    sent_to_whatsapp: str
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    message_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    phone_class: Optional[str] = None
    
    class Config:
        orm_mode = True 