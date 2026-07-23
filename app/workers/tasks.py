from app.workers.celery import celery_app
from app.workers.runtime import run_async
from app.ai.openai import (
    generate_image,
    tool_call,
    llm_call_without_images,
    llm_call_with_images,
)
from app.ai.gemini import call_gemini_llm
from app.ai.prompts.user_see_on import (
    user_see_on_prompt,
    gemini_see_on_prompt,
    gemini_checking_cloth_prompt,
    gemini_see_on_link_prompt,
)
from app.ai.prompts.user_dress_up import (
    gemini_user_dress_up_prompt,
    gemini_final_prompt_generation_prompt,
)
from app.ai.prompts.price_comparison import gemini_price_comparison_prompt
from app.ai.prompts.intent_analyzer import intent_clasifier_prompt
from app.ai.prompts.irrelevant_reply import irrelevant_reply_prompt
from app.ai.prompts.feedback_reference import feedback_reference_prompt
from app.ai.prompts.feedback_reply import feedback_reply_prompt
from app.ai.prompts.edit_reference import edit_reference_prompt
from app.ai.prompts.edit_softner_enhancer import edit_softener_prompt
from app.ai.prompts.edit_reply import edit_feedback_reply_prompt
from app.services.storage import R2Storage
from app.database.queries.pooling import update_pooling_status
from app.database.queries.messages import (
    add_image_message,
    get_first_message,
    get_last_20_messages,
    get_message_by_message_id,
)
from app.database.queries.images import save_user_uploaded_images, get_image_by_image_id
from app.database.queries.conversations import update_conversation_title
from app.database.queries.models import get_model_document_by_id
from app.database.queries.comparison_analytics import save_comparison_analytics
from app.utils.scraper import scrape_product
from app.utils.comparison_scraper import scrape_price_comparison
from app.ai.prompts.dress_up_config import DRESS_DESCRIPTIONS
from app.ai.tools import intent_tool

