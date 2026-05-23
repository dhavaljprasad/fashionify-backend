from google import genai
from google.genai import types
from pydantic import BaseModel
import httpx

client = genai.Client()


def call_gemini_llm(
    model: str = "gemini-3.1-flash-lite-preview",
    custom_prompt: str = "",
    temps: float = 0.7,
    image_url: str = None,
    output_format: str = "text",
    output_schema: BaseModel = None,
):
    try:
        if not custom_prompt:
            return None

        # Build the configuration using the new types.GenerateContentConfig
        config_args = {"temperature": temps, "response_mime_type": "text/plain"}

        # Properly map the JSON output format AND the Pydantic schema
        if output_format == "json" and output_schema:
            config_args["response_mime_type"] = "application/json"
            config_args["response_schema"] = output_schema

        config = types.GenerateContentConfig(**config_args)

        # Build the prompt parts
        prompt_parts = []

        # If an image URL is provided, fetch it and append as a Part
        if image_url:
            # Fetch the image bytes from the internet
            image_data = httpx.get(image_url).content
            prompt_parts.append(
                types.Part.from_bytes(
                    data=image_data,
                    mime_type="image/webp",  # Change if expecting png/webp etc.
                )
            )

        # Append the text prompt (SDK natively handles simple strings)
        prompt_parts.append(custom_prompt)

        # Call the Gemini LLM with the properly constructed list and config
        response = client.models.generate_content(
            model=model,
            contents=prompt_parts,
            config=config,
        )

        if output_format == "text":
            return response.text
        else:
            return response.parsed.model_dump()

    except Exception as e:
        print("Unexpected error occurred calling gemini llm as:", e)
        return None
