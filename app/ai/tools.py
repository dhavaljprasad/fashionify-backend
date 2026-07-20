intent_tool = {
    "type": "function",
    "function": {
        "name": "classify_intent",
        "description": (
            "Classify the user's current message in an ongoing fashion visualization "
            "conversation into one of three intents: 'feedback', 'edit', or 'irrelevant'. "
            "Use the full conversation history for context, since the current message alone "
            "may be ambiguous (e.g. 'make it purple' or 'which one looks better')."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": ["feedback", "edit", "irrelevant"],
                    "description": (
                        "feedback: user is asking for an opinion, comparison, or styling "
                        "advice about existing generated image(s) (e.g. 'what do you think?', "
                        "'which looks better?', 'would purple suit me better?'). "
                        "edit: user wants an existing generated image to be modified/regenerated "
                        "with a change (e.g. 'add a golden border', 'make the sleeves longer'). "
                        "irrelevant: message is unrelated to the fashion visualization/styling "
                        "context, or inappropriate (e.g. general knowledge questions, small talk "
                        "unrelated to the outfit, inappropriate/explicit requests)."
                    ),
                },
                "reasoning": {
                    "type": "string",
                    "description": (
                        "One short sentence explaining why this intent was chosen, based on the "
                        "current message and relevant history. Used for internal logging/debugging."
                    ),
                },
            },
            "required": ["intent", "reasoning"],
            "additionalProperties": False,
        },
    },
}
