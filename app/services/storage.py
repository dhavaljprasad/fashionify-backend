import boto3
import base64
from botocore.config import Config
from botocore.exceptions import ClientError
from app.config.variables import ConfigVariables

r2 = boto3.client(
    "s3",
    endpoint_url=ConfigVariables.R2_ENDPOINT,
    aws_access_key_id=ConfigVariables.R2_ACCESS_KEY_ID,
    aws_secret_access_key=ConfigVariables.R2_SECRET_ACCESS_KEY,
    region_name=ConfigVariables.R2_REGION,
    config=Config(signature_version="s3v4"),
)


class R2Storage:
    bucket = ConfigVariables.R2_BUCKET
    public_url = ConfigVariables.R2_PUBLIC_URL.rstrip("/")

    # base function to get _object_url
    @staticmethod
    def _object_url(key: str) -> str:
        return f"{R2Storage.public_url}/{key}"

    @staticmethod
    def get_user_uploaded_images(
        user_id: str,
        conversation_id: str,
        file_name: str,
    ):
        key = f"{user_id}/uploads/{conversation_id}/{file_name}"
        return R2Storage._object_url(key)

    @staticmethod
    def get_user_generated_images(
        user_id: str,
        conversation_id: str,
        file_name: str,
    ):
        key = f"{user_id}/generated/{conversation_id}/{file_name}"
        return R2Storage._object_url(key)

    @staticmethod
    def get_user_model_image(
        user_id: str,
        file_name: str,
    ):
        key = f"{user_id}/uploads/models/{file_name}"
        return R2Storage._object_url(key)

    @staticmethod
    def upload_generated_see_on_image(
        user_id: str,
        conversation_id: str,
        file_name: str,
        b64_image: str,
    ):
        try:
            key = f"{user_id}/generated/{conversation_id}/{file_name}"

            image_bytes = base64.b64decode(b64_image)

            r2.put_object(
                Bucket=R2Storage.bucket,
                Key=key,
                Body=image_bytes,
                ContentType="image/webp",
            )

            return {
                "url": R2Storage._object_url(key),
                "file_id": key,
                "file_path": key,
            }

        except Exception as e:
            print("Unexpected error uploading generated image:", e)
            return None

    # upload presigned functions
    @staticmethod
    def get_upload_image_presigned_url(
        user_id: str,
        conversation_id: str,
        file_name: str,
        expires_in: int = 600,
    ):
        try:
            key = f"{user_id}/uploads/{conversation_id}/{file_name}"

            upload_url = r2.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": R2Storage.bucket,
                    "Key": key,
                    "ContentType": "image/webp",
                },
                ExpiresIn=expires_in,
                HttpMethod="PUT",
            )

            return {
                "upload_url": upload_url,
                "url": R2Storage._object_url(key),
                "file_path": key,
            }

        except ClientError as e:
            print("Unexpected error generating upload presigned URL:", e)
            return None

    @staticmethod
    def get_model_image_presigned_url(
        user_id: str,
        file_name: str,
        expires_in: int = 600,
    ):
        try:
            key = f"{user_id}/uploads/models/{file_name}"

            upload_url = r2.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": R2Storage.bucket,
                    "Key": key,
                    "ContentType": "image/webp",
                },
                ExpiresIn=expires_in,
                HttpMethod="PUT",
            )

            return {
                "upload_url": upload_url,
                "url": R2Storage._object_url(key),
                "file_path": key,
            }

        except ClientError as e:
            print("Unexpected error generating model upload presigned URL:", e)
            return None

    # additional functions
    @staticmethod
    def upload_bytes(
        key: str,
        data: bytes,
        content_type: str,
    ):
        try:
            r2.put_object(
                Bucket=R2Storage.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )

            return R2Storage._object_url(key)

        except Exception as e:
            print(e)
            return None

    @staticmethod
    def delete(key: str):
        try:
            r2.delete_object(
                Bucket=R2Storage.bucket,
                Key=key,
            )

            return True

        except Exception as e:
            print(e)
            return False

    @staticmethod
    def exists(key: str):
        try:
            r2.head_object(
                Bucket=R2Storage.bucket,
                Key=key,
            )

            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise
