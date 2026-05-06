from imagekitio import ImageKit
from app.config.variables import ConfigVariables

imagekit = ImageKit(
    private_key=ConfigVariables.IMGKIT_PRIVATE_KEY,
)


def get_client_upload_auth_params():
    if imagekit:
        return imagekit.helper.get_authentication_parameters()
    else:
        return None


def get_user_uploaded_images(user_id: str, conversation_id: str, file_name: str):
    try:
        path = f"/{user_id}/uploads/{conversation_id}/{file_name}"

        url = imagekit.helper.build_url(
            url_endpoint=ConfigVariables.IMGKIT_URL_ENDPOINT,
            src=path,
        )

        return url

    except Exception as e:
        print("Unexpected error occured getting image URL:", e)
        return None
