from google import genai

client = genai.Client()

def call_gemini_llm(
    model: str = "gemini-3.1-flash-lite-preview",
    prompt: str = "",
    temps: float = 0.7,
    structured_json: bool = False,
):
    try:
        if not prompt:
            return None
        
        generation_config = {
            "temperature": temps,
        }
        
        if structured_json:
            generation_config["response_mime_type"] = "application/json"
        
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=genai.GenerateContentConfig(**generation_config),
        )
        
        return response.text
    except Exception as e:
        print("Unexpected error occured calling gemini llm as:", e)
        return None