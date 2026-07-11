from app.database.init import Images
from beanie import PydanticObjectId


async def save_user_uploaded_images(
    user_id: str, conversation_id: str, image_name: str
):
    try:
        new_image = Images(
            user_id=PydanticObjectId(user_id),
            conversation_id=PydanticObjectId(conversation_id),
            image_name=image_name,
        )
        await new_image.insert()
        return new_image
    except Exception as e:
        print("Unexpected error occured saving the image as:", e)
        return None


async def get_bunch_images_name(image_ids: list[str]):
    try:
        obj_ids = [PydanticObjectId(img_id) for img_id in image_ids]

        fetched_images = await Images.find({"image_id": {"$in": obj_ids}}).to_list()

        return [img.image_name for img in fetched_images]

    except Exception as e:
        print("Unexpected error occured in mongo function fetching bunch images as", e)
        return None


async def get_latest_user_images(user_id: str, limit: int = 10):
    try:
        images = (
            await Images.find(
                {
                    "user_id": PydanticObjectId(user_id),
                    "image_name": "user_image.webp",
                }
            )
            .sort("-created_at")
            .limit(limit)
            .to_list()
        )

        return images

    except Exception as e:
        print(
            "Unexpected error occured in mongo function fetching latest user images as",
            e,
        )
        return None


async def get_all_user_images(user_id: str):
    try:
        images = (
            await Images.find(
                Images.user_id == PydanticObjectId(user_id),
            )
            .sort("-created_at")
            .to_list()
        )

        return images

    except Exception as e:
        print(
            "Unexpected error occured in mongo function fetching latest user images as",
            e,
        )
        return None
