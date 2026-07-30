from app.database.init import WardrobeItems
from app.database.models.wardrobe_items import ImagesDict


async def add_wardrobe_items(
    user_id: str,
    original_image: str,
    item_name: str,
    metadata: dict,
    model_id: str | None = None,
):
    try:
        wardrobe_item = WardrobeItems(
            user_id=user_id,
            model_id=model_id,
            images=ImagesDict(processed_image="", original_image=original_image),
            item_name=item_name,
            metadata=metadata,
        )
        await wardrobe_item.insert()
        return wardrobe_item
    except Exception as e:
        print(f"Unexpected error occurred in mongo function add_wardrobe_items: {e}")
        return None


async def get_general_wardrobe_items(user_id: str):
    try:
        wardrobe_items = await WardrobeItems.find(
            WardrobeItems.user_id == user_id,
            WardrobeItems.model_id == None,
        ).to_list()

        return wardrobe_items

    except Exception as e:
        print(
            f"Unexpected error occurred in mongo function get_general_wardrobe_items: {e}"
        )
        return []


async def get_model_wardrobe_items(user_id: str, model_id: str):
    try:
        wardrobe_items = await WardrobeItems.find(
            WardrobeItems.user_id == user_id,
            WardrobeItems.model_id == model_id,
        ).to_list()

        return wardrobe_items

    except Exception as e:
        print(
            f"Unexpected error occurred in mongo function get_general_wardrobe_items: {e}"
        )
        return []
