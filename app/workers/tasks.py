from app.workers.celery import celery_app
from app.workers.runtime import run_async
from app.utils.imgkit import get_user_uploaded_images
from app.ai.openai import generate_image
from app.ai.gemini import call_gemini_llm
from app.ai.prompts.user_see_on import (
    user_see_on_prompt,
    gemini_see_on_prompt,
    gemini_checking_cloth_prompt,
    gemini_see_on_link_prompt,
)
from app.ai.prompts.user_dress_up import gemini_user_dress_up_prompt
from app.utils.imgkit import upload_generated_see_on_image
from app.database.queries.pooling import update_pooling_status
from app.database.queries.messages import add_image_message, get_first_message
from app.database.queries.images import save_user_uploaded_images
from app.database.queries.conversations import update_conversation_title
from app.database.queries.models import get_model_document_by_id
from app.utils.scraper import scrape_product

from pydantic import BaseModel
import json


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
            # STEP2: Scraping the product data from the provided link
            # ======================================================================
            print("STEP2: Scraping the product data from the provided link")
            scraped_data = await scrape_product(link)

            # ======================================================================
            # STEP3: Defining the output schema for Gemini LLM
            # ======================================================================
            print("STEP3: Defining the output schema for Gemini LLM")

            class GeminiCheckingClothOutputSchema(BaseModel):
                is_clothing_item: bool

            # ======================================================================
            # STEP4: Checking if the scraped data is a clothing item or not
            # ======================================================================
            print("STEP4: Checking if the scraped data is a clothing item or not")
            checking_clothing_item_response = call_gemini_llm(
                custom_prompt=f"${gemini_checking_cloth_prompt}\n\nProduct Heading: {scraped_data['product_type']}",
                output_format="json",
                output_schema=GeminiCheckingClothOutputSchema,
            )

            # ======================================================================
            # STEP5: If it is not a clothing item, update the pooling status with failed and return
            # ======================================================================
            if not checking_clothing_item_response["is_clothing_item"]:
                print(
                    "The provided link does not belong to a clothing item. Updating pooling status with failed."
                )
                update_response = await update_pooling_status(
                    pooling_id=pooling_id,
                    status="failed",
                    data={
                        "error": "The provided link does not belong to a clothing item."
                    },
                )
                return

            # ======================================================================
            # STEP6: Load the user image for this conversation
            # ======================================================================
            print("STEP6: Loading User Image for this Conversation")
            user_image_url = get_user_uploaded_images(
                user_id=user_id,
                conversation_id=conversation_id,
                file_name="user_image.webp",
            )

            # ======================================================================
            # STEP7: Load the first text message as well if any
            # ======================================================================
            print("STEP7: Loading the first text message if any")
            first_message_doc = await get_first_message(conversation_id=conversation_id)
            first_text_message = first_message_doc.text
            measurements = None

            # ======================================================================
            # STEP8: If first_text_message is a valid string, loading user model
            # ======================================================================
            print("STEP8: If first_text_message is valid string, loading user_model")
            if first_text_message:
                model_document = await get_model_document_by_id(
                    model_id=first_text_message
                )
                if model_document.gender == "female":
                    measurements = model_document.female_measurements
                elif model_document.gender == "male":
                    measurements = model_document.male_measurements

            # ======================================================================
            # STEP9: Generate the new Try On Image
            # ======================================================================
            print("STEP9: Generating the new Try On Image for this Conversation")
            image_64_bytes = generate_image(
                model="gpt-image-1.5",
                prompt=user_see_on_prompt,
                image_urls=[user_image_url, scraped_data["product_image"]],
                user_id=user_id,
            )

            # ======================================================================
            # STEP10: Upload the new Try On Image
            # ======================================================================
            print(
                "STEP10: Uploading the new Try On Image for this Conversation on Imgkit"
            )
            response = upload_generated_see_on_image(
                user_id=user_id,
                conversation_id=conversation_id,
                file_name="generated_see_on.webp",
                b64_image=image_64_bytes,
            )

            # ======================================================================
            # STEP11: Defining the output schema for Gemini LLM final response
            # ======================================================================
            print("STEP11: Defining the output schema for Gemini LLM final response")

            class GeminiFinalResponseSchema(BaseModel):
                outfit_description: str
                conversation_title: str

            # ======================================================================
            # STEP12: Calling Gemini API to get description and title based on the generated see on image
            # ======================================================================
            print(
                "STEP12: Calling Gemini API to get description and title based on the generated see on image"
            )
            gemini_response = call_gemini_llm(
                custom_prompt=f"{gemini_see_on_link_prompt} \n\n Garment sizing chart:{json.dumps(scraped_data.get('product_size', ''))} \n\n User body measurements:{measurements}",
                image_url=response["url"],
                output_format="json",
                output_schema=GeminiFinalResponseSchema,
            )

            # ======================================================================
            # STEP13: Updating the conversation title
            # ======================================================================
            print("STEP13: Updating the conversation title")
            updated_conversation_doc = await update_conversation_title(
                conversation_id=conversation_id,
                title=gemini_response["conversation_title"],
            )

            # ======================================================================
            # STEP14: Saving the generated image in the images and messages collection
            # ======================================================================
            print(
                "STEP14: Saving the generated image in the images and messages collection"
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
            # STEP15: Updating the pooling status with completed and the new see on image url
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
def dress_up(
    self,
    conversation_id: str,
    user_id: str,
    pooling_id: str,
    images: str,
    dress_name: str,
    custom_instruction: str,
):
    async def main_async_logic():
        try:
            print(conversation_id, "=== Conversation Id")
            print(images, "=== Images")
            print(dress_name, "=== Dress Name")
            print(custom_instruction, "=== Custom Instruction")
            print(user_id, "=== User Id")
            print(pooling_id, "=== Pooling Id")

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
            # STEP2: Fetching fabric images from ImgKit
            # ======================================================================
            print("STEP2: Fetching fabric images from ImgKit")
            fabric_images = []
            for image in images:
                fabric_image_url = get_user_uploaded_images(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    file_name=f"{image}.webp",
                )
                fabric_images.append(fabric_image_url)

            print(fabric_images, "==========print")
            # ======================================================================
            # STEP3: Fetching model image from ImgKit
            # ======================================================================
            print("STEP3: Fetching model image from ImgKit")
            model_image_url = get_user_uploaded_images(
                user_id=user_id,
                conversation_id=conversation_id,
                file_name="user_image.webp",
            )

            # ======================================================================
            # STEP4: Creating ordered image array
            # ======================================================================
            print("STEP4: Creating ordered image array")
            final_image_array = [model_image_url, *fabric_images]

            # ======================================================================
            # STEP5: Generating final image gen prompt
            # ======================================================================
            print("STEP5: Generating final image gen prompt")
            image_reference_text = []

            for index, image_name in enumerate(images):
                position = index + 2

                if position == 2:
                    order = "second"
                elif position == 3:
                    order = "third"
                elif position == 4:
                    order = "fourth"
                elif position == 5:
                    order = "fifth"
                else:
                    order = f"{position}th"

                garment_name = image_name.split(".")[0].replace("_", " ")

                image_reference_text.append(
                    f"The {order} image is a {garment_name} reference."
                )

            image_reference_text = "\n".join(image_reference_text)

            prompt = f"""
                I've attached {len(fabric_images) + 1} images.

                The first image is of a model.

                {image_reference_text}

                Generate a photorealistic full-body image of the model wearing the supplied garments.

                Preserve all colors, textures, embroidery, prints, stitching details and fabric characteristics exactly.

                Construct a complete {dress_name} outfit using the supplied garment references.

                Do not invent garments that were not supplied.

                {custom_instruction or ""}
            """.strip()

            # ======================================================================
            # STEP6: Generating final image
            # ======================================================================
            print("STEP6: Generating final image")
            image_64_bytes = generate_image(
                model="gpt-image-1.5",
                prompt=prompt,
                image_urls=final_image_array,
                user_id=user_id,
            )

            # ======================================================================
            # STEP7: Upload the new Dress Up Image
            # ======================================================================
            print(
                "STEP7: Uploading the new Dress Up Image for this Conversation on Imgkit"
            )
            response = upload_generated_see_on_image(
                user_id=user_id,
                conversation_id=conversation_id,
                file_name="generated_see_on.webp",
                b64_image=image_64_bytes,
            )

            # ======================================================================
            # STEP9: Defining the output schema for Gemini LLM final response
            # ======================================================================
            print("STEP9: Defining the output schema for Gemini LLM final response")

            class GeminiFinalResponseSchema(BaseModel):
                outfit_description: str
                conversation_title: str

            # ======================================================================
            # STEP10: Calling Gemini API to get description and title based on the generated see on image
            # ======================================================================
            print(
                "STEP10: Calling Gemini API to get description and title based on the generated see on image"
            )
            gemini_response = call_gemini_llm(
                custom_prompt=f"{gemini_user_dress_up_prompt}",
                image_url=response["url"],
                output_format="json",
                output_schema=GeminiFinalResponseSchema,
            )

            # ======================================================================
            # STEP11: Updating the conversation title
            # ======================================================================
            print("STEP11: Updating the conversation title")
            updated_conversation_doc = await update_conversation_title(
                conversation_id=conversation_id,
                title=gemini_response["conversation_title"],
            )

            # ======================================================================
            # STEP12: Saving the generated image in the images and messages collection
            # ======================================================================
            print(
                "STEP12: Saving the generated image in the images and messages collection"
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
            # STEP13: Updating the pooling status with completed and the new see on image url
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
            print("Unexpected worker error in dress_up as: ", e)
            update_response = await update_pooling_status(
                pooling_id=pooling_id,
                status="failed",
                data={"error": str(e)},
            )

    return run_async(main_async_logic())
