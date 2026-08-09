"""
Thin wrapper around the Featherless (OpenAI-compatible) chat completions API.
Centralizes error handling so the rest of the app never has to deal with
raw exceptions from the AI call.
"""

from openai import OpenAI, APIError, APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError

from config import FEATHERLESS_API_KEY, FEATHERLESS_BASE_URL, FEATHERLESS_MODEL


class AIServiceError(Exception):
    """Raised with a user-friendly message — safe to display directly in the UI."""
    pass


def _client() -> OpenAI:
    if not FEATHERLESS_API_KEY:
        raise AIServiceError(
            "No Featherless API key configured. Set FEATHERLESS_API_KEY in your "
            ".env file (local) or in Streamlit secrets (deployed)."
        )
    return OpenAI(base_url=FEATHERLESS_BASE_URL, api_key=FEATHERLESS_API_KEY)


def chat_completion(system_prompt: str, user_prompt: str, max_tokens: int = 1500,
                     temperature: float = 0.3) -> str:
    """Call Featherless chat completions and return the raw text response.
    Raises AIServiceError with a friendly message on any failure — callers
    should catch this and show it directly, never a raw traceback."""
    client = _client()
    try:
        response = client.chat.completions.create(
            model=FEATHERLESS_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except AuthenticationError:
        raise AIServiceError(
            "Authentication failed (401). Check that your Featherless API key "
            "is correct and hasn't expired."
        )
    except RateLimitError:
        raise AIServiceError(
            "Featherless rate limit or capacity reached (429). Please wait a "
            "moment and try again."
        )
    except APITimeoutError:
        raise AIServiceError(
            "The request timed out. The model may be cold — please try again."
        )
    except APIConnectionError:
        raise AIServiceError(
            "Couldn't connect to Featherless. Check your internet connection "
            "and try again."
        )
    except APIError as e:
        status = getattr(e, "status_code", None)
        if status == 403:
            raise AIServiceError(
                "This model is gated (403). Visit the model's page on "
                "featherless.ai, click 'Unlock Model', and agree to its terms."
            )
        if status == 500:
            raise AIServiceError(
                "Featherless had an internal error (500) processing this "
                "request. Please try again."
            )
        if status == 503:
            raise AIServiceError(
                "The model is temporarily unavailable or cold (503). Please "
                "retry — if this persists, try again in a minute."
            )
        raise AIServiceError(f"CampusBridge couldn't reach the AI service ({e}).")
    except Exception as e:
        raise AIServiceError(f"Unexpected error calling the AI service: {e}")

    if not response.choices:
        raise AIServiceError("The AI service returned an empty response. Please try again.")

    text = response.choices[0].message.content
    if not text:
        # Some models put output in reasoning_content instead of content
        text = getattr(response.choices[0].message, "reasoning_content", None)
    if not text:
        raise AIServiceError(
            "The AI returned no visible text. This can happen with a cold "
            "model — please try again."
        )
    return text
