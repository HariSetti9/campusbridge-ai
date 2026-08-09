import json

from prompts.translation_prompt import TRANSLATION_SYSTEM_PROMPT, TRANSLATION_USER_TEMPLATE
from services.ai_service import chat_completion


def explain_in_language(opportunity: dict, language: str, simple_english: bool = False) -> str:
    user_prompt = TRANSLATION_USER_TEMPLATE.format(
        opportunity_json=json.dumps(opportunity, indent=2),
        language=language,
        simple_english=simple_english,
    )
    return chat_completion(TRANSLATION_SYSTEM_PROMPT, user_prompt, max_tokens=1200)
