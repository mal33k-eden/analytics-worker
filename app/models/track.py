from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class AnalyticsTrackBase(SQLModel, table=True):
    """
    Base model for tracking analytics events.

    Attributes:
        event_id: Unique identifier for the event
        app_id: Application identifier (e.g., 'esa')
        event_name: Name of the event being tracked (e.g., 'cart_add')
        event_data: Data specific to the event
        identity: User identification information from various analytics services
        metadata: Additional tracking metadata
        created_at: Timestamp when the event was created
    """
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    event_id: UUID = Field(default_factory=uuid4, primary_key=False)
    app_id: str = Field(default='esa', max_length=10, index=True)
    event_name: str = Field(max_length=125, index=True)
    event_data: Dict = Field(default_factory=dict, sa_column=Column(JSON))
    identity: Dict = Field(default_factory=dict, sa_column=Column(JSON))
    event_meta: Dict = Field(default_factory=dict, sa_column=Column(JSON))
    processed_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Needed for Column(JSON)
    class Config:
        arbitrary_types_allowed = True
