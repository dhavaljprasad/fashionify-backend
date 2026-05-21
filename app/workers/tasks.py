from app.workers.celery import celery_app
from app.workers.runtime import run_async
from app.utils.imgkit import get_user_uploaded_images
from app.ai.openai import generate_image
from app.ai.prompts.user_see_on import user_see_on_prompt
from app.utils.imgkit import upload_generated_see_on_image
from app.database.queries.pooling import update_pooling_status
from app.database.queries.messages import add_image_message
from app.database.queries.images import save_user_uploaded_images


@celery_app.task(bind=True, max_retries=0)
def prestitched_seeon(
    self, conversation_id: str, user_id: str, pooling_id: str, link: str
):
    async def main_async_logic():
        try:
            print("Worker running for PRESTITCHED SEE ON with the following creds:")
            print("Conversation_id: ", conversation_id)
            print("User_id: ", user_id)
            print("Link: ", link)
            print("Pooling_id: ", pooling_id)

            update_response = await update_pooling_status(
                pooling_id=pooling_id,
                status="pending",
                data={},
            )

            # ======================================================================
            # STEP1: Load the user image for this conversation
            # ======================================================================

            print("===== Loading User Image for this Conversation =====")
            user_image_url = get_user_uploaded_images(
                user_id=user_id,
                conversation_id=conversation_id,
                file_name="user_image.webp",
            )
            print("===== Loaded User Image for this Conversation =====")

            # ======================================================================
            # STEP2: Load the user seeon image for this conversation
            # ======================================================================

            print("===== Loading See On Image for this Conversation =====")
            see_on_image_url = get_user_uploaded_images(
                user_id=user_id,
                conversation_id=conversation_id,
                file_name="user_see_on_image.webp",
            )
            print("===== Loaded See On Image for this Conversation =====")

            # ======================================================================
            # STEP3: Generate the new Try On Image
            # ======================================================================

            print("===== Generating the new Try On Image for this Conversation =====")
            image_64_bytes = generate_image(
                model="gpt-image-1.5",
                prompt=user_see_on_prompt,
                image_urls=[user_image_url, see_on_image_url],
                user_id=user_id,
            )
            print("===== Generated the new Try On Image for this Conversation =====")

            # ======================================================================
            # STEP4: Upload the new Try On Image
            # ======================================================================

            print(
                "===== Uploading the new Try On Image for this Conversation on Imgkit ====="
            )
            response = upload_generated_see_on_image(
                user_id=user_id,
                conversation_id=conversation_id,
                file_name="generated_see_on.webp",
                b64_image=image_64_bytes,
            )
            print(
                "===== Uploaded the new Try On Image for this Conversation on Imgkit ====="
            )

            update_response = await update_pooling_status(
                pooling_id=pooling_id,
                status="completed",
                data={"see_on_image_url": response},
            )

            image_doc = await save_user_uploaded_images(
                user_id=user_id,
                conversation_id=conversation_id,
                image_name="generated_see_on.webp",
            )

            added_message = await add_image_message(
                conversation_id=conversation_id,
                role="ai",
                text="Here's how the outfit looks on you!",
                image_ids=[str(image_doc.image_id)],
            )

            if update_response and added_message:
                print(response, "final response")

        except Exception as e:
            print("Unexpected worker error in prestitched_seeon as:", e)
            update_response = await update_pooling_status(
                pooling_id=pooling_id,
                status="failed",
                data={"error": str(e)},
            )

    return run_async(main_async_logic())


@celery_app.task(bind=True, max_retries=0)
def link_seeon(self, conversation_id: str, user_id: str, pooling_id: str, link: str):
    async def main_async_logic():
        try:
            print(conversation_id, "conversation_id")
            print(user_id, "user_id")
            print(pooling_id, "pooling_id")
            print(link, "link")
        except Exception as e:
            print("Unexpected worker error in prestitched_seeon as:", e)

    return run_async(main_async_logic())
