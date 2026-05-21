from fastapi import APIRouter
from app.database.queries.pooling import get_pooling_info

router = APIRouter(prefix="/pooling", tags=["Pooling"])


@router.get("/{pooling_id}")
async def get_pooling_info_function(pooling_id: str):
    try:
        pooling_doc = await get_pooling_info(pooling_id=pooling_id)
        if pooling_doc is None:
            return {"error": "Pooling document not found"}
        return {
            "pooling_id": str(pooling_doc.pooling_id),
            "status": pooling_doc.status,
            "data": pooling_doc.data,
        }
    except Exception as e:
        print(
            "Unexpected error occured getting pooling info for pooling_id:",
            pooling_id,
            "error:",
            e,
        )
        return None
