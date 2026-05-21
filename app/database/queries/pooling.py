from app.database.init import Pooling
from beanie import PydanticObjectId


async def init_pooling_doc(user_id: str, pooling_type: str):
    try:
        new_pooling_doc = Pooling(user_id=user_id, pooling_type=pooling_type)
        await new_pooling_doc.save()
        return new_pooling_doc
    except Exception as e:
        print("Unexpected error occured in init_pooling mongo function as:", e)
        return None


async def update_pooling_status(pooling_id: str, status: str, data: dict = {}):
    try:
        pooling_doc = await Pooling.find_one(
            Pooling.pooling_id == PydanticObjectId(pooling_id)
        )
        if pooling_doc is None:
            print("Pooling document not found for pooling_id:", pooling_id)
            return None

        pooling_doc.status = status
        pooling_doc.data = data
        await pooling_doc.save()
        return pooling_doc
    except Exception as e:
        print("Unexpected error occured in update_pooling_status mongo function as:", e)
        return None


async def get_pooling_info(pooling_id: str):
    try:
        pooling_doc = await Pooling.find_one(
            Pooling.pooling_id == PydanticObjectId(pooling_id)
        )
        return pooling_doc
    except Exception as e:
        print("Unexpected error occured in get_pooling_info mongo function as:", e)
        return None
