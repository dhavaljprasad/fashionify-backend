from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime, timezone
from enum import StrEnum


class TypeOfUser(StrEnum):
    INDEPENDENT = "independent"
    STORE = "store"
    TAILOR = "tailor"


class Users(Document):
    user_id: PydanticObjectId = Field(default_factory=PydanticObjectId)
    name: str = ""
    email: str = ""
    provider: str = ""
    provider_user_id: str = ""
    image_url: str = ""
    type_of_user: TypeOfUser = TypeOfUser.INDEPENDENT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
