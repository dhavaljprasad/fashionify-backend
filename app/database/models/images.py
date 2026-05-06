from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime, timezone


class Images(Document):
    image_id: PydanticObjectId = Field(default_factory=PydanticObjectId, index=True)
    user_id: PydanticObjectId
    conversation_id: PydanticObjectId
    image_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "images"
