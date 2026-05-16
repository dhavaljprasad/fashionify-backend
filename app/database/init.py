from pymongo import AsyncMongoClient
from beanie import init_beanie
from app.config.variables import ConfigVariables

from app.database.models import (
    Users,
    Subscriptions,
    Conversations,
    Messages,
    Images,
    Usage_Events,
    Pooling,
)

_client: AsyncMongoClient | None = None


async def init_mongo():
    global _client
    if not ConfigVariables.MONGO_URI:
        raise RuntimeError("MONGO_URI is not set")

    _client = AsyncMongoClient(ConfigVariables.MONGO_URI)
    db = _client[ConfigVariables.DATABASE_NAME]

    await init_beanie(
        database=db,
        document_models=[
            Users,
            Subscriptions,
            Conversations,
            Messages,
            Images,
            Usage_Events,
            Pooling,
        ],
    )


async def close_mongo():
    global _client
    if _client is not None:
        await _client.close()
        _client = None
