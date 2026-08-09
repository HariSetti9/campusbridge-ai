from prompts.analyzer_prompt import ANALYZER_SYSTEM_PROMPT, ANALYZER_USER_TEMPLATE
from services.ai_service import chat_completion
from utils.parsers import safe_json_parse

REQUIRED_FIELDS = [
    "title", "organization", "opportunity_type", "summary", "eligibility",
    "deadline", "location", "mode", "cost", "prize_or_benefits",
    "required_documents", "skills_or_requirements", "submission_requirements",
    "important_dates", "next_actions", "warnings", "missing_information",
]


def _fill_missing_fields(data: dict) -> dict:
    """Guarantee every expected key exists so the UI never KeyErrors on a
    slightly-incomplete AI response."""
    for field in REQUIRED_FIELDS:
        if field not in data:
            data[field] = [] if field in (
                "eligibility", "prize_or_benefits", "required_documents",
                "skills_or_requirements", "submission_requirements",
                "important_dates", "next_actions", "warnings", "missing_information",
            ) else "Not specified"
    return data


def analyze_notice(notice_text: str) -> dict:
    """Returns a structured opportunity dict. Raises AIServiceError or
    ParseError on failure — caller should catch and show a friendly message."""
    user_prompt = ANALYZER_USER_TEMPLATE.format(notice_text=notice_text)
    raw = chat_completion(ANALYZER_SYSTEM_PROMPT, user_prompt, max_tokens=1800)
    data = safe_json_parse(raw)
    return _fill_missing_fields(data)
