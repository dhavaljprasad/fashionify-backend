from beanie import Document, PydanticObjectId
from pydantic import Field
from typing import Optional
from datetime import datetime, timezone
from enum import StrEnum


class RoleType(StrEnum):
    USER = "user"
    AI = "ai"


class Messages(Document):
    message_id: PydanticObjectId = Field(default_factory=PydanticObjectId, index=True)
    conversation_id: PydanticObjectId
    role: RoleType
    text: Optional[str] = None
    image_id: Optional[PydanticObjectId] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "messages"
