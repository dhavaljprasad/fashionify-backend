from app.database.init import Users
from typing import Dict


async def save_or_update_user(user_dict: Dict):
    try:
        # Checking if user already exists
        user = await Users.find_one(Users.email == user_dict["email"])

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
