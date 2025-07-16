from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Guest(Base):
    __tablename__ = 'guests'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    prefix = Column(String)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    greeting_name = Column(String)
    phone = Column(String, unique=True)
    group_id = Column(String, nullable=False)
    is_group_primary = Column(Boolean, nullable=False)
    ready = Column(Boolean, nullable=False, default=False)
    sent_to_whatsapp = Column(String, default='pending')
    api_call_at = Column(DateTime)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    responded_with_button = Column(Boolean, default=False)
    message_id = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    api_calls = relationship("WhatsAppAPICall", back_populates="guest")
    webhook_payloads = relationship("WebhookPayload", back_populates="guest")
    
    # Indexes
    __table_args__ = (
        Index('idx_group_id', 'group_id'),
        Index('idx_message_id', 'message_id'),
    )


class WhatsAppAPICall(Base):
    __tablename__ = 'whatsapp_api_calls'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now())
    guest_id = Column(Integer, ForeignKey('guests.id'))
    direction = Column(String(10))  # 'request' or 'response'
    method = Column(String(10))
    url = Column(Text)
    headers = Column(Text)
    payload = Column(Text)
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    error_message = Column(Text)
    
    # Relationships
    guest = relationship("Guest", back_populates="api_calls")
    
    # Indexes
    __table_args__ = (
        Index('idx_api_calls_timestamp', 'timestamp'),
        Index('idx_api_calls_guest_id', 'guest_id'),
    )


class WebhookPayload(Base):
    __tablename__ = 'webhook_payloads'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now())
    guest_id = Column(Integer, ForeignKey('guests.id'))
    event_type = Column(String(50))
    payload = Column(Text)
    headers = Column(Text)
    processed = Column(Boolean, default=False)
    is_multiple = Column(Boolean, default=False)
    
    # Relationships
    guest = relationship("Guest", back_populates="webhook_payloads")
    
    # Indexes
    __table_args__ = (
        Index('idx_webhooks_timestamp', 'timestamp'),
        Index('idx_webhooks_event_type', 'event_type'),
        Index('idx_webhooks_guest_id', 'guest_id'),
    )