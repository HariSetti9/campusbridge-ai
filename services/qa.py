import json

from prompts.qa_prompt import QA_SYSTEM_PROMPT, QA_USER_TEMPLATE
from services.ai_service import chat_completion


def ask_about_notice(notice_text: str, opportunity: dict, question: str) -> str:
    user_prompt = QA_USER_TEMPLATE.format(
        notice_text=notice_text,
        opportunity_json=json.dumps(opportunity, indent=2),
        question=question,
    )
    return chat_completion(QA_SYSTEM_PROMPT, user_prompt, max_tokens=600)
