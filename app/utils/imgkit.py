from imagekitio import ImageKit
from app.config.variables import ConfigVariables

import base64

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


def get_user_generated_images(user_id: str, conversation_id: str, file_name: str):
    try:
        path = f"/{user_id}/generated/{conversation_id}/{file_name}"

        url = imagekit.helper.build_url(
            url_endpoint=ConfigVariables.IMGKIT_URL_ENDPOINT,
            src=path,
        )

        return url

    except Exception as e:
        print("Unexpected error occured getting image URL:", e)
        return None


def upload_generated_see_on_image(
    user_id: str, conversation_id: str, file_name: str, b64_image: str
):
    try:
        folder = f"/{user_id}/generated/{conversation_id}"
        image_bytes = base64.b64decode(b64_image)

        response = imagekit.files.upload(
            file=image_bytes,
            file_name=file_name,
            folder=folder,
            use_unique_file_name=False,
            overwrite_file=True,
        )

        return {
            "url": response.url,
            "file_id": response.file_id,
            "file_path": f"{folder}/{file_name}",
        }

    except Exception as e:
        print("Unexpected error occured saving generated see on image on imgkit as:", e)
        return None


def get_user_model_image(user_id: str, file_name: str):
    try:
        path = f"/{user_id}/uploads/models/{file_name}"

        url = imagekit.helper.build_url(
            url_endpoint=ConfigVariables.IMGKIT_URL_ENDPOINT,
            src=path,
        )

        return url

    except Exception as e:
        print("Unexpected error occured getting image URL:", e)
        return None
