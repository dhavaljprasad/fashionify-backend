from beanie import Document, PydanticObjectId
from pydantic import Field
from enum import StrEnum
from typing import Optional


class Status(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    NOT_STARTED = "not_started"


class Generation(StrEnum):
    SEE_ON = "see_on"
    DRESS_UP = "dress_up"
    THREE_SIXTY = "three_sixty"
    ITERATION = "iteration"
    COMPARISON = "comparison"


class Pooling(Document):
    pooling_id: PydanticObjectId = Field(default_factory=PydanticObjectId, index=True)
    user_id: PydanticObjectId
    status: Status = Status.NOT_STARTED
    pooling_type: Generation = Generation.SEE_ON
    data: Optional[dict] = {}

    class Settings:
        name = "pooling"
