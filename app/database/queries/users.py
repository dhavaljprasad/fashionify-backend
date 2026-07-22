from app.database.init import Users
from typing import Dict, Optional
from beanie import PydanticObjectId


async def save_or_update_user(user_dict: Dict):
    try:
        # Checking if user already exists
        user = await Users.find_one(
            Users.email == user_dict["email"], Users.active == True
        )

        # Updating if the user already exists
        if user:
            user.name = user_dict["name"]
            user.image_url = user_dict["image_url"]
            await user.save()
            return user

        # Making new user if user does not exist
        user = Users(
            name=user_dict["name"],
            email=user_dict["email"],
            image_url=user_dict["image_url"],
            provider=user_dict["provider"],
            provider_user_id=user_dict["provider_user_id"],
        )
        await user.insert()
        return user

    except Exception as e:
        print("Unexpected error occured saving or updating user as:", e)
        return False


async def update_user_profile(
    user_id: str,
    name: str,
    type_of_user: str,
    bussiness_name: Optional[str] = None,
    bussiness_address: Optional[str] = None,
):
    try:
        user = await Users.find_one(Users.user_id == PydanticObjectId(user_id))
        if user is None:
            return None

        user.name = name
        user.type_of_user = type_of_user
        user.bussiness_name = bussiness_name
        user.bussiness_address = bussiness_address

        await user.save()
        return user
    except Exception as e:
        print("Unexpected error occured updating user profile as:", e)
        return None


async def delete_user(user_id: str, user_email: str):
    try:
        user_doc = await Users.find_one(
            Users.user_id == PydanticObjectId(user_id), Users.email == user_email
        )
        user_doc.active = False

        await user_doc.save()
        return user_doc
    except Exception as e:
        print(f"Unexpected error occured in query function delete_user as: {e}")
