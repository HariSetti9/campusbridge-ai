from config import MIN_NOTICE_LENGTH, MAX_NOTICE_LENGTH


def validate_notice_text(text: str) -> str | None:
    """Returns an error message string if invalid, or None if valid."""
    if not text or not text.strip():
        return "Please paste an opportunity notice before analyzing."
    stripped = text.strip()
    if len(stripped) < MIN_NOTICE_LENGTH:
        return f"This notice looks too short to analyze (minimum {MIN_NOTICE_LENGTH} characters)."
    if len(stripped) > MAX_NOTICE_LENGTH:
        return f"This notice is very long — please trim it to under {MAX_NOTICE_LENGTH} characters."
    return None


def validate_question(text: str) -> str | None:
    if not text or not text.strip():
        return "Please enter a question."
    if len(text.strip()) < 3:
        return "Please enter a more complete question."
    return None
