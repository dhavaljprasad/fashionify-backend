from openai import OpenAI
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
            output_format="webp",  # use "webp", not "image/webp"
            output_compression=80,
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
