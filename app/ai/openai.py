from openai import OpenAI
from typing import List, Dict, Optional, Any
import requests
import json

client = OpenAI()


def generate_image(
    model: str = "gpt-image-1.5",
    prompt: str = "",
    image_urls: list[str] | None = None,
    user_id: str = "",
):
    try:
        image_urls = image_urls or []
        image_files = []

        for idx, url in enumerate(image_urls):
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Explicitly specify filename, raw bytes, and MIME type
            image_files.append(
                (
                    f"reference_{idx}.webp",
                    response.content,
                    "image/webp",
                )
            )

        result = client.images.edit(
            model=model,
            image=image_files,
            prompt=prompt,
            output_format="webp",
            output_compression=90,
            quality="low",
            size="1024x1536",
            input_fidelity="low",
            user=user_id,
        )

        return result.data[0].b64_json

    except Exception as e:
        print("Unexpected error occured calling generate image function as", e)
        return None


def tool_call(
    tools: list, custom_prompt: str, context: str, model: str = "gpt-4.1-mini"
):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": custom_prompt},
                {"role": "user", "content": context},
            ],
            tools=tools,
            tool_choice="required",
        )

        message = response.choices[0].message
        tool_call = message.tool_calls[0]

        return json.loads(tool_call.function.arguments)

    except Exception as e:
        print(f"Unexpected error occured in tools_call as {e}")
        return None


def llm_call_without_images(
    custom_prompt: str,
    context: str,
    model: str = "gpt-4.1-mini",
    temp: float = 0.7,
):
    try:
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": custom_prompt,
                },
                {
                    "role": "user",
                    "content": context,
                },
            ],
            temperature=temp,
        )

        return response.output_text

    except Exception as e:
        print(f"Unexpected error occurred in ai function llm_call_without_images: {e}")
        return None


def llm_call_with_images(
    custom_prompt: str,
    context: list,
    model: str = "gpt-4.1-mini",
    temp: float = 0.7,
):
    try:
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": custom_prompt,
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": context,
                },
            ],
            temperature=temp,
        )

        return response.output_text
    except Exception as e:
        print(f"Unexpected error occurred in ai function llm_call_with_images: {e}")
        return None


def llm_call_with_attachments_json(
    system_prompt: str,
    content: List[Dict[str, Any]],
    json_schema: Optional[Dict[str, Any]] = None,
    model: str = "gpt-5-mini",
):
    """
    Generic multimodal LLM call.

    Parameters
    ----------
    system_prompt : str
        System instructions.

    content : list
        User content for Responses API.

        Example:
        [
            {
                "type": "input_text",
                "text": "Extract the PAN number."
            },
            {
                "type": "input_image",
                "image_url": "https://example.com/image.jpg"
            }
        ]

    json_schema : dict | None
        JSON Schema for structured output.
        If None, plain text is returned.

    model : str
        OpenAI model.

    temperature : float
        Sampling temperature.

    Returns
    -------
    dict | str | None
    """

    try:
        request = {
            "model": model,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": system_prompt,
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": content,
                },
            ],
        }

        if json_schema:
            request["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": json_schema["name"],
                    "schema": json_schema["schema"],
                    "strict": True,
                }
            }

        response = client.responses.create(**request)

        if json_schema:
            return json.loads(response.output_text)

        return response.output_text

    except Exception as e:
        print(f"Unexpected error in llm_call_with_attachments_json: {e}")
        return None
