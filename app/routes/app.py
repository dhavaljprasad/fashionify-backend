from fastapi import APIRouter, Request
from app.database.queries.images import get_latest_user_images
from app.utils.imgkit import get_user_uploaded_images

router = APIRouter(prefix="/app", tags=["App"])


@router.get("/user-models")
async def get_user_models(request: Request):
    try:
        user = request.state.user
        user_id = user["id"]

        user_images_docs = await get_latest_user_images(user_id=user_id, limit=20)

        user_images = []
        for img_doc in user_images_docs:
            img_url = get_user_uploaded_images(
                user_id=user_id,
                conversation_id=str(img_doc.conversation_id),
                file_name=img_doc.image_name,
            )
            if img_url:
                user_images.append(img_url)

        return {
            "status": True,
            "data": user_images,
            "details": "User models fetched successfully",
        }

    except Exception as e:
        print("Unexpected error occured getting user models as:", e)
        return {"status": False, "data": None, "details": "Error getting user models"}
