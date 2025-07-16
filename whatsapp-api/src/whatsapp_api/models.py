from pydantic import BaseModel, Field, validator
from typing import Optional
import re

class GuestIn(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    greeting_name: Optional[str] = None
    phone: Optional[str] = None
    group_id: str = Field(..., min_length=1)
    is_group_primary: bool

    @validator("phone")
    def validate_phone(cls, v, values):
        if values.get("is_group_primary") and not v:
            raise ValueError("Primary contact must have a phone number.")
        if v:
            if not re.match(r"^\+\d{10,15}$", v):
                raise ValueError("Phone must be in E.164 format (e.g., +1234567890).")
        return v

    @validator("group_id")
    def group_id_not_empty(cls, v):
        if not v.strip():
            raise ValueError("group_id must not be empty.")
        return v

    @validator("first_name", "last_name")
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Name fields must not be empty.")
        return v
