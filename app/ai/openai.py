from openai import OpenAI
import requests

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
