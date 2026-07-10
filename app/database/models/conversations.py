from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime, timezone
from enum import StrEnum


class EntryType(StrEnum):
    LINK = "link"
    PRESTITCHED = "prestitched"
    CLOTHPIECE = "clothpiece"


class ConversationType(StrEnum):
    VISUALIZATION = "visualization"
    STYLIST = "stylist"


class Conversations(Document):
    user_id: PydanticObjectId
    conversation_id: PydanticObjectId = Field(default_factory=PydanticObjectId)
    entry_type: EntryType = EntryType.LINK
    conversation_type: ConversationType = ConversationType.VISUALIZATION
    title: str = "New Conversation"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "conversations"
