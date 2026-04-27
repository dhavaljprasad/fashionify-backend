from datetime import datetime, timezone
from beanie import Document, PydanticObjectId
from pydantic import Field


class Subscriptions(Document):
    user_id: PydanticObjectId
    subscription_name: str
    subscription_id: PydanticObjectId = Field(default_factory=PydanticObjectId)
    total_images_allowed: int
    total_images_used: int = 0
    current_month_images_allowed: int
    current_month_images_used: int = 0
    renewal_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "subscriptions"