from beanie import PydanticObjectId
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
            user_image_url = R2Storage.get_user_uploaded_images(
                user_id=user_id,
                conversation_id=conversation_id,
                file_name="user_image.webp",
            )

            # ======================================================================
            # STEP3: Load the user seeon image for this conversation
            # ======================================================================
            print("STEP3: Loading See On Image for this Conversation")
            see_on_image_url = R2Storage.get_user_uploaded_images(
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
            print("STEP5: Uploading the new Try On Image for this Conversation on R2")
            response = R2Storage.upload_generated_see_on_image(
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
            user_image_url = R2Storage.get_user_uploaded_images(
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
            print("STEP10: Uploading the new Try On Image for this Conversation on R2")
            response = R2Storage.upload_generated_see_on_image(
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
            # STEP2: Fetching fabric images from R2
            # ======================================================================
            print("STEP2: Fetching fabric images from R2")
            fabric_images = []
            for image in images:
                fabric_image_url = R2Storage.get_user_uploaded_images(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    file_name=f"{image}",
                )
                fabric_images.append(fabric_image_url)

            # ======================================================================
            # STEP3: Fetching model image from R2
            # ======================================================================
            print("STEP3: Fetching model image from R2")
            model_image_url = R2Storage.get_user_uploaded_images(
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
            # STEP5: Lookup DressDescription from config & making passing prompt
            # ======================================================================
            dress_config_description = DRESS_DESCRIPTIONS[dress_name]

            # ======================================================================
            # STEP6: Generating final pass-on prompt for image generation
            # ======================================================================
            print("STEP6: Generating final pass-on prompt for image generation")
            custom_dress_description = call_gemini_llm(
                custom_prompt=f"${gemini_final_prompt_generation_prompt}\n\nProduct Description:${dress_config_description} \n\nCustom User Prompt:${custom_instruction.strip()}",
                output_format="text",
            )

            # ======================================================================
            # STEP7: Generating final image gen prompt
            # ======================================================================
            print("STEP7: Generating final image gen prompt")
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
                I've attached {len(final_image_array)} images.

                IMAGE REFERENCES:
                The first image is the identity and composition reference for the subject.
                {image_reference_text}

                TASK:
                Create a realistic apparel visualization.
                The subject should already be wearing the complete outfit described below.

                OUTFIT SPECIFICATION:
                {dress_name}:{custom_dress_description}

                GARMENT PRESERVATION RULES:
                Use each garment reference only for its corresponding garment.
                Preserve exactly:
                - colors
                - fabric
                - texture
                - embroidery
                - prints
                - stitching
                - borders
                - trims
                - embellishments
                - logos
                - patterns
                Do not redesign, simplify, replace, merge, or invent any garment.

                FIT & DRAPING:
                Resize and naturally fit the supplied garments to the model's body while preserving their design.
                Only adjust:
                - scale
                - draping
                - folding
                - natural fabric deformation
                Do not alter the garment construction.

                IDENTITY PRESERVATION:
                The first image defines the subject.
                Preserve exactly:
                - face
                - hairstyle
                - body proportions
                - pose
                - camera angle
                - framing
                - crop
                - perspective
                - lighting
                - background
                Maintain the identity and composition from Image 1. Render the subject naturally wearing the supplied outfit.

                SAFETY:
                The subject should appear naturally and completely dressed in the finished outfit.                
            """.strip()

            # ======================================================================
            # STEP8: Generating final image
            # ======================================================================
            print("STEP8: Generating final image")
            image_64_bytes = generate_image(
                model="gpt-image-1.5",
                prompt=prompt,
                image_urls=final_image_array,
                user_id=user_id,
            )

            # ======================================================================
            # STEP9: Upload the new Dress Up Image
            # ======================================================================
            print("STEP9: Uploading the new Dress Up Image for this Conversation on R2")
            response = R2Storage.upload_generated_see_on_image(
                user_id=user_id,
                conversation_id=conversation_id,
                file_name="generated_see_on.webp",
                b64_image=image_64_bytes,
            )

            # ======================================================================
            # STEP10: Defining the output schema for Gemini LLM final response
            # ======================================================================
            print("STEP11: Defining the output schema for Gemini LLM final response")

            class GeminiFinalResponseSchema(BaseModel):
                outfit_description: str
                conversation_title: str

            # ======================================================================
            # STEP11: Calling Gemini API to get description and title based on the generated see on image
            # ======================================================================
            print(
                "STEP11: Calling Gemini API to get description and title based on the generated see on image"
            )
            gemini_response = call_gemini_llm(
                custom_prompt=f"{gemini_user_dress_up_prompt}",
                image_url=response["url"],
                output_format="json",
                output_schema=GeminiFinalResponseSchema,
            )

            # ======================================================================
            # STEP12: Updating the conversation title
            # ======================================================================
            print("STEP12: Updating the conversation title")
            updated_conversation_doc = await update_conversation_title(
                conversation_id=conversation_id,
                title=gemini_response["conversation_title"],
            )

            # ======================================================================
            # STEP13: Saving the generated image in the images and messages collection
            # ======================================================================
            print(
                "STEP13: Saving the generated image in the images and messages collection"
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
            # STEP14: Updating the pooling status with completed and the new see on image url
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


@celery_app.task(bind=True, max_retries=0)
def price_compare(self, product_url: str, user_id: str, pooling_id: str):
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
            # STEP2: Scraping the product data from the provided link
            # ======================================================================
            print("STEP2: Scraping the product data from the provided link")
            scraped_data = await scrape_price_comparison(link=product_url)

            # ======================================================================
            # STEP3: Defining the output schema for Gemini LLM
            # ======================================================================
            print("STEP3: Defining the output schema for Gemini LLM")

            class ComparisonTable(BaseModel):
                brand_name: str
                price: str
                url: str

            class GeminiProductScraper(BaseModel):
                product_image_url: str
                product_name: str
                product_price: str
                comparison_table: list[ComparisonTable]
                recommendation_to_buy: bool
                lowest_price: str
                highest_price: str

            # ======================================================================
            # STEP4: Getting usable values out of the scraped data
            # ======================================================================
            print("STEP4: Getting usable values out of the scraped data")

            custom_prompt = f"""
            {gemini_price_comparison_prompt}

            ========================================
            SCRAPED HTML
            ========================================

            {scraped_data.model_dump_json(indent=2)}
            """

            gemini_comparison_result = call_gemini_llm(
                custom_prompt=custom_prompt,
                output_format="json",
                output_schema=GeminiProductScraper,
            )

            print(gemini_comparison_result, "result ===========")

            saved_comparison_doc = await save_comparison_analytics(
                user_id=user_id,
                searched_url=product_url,
                comparison_result=gemini_comparison_result,
            )

            if gemini_comparison_result and saved_comparison_doc:
                # ======================================================================
                # STEP5: Updating the pooling status with completed and returning the response
                # ======================================================================
                await update_pooling_status(
                    pooling_id=pooling_id,
                    status="completed",
                    data={"smart_compare": gemini_comparison_result},
                )

        except Exception as e:
            print("Unexpected worker error in price_compare as: ", e)
            await update_pooling_status(
                pooling_id=pooling_id,
                status="failed",
                data={"error": str(e)},
            )

    return run_async(main_async_logic())


@celery_app.task(bind=True, max_retries=0)
def visualization_iteration(
    self, user_id: str, conversation_id: str, message: str, pooling_id: str
):
    async def main_async_logic():
        try:
            # ======================================================================
            # STEP1: Updating pooling status with pending
            # ======================================================================
            print("STEP1: Updating pooling status with pending")
            await update_pooling_status(
                pooling_id=pooling_id,
                status="pending",
                data={},
            )

            # ======================================================================
            # STEP2: Saving the user message in the DB
            # ======================================================================
            print("STEP2: Saving the user message in the DB")
            added_message = await add_image_message(
                conversation_id=conversation_id,
                role="user",
                text=message,
                image_ids=[],
            )

            # ======================================================================
            # STEP3: Fetching upto last 20 messages
            # ======================================================================
            print("STEP3: Fetching & Cleaning upto last 20 messages")
            latest_messages = await get_last_20_messages(
                conversation_id=conversation_id
            )

            processed_message_history = []
            for msg in latest_messages:
                updated_message_object = {
                    "role": msg.role,
                    "text": msg.text,
                    "image_ids": msg.image_ids,
                    "message_id": str(msg.message_id),
                }
                processed_message_history.append(updated_message_object)

            # ======================================================================
            # STEP4: Making tools call to determine if the intent is: irrelevant | feedback | edit
            # ======================================================================
            print(
                "STEP4: Making tools call to determine if the intent is: irrelevant | feedback | edit"
            )
            context = json.dumps(processed_message_history)
            tools_response = tool_call(
                tools=[intent_tool],
                custom_prompt=intent_clasifier_prompt,
                context=context,
            )

            intent = tools_response["intent"]
            reasoning = tools_response["reasoning"]

            print(f"Intent found: {intent}")
            print(f"Reason behind the intent: {reasoning}")

            # ======================================================================
            # STEP5: Orchestrating based on intent
            # ======================================================================
            print("STEP5: Orchestrating based on intent")

            if intent == "irrelevant":
                # ======================================================================
                # STEP6: Generating response for irrelevant intent
                # ======================================================================
                print("STEP6: Generating response for irrelevant intent")

                final_reply = llm_call_without_images(
                    custom_prompt=irrelevant_reply_prompt,
                    context=f"Conversation history:\n{context} \n\nCurrent message:\n{message} \n\nReason for Intent: \n{reasoning}",
                )

                # ======================================================================
                # STEP7: Saving the generated message in the DB
                # ======================================================================
                print("STEP7: Saving the generated message in the DB")
                added_message = await add_image_message(
                    conversation_id=conversation_id,
                    role="ai",
                    text=final_reply,
                    image_ids=[],
                )

                # ======================================================================
                # STEP8: Updating the pooling doc along with the response
                # ======================================================================
                print("STEP8: Updating the pooling doc along with the response")
                await update_pooling_status(
                    pooling_id=pooling_id,
                    status="completed",
                    data={
                        "iteration_result": {
                            "text": final_reply,
                            "role": "ai",
                            "images": [],
                            "message_id": str(added_message.message_id),
                        },
                        "status": "success",
                    },
                )

            elif intent == "feedback":
                # ======================================================================
                # STEP6: Checking which message image or messages image needs feedback on
                # ======================================================================
                print(
                    "STEP6: Checking which message image or messages image needs feedback on"
                )
                message_ids_string = llm_call_without_images(
                    custom_prompt=feedback_reference_prompt,
                    context=f"Conversation history:\n{context} \n\nCurrent message:\n{message}",
                )

                message_ids = json.loads(message_ids_string)

                # ======================================================================
                # STEP7: Fetch image documents and group image URLs by message
                # ======================================================================
                print(
                    "STEP7: Fetching image documents and grouping image URLs by message..."
                )
                passing_context = [
                    {
                        "type": "input_text",
                        "text": (
                            f"Current user message: {message}\n\n"
                            "Here are the image(s) being referred to:"
                        ),
                    }
                ]

                for idx, msg_id in enumerate(message_ids, start=1):
                    message_doc = await get_message_by_message_id(message_id=msg_id)
                    image_ids = message_doc.image_ids

                    passing_context.append(
                        {
                            "type": "input_text",
                            "text": f"Image {idx} (message_id: {msg_id}):",
                        }
                    )

                    for img_id in image_ids:
                        image_doc = await get_image_by_image_id(image_id=img_id)

                        if message_doc.role == "user":
                            image_url = R2Storage.get_user_uploaded_images(
                                user_id=user_id,
                                conversation_id=conversation_id,
                                file_name=image_doc.image_name,
                            )
                        else:  # message_doc.role == "ai"
                            image_url = R2Storage.get_user_generated_images(
                                user_id=user_id,
                                conversation_id=conversation_id,
                                file_name=image_doc.image_name,
                            )

                        passing_context.append(
                            {
                                "type": "input_image",
                                "image_url": image_url,
                            }
                        )

                # ======================================================================
                # STEP8: Generating response for feedback intent
                # ======================================================================
                print("STEP8: Generating response for feedback intent")

                final_reply = llm_call_with_images(
                    custom_prompt=feedback_reply_prompt,
                    context=passing_context,
                )

                # ======================================================================
                # STEP9: Saving the generated message in the DB
                # ======================================================================
                print("STEP9: Saving the generated message in the DB")
                added_message = await add_image_message(
                    conversation_id=conversation_id,
                    role="ai",
                    text=final_reply,
                    image_ids=[],
                )

                # ======================================================================
                # STEP10: Updating the pooling doc along with the response
                # ======================================================================
                print("STEP10: Updating the pooling doc along with the response")
                await update_pooling_status(
                    pooling_id=pooling_id,
                    status="completed",
                    data={
                        "iteration_result": {
                            "text": final_reply,
                            "role": "ai",
                            "images": [],
                            "message_id": str(added_message.message_id),
                        },
                        "status": "success",
                    },
                )

            elif intent == "edit":
                # ======================================================================
                # STEP6: Checking which message image or messages image needs edit on
                # ======================================================================
                print(
                    "STEP6: Checking which message image or messages image needs edit on"
                )
                message_id_string = llm_call_without_images(
                    custom_prompt=edit_reference_prompt,
                    context=f"Conversation history:\n{context} \n\nCurrent message:\n{message}",
                )

                # ======================================================================
                # STEP7: Getting image_url from the message_id
                # ======================================================================
                print("STEP7: Getting image_url from the message_id")
                message_doc = await get_message_by_message_id(
                    message_id=message_id_string
                )
                image_ids = message_doc.image_ids
                image_doc = await get_image_by_image_id(image_id=image_ids[0])
                image_url = R2Storage.get_user_generated_images(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    file_name=image_doc.image_name,
                )

                # ======================================================================
                # STEP8: Generating the new enhanced and softened prompt for image edit
                # ======================================================================
                print(
                    "STEP8: Generating the new enhanced and softened prompt for image edit"
                )
                enhanced_prompt = llm_call_without_images(
                    custom_prompt=edit_softener_prompt,
                    context=f"User's edit request: {message} \n\n Prev Messaages: {context}",
                )

                prompt = f"""
                    IMAGE REFERENCES:
                    The image is the identity and composition reference for the subject.

                    TASK:
                    {enhanced_prompt}

                    GARMENT PRESERVATION RULES:
                    Use each garment reference only for its corresponding garment.
                    Preserve exactly:
                    - colors
                    - fabric
                    - texture
                    - embroidery
                    - prints
                    - stitching
                    - borders
                    - trims
                    - embellishments
                    - logos
                    - patterns
                    Do not redesign, simplify, replace, merge, or invent any garment.

                    FIT & DRAPING:
                    Resize and naturally fit the supplied garments to the model's body while preserving their design.
                    Only adjust:
                    - scale
                    - draping
                    - folding
                    - natural fabric deformation
                    Do not alter the garment construction.

                    IDENTITY PRESERVATION:
                    The first image defines the subject.
                    Preserve exactly:
                    - face
                    - hairstyle
                    - body proportions
                    - pose
                    - camera angle
                    - framing
                    - crop
                    - perspective
                    - lighting
                    - background
                    Maintain the identity and composition from Image 1. Render the subject naturally wearing the supplied outfit.

                    SAFETY:
                    The subject should appear naturally and completely dressed in the finished outfit.                
                """.strip()

                # ======================================================================
                # STEP9: Generate the new Iteration Image
                # ======================================================================
                print("STEP9: Generating the new Iteration Image for this Conversation")
                image_64_bytes = generate_image(
                    model="gpt-image-1.5",
                    prompt=prompt,
                    image_urls=[image_url],
                    user_id=user_id,
                )

                # ======================================================================
                # STEP10: Upload the new Iteration Image
                # ======================================================================
                print(
                    "STEP10: Uploading the new Iteration Up Image for this Conversation on R2"
                )
                file_name = f"iteration_{str(PydanticObjectId())}.webp"
                response = R2Storage.upload_generated_see_on_image(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    file_name=file_name,
                    b64_image=image_64_bytes,
                )

                # ======================================================================
                # STEP11: Calling OpenAI again to generate a contextual reply
                # ======================================================================
                print("STEP11: Calling OpenAI again to generate a contextual reply")
                edit_final_reply_context = [
                    {
                        "type": "input_text",
                        "text": f"User's original request: {message}\n\nHere is the updated image after the edit:",
                    },
                    {
                        "type": "input_image",
                        "image_url": response["url"],
                    },
                ]
                final_reply = llm_call_with_images(
                    custom_prompt=edit_feedback_reply_prompt,
                    context=edit_final_reply_context,
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
                    image_name=file_name,
                )

                added_message = await add_image_message(
                    conversation_id=conversation_id,
                    role="ai",
                    text=final_reply,
                    image_ids=[str(image_doc.image_id)],
                )

                # ======================================================================
                # STEP13: Updating the pooling doc along with the response
                # ======================================================================
                print("STEP13: Updating the pooling doc along with the response")
                await update_pooling_status(
                    pooling_id=pooling_id,
                    status="completed",
                    data={
                        "iteration_result": {
                            "text": final_reply,
                            "role": "ai",
                            "images": [response["url"]],
                            "message_id": str(added_message.message_id),
                        },
                        "status": "success",
                    },
                )

        except Exception as e:
            print("Unexpected worker error in visualization_iteration as: ", e)
            await update_pooling_status(
                pooling_id=pooling_id,
                status="failed",
                data={"error": str(e)},
            )

    return run_async(main_async_logic())
