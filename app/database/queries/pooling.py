from app.database.init import Pooling


async def init_pooling_doc(user_id: str, pooling_type: str):
    try:
        new_pooling_doc = Pooling(user_id=user_id, pooling_type=pooling_type)
        await new_pooling_doc.save()
        return new_pooling_doc
    except Exception as e:
        print("Unexpected error occured in init_pooling mongo function as:", e)
        return None
