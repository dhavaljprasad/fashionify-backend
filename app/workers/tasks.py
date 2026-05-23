from app.workers.celery import celery_app
from app.workers.runtime import run_async
from app.utils.imgkit import get_user_uploaded_images
from app.ai.openai import generate_image
from app.ai.gemini import call_gemini_llm
from app.ai.prompts.user_see_on import user_see_on_prompt, gemini_see_on_prompt
from app.utils.imgkit import upload_generated_see_on_image
from app.database.queries.pooling import update_pooling_status
from app.database.queries.messages import add_image_message
from app.database.queries.images import save_user_uploaded_images
from app.database.queries.conversations import update_conversation_title

from pydantic import BaseModel


@celery_app.task(bind=True, max_retries=0)
def prestitched_seeon(
    self, conversation_id: str, user_id: str, pooling_id: str, link: str
):
    async def main_async_logic():
        try:
            # ======================================================================
            # STEP1: Updating pooling status with pending
            # ======================================================================
            print("STEP1: Updating pooling status with pending")
            update_response = await update_pooling_status(
                pooling_id=pooling_id,
                status="pending",
                data={},
            )

            # ======================================================================
            # STEP2: Load the user image for this conversation
            # ======================================================================
            print("STEP2: Loading User Image for this Conversation")
            user_image_url = get_user_uploaded_images(
                user_id=user_id,
                conversation_id=conversation_id,
                file_name="user_image.webp",
            )

            # ======================================================================
            # STEP3: Load the user seeon image for this conversation
            # ======================================================================
            print("STEP3: Loading See On Image for this Conversation")
            see_on_image_url = get_user_uploaded_images(
                user_id=user_id,
                conversation_id=conversation_id,
                file_name="user_see_on_image.webp",
            )

            # ======================================================================
            # STEP4: Generate the new Try On Image
            # ======================================================================
            print("STEP4: Generating the new Try On Image for this Conversation")
            image_64_bytes = generate_image(
                model="gpt-image-1.5",
                prompt=user_see_on_prompt,
                image_urls=[user_image_url, see_on_image_url],
                user_id=user_id,
            )

            # ======================================================================
            # STEP5: Upload the new Try On Image
            # ======================================================================
            print(
                "STEP5: Uploading the new Try On Image for this Conversation on Imgkit"
            )
            response = upload_generated_see_on_image(
                user_id=user_id,
                conversation_id=conversation_id,
                file_name="generated_see_on.webp",
                b64_image=image_64_bytes,
            )

            # ======================================================================
            # STEP6: Defining the output schema for Gemini LLM
            # ======================================================================
            print("STEP6: Defining the output schema for Gemini LLM")

            class GeminiSeeOnOutputSchema(BaseModel):
                outfit_description: str
                conversation_title: str

            # ======================================================================
            # STEP7: Calling Gemini API to get description and title
            # ======================================================================
            print("STEP7: Calling Gemini API to get description and title")
            gemini_response = call_gemini_llm(
                custom_prompt=gemini_see_on_prompt,
                image_url=response["url"],
                output_format="json",
                output_schema=GeminiSeeOnOutputSchema,
            )

            # ======================================================================
            # STEP8: Updating the conversation title
            # ======================================================================
            print("STEP8: Updating the conversation title")
            updated_conversation_doc = await update_conversation_title(
                conversation_id=conversation_id,
                title=gemini_response["conversation_title"],
            )

            # ======================================================================
            # STEP9: Saving the generated image in the images and messages collection
            # ======================================================================
            print(
                "STEP9: Saving the generated image in the images and messages collection"
            )
            image_doc = await save_user_uploaded_images(
                user_id=user_id,
                conversation_id=conversation_id,
                image_name="generated_see_on.webp",
            )

            added_message = await add_image_message(
                conversation_id=conversation_id,
                role="ai",
                text=gemini_response["outfit_description"],
                image_ids=[str(image_doc.image_id)],
            )

            # ======================================================================
            # STEP10: Updating the pooling status with completed and the new see on image url
            # ======================================================================
            update_response = await update_pooling_status(
                pooling_id=pooling_id,
                status="completed",
                data={
                    "see_on_image_url": response["url"],
                    "text": gemini_response["outfit_description"],
                },
            )

            if update_response and added_message and updated_conversation_doc:
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
