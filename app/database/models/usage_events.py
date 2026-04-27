from beanie import Document, PydanticObjectId


class Usage_Events(Document):
    user_id: PydanticObjectId
    subscription_id: PydanticObjectId
    token_used: int
    image_id: PydanticObjectId
    conversation_id: PydanticObjectId

    class Settings:
        name = "usage_events"
