"""Safe JSON parsing for LLM output — handles fenced code blocks and minor
formatting issues without repeatedly calling the AI to "fix itself"."""

import json
import re


class ParseError(Exception):
    pass


def strip_code_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrappers if present."""
    text = text.strip()
    fence_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    return text


def extract_json_object(text: str) -> str:
    """If there's extra text around the JSON object, extract the outermost {...}."""
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return text


def safe_json_parse(text: str) -> dict:
    """Best-effort parse of LLM JSON output. Raises ParseError with a clear
    message if it truly can't be salvaged — caller should show a friendly
    error rather than crash."""
    cleaned = strip_code_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # One fallback attempt: extract the outermost JSON object and retry
    candidate = extract_json_object(cleaned)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        raise ParseError(
            f"CampusBridge couldn't parse the AI's response as valid JSON. ({e})"
        )
