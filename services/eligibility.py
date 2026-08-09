import json

from prompts.eligibility_prompt import (
    ELIGIBILITY_SYSTEM_PROMPT, ELIGIBILITY_USER_TEMPLATE,
    FIT_SYSTEM_PROMPT, FIT_USER_TEMPLATE,
)
from services.ai_service import chat_completion
from utils.parsers import safe_json_parse


def check_eligibility(opportunity: dict, profile: dict) -> dict:
    user_prompt = ELIGIBILITY_USER_TEMPLATE.format(
        opportunity_json=json.dumps(opportunity, indent=2),
        profile_json=json.dumps(profile, indent=2),
    )
    raw = chat_completion(ELIGIBILITY_SYSTEM_PROMPT, user_prompt, max_tokens=1200)
    data = safe_json_parse(raw)

    data.setdefault("verdict", "UNCERTAIN")
    data.setdefault("confidence", "Low")
    data.setdefault("requirements", [])
    data.setdefault("missing_information", [])
    data.setdefault("recommended_action", "Review the original notice for full details.")
    return data


def estimate_fit(opportunity: dict, profile: dict, eligibility_result: dict) -> dict:
    """Qualitative Strong/Moderate/Weak fit estimate — not an acceptance probability."""
    user_prompt = FIT_USER_TEMPLATE.format(
        opportunity_json=json.dumps(opportunity, indent=2),
        profile_json=json.dumps(profile, indent=2),
        eligibility_json=json.dumps(eligibility_result, indent=2),
    )
    raw = chat_completion(FIT_SYSTEM_PROMPT, user_prompt, max_tokens=500)
    data = safe_json_parse(raw)

    data.setdefault("overall_fit", "Moderate Fit")
    data.setdefault("eligibility_match", "Moderate")
    data.setdefault("skills_match", "Moderate")
    data.setdefault("experience_alignment", "Moderate")
    data.setdefault("readiness", "Moderate")
    data.setdefault("recommendation", "Review the opportunity details before deciding.")
    return data
