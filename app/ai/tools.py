intent_tool = {
    "type": "function",
    "function": {
        "name": "classify_intent",
        "description": (
            "Classify the user's current message in an ongoing fashion visualization "
            "conversation into one of three intents: 'feedback', 'edit', or 'irrelevant'. "
            "Use the full conversation history for context, since the current message alone "
            "may be ambiguous (e.g. 'make it purple' vs 'what if it was purple, how would "
            "that look?' — these are DIFFERENT intents despite both mentioning purple)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": ["feedback", "edit", "irrelevant"],
                    "description": (
                        "feedback: user is asking for an opinion, comparison, or styling "
                        "advice — including HYPOTHETICAL or conditional questions about a "
                        "possible change, WITHOUT explicitly instructing the change to be "
                        "made. Key signal words: 'what if', 'how would it look', 'do you "
                        "think', 'would X suit me better', 'which looks better'. "
                        "Examples: 'what do you think?', 'which looks better?', 'would "
                        "purple suit me better?', 'what if I go with a baby pink blouse "
                        "instead of cream, how will that look?' — all of these are "
                        "feedback, NOT edit, because the user is exploring an idea or "
                        "asking an opinion, not instructing an actual change yet.\n\n"
                        "edit: user is EXPLICITLY instructing an existing generated image "
                        "to be modified/regenerated with a change. This requires clear "
                        "imperative/action language, not a question about a hypothetical. "
                        "Examples: 'add a golden border', 'make the sleeves longer', "
                        "'change it to baby pink', 'go ahead and make it purple', 'yes do "
                        "that', 'generate it with the pink blouse'. Also applies when the "
                        "user explicitly confirms/approves a previously discussed "
                        "hypothetical from earlier in the conversation (e.g. after being "
                        "told feedback on 'what if it was pink', user says 'okay do that' "
                        "or 'yes generate that') — treat this as edit, using the earlier "
                        "message for what the actual change should be.\n\n"
                        "irrelevant: message is unrelated to the fashion visualization/styling "
                        "context, or inappropriate (e.g. general knowledge questions, small talk "
                        "unrelated to the outfit, inappropriate/explicit requests)."
                    ),
                },
                "reasoning": {
                    "type": "string",
                    "description": (
                        "One short sentence explaining why this intent was chosen, based on the "
                        "current message and relevant history — explicitly note if the message "
                        "was hypothetical/questioning (→ feedback) vs a direct instruction "
                        "(→ edit). Used for internal logging/debugging."
                    ),
                },
            },
            "required": ["intent", "reasoning"],
            "additionalProperties": False,
        },
    },
}
