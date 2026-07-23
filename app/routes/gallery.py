from fastapi import APIRouter, Request
from app.database.queries.images import get_all_user_images
from app.database.queries.conversations import get_conversation_doc
from app.services.storage import R2Storage

router = APIRouter(prefix="/gallery", tags=["Gallery"])


@router.get("/")
async def get_user_gallery_function(request: Request):
    try:
        user = request.state.user
        user_id = user["id"]

        images_list = await get_all_user_images(user_id=user_id)
        if images_list:
            final_images_list = []
            for image in images_list:

                if "generated" in image.image_name:
                    conversation_doc = await get_conversation_doc(
                        user_id=user_id, conversation_id=str(image.conversation_id)
                    )

                    image_obj = {
                        "image_url": R2Storage.get_user_generated_images(
                            user_id=user_id,
                            conversation_id=str(image.conversation_id),
                            file_name=image.image_name,
                        ),
                        "conversation_id": str(image.conversation_id),
                        "conversation_type": conversation_doc.conversation_type
                        or "visualization",
                    }
                    final_images_list.append(image_obj)

            return {"images": final_images_list}
        else:
            return {"images": []}
    except Exception as e:
        print("Unexpected error occured getting gallery for user as :", e)
        return None
