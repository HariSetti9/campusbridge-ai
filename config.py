"""
Centralized configuration for CampusBridge AI.
Never hardcode the model name or API key elsewhere — import from here.
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed — fine in deployed environments using st.secrets

import streamlit as st


def _get_secret(key: str, default: str = "") -> str:
    """Check st.secrets first (for Streamlit Cloud), fall back to env vars (for local)."""
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)


FEATHERLESS_API_KEY = _get_secret("FEATHERLESS_API_KEY", "")
FEATHERLESS_BASE_URL = "https://api.featherless.ai/v1"
FEATHERLESS_MODEL = _get_secret("FEATHERLESS_MODEL", "deepseek-ai/DeepSeek-V3.2")

APP_NAME = "CampusBridge AI"
APP_TAGLINE = "Opportunities should have no language barrier."

SUPPORTED_LANGUAGES = ["English", "Telugu", "Hindi", "Gujarati", "Tamil"]

DB_PATH = "campusbridge.db"

MIN_NOTICE_LENGTH = 30  # characters — below this we reject as "too short to analyze"
MAX_NOTICE_LENGTH = 12000  # characters — safety cap so we don't send huge prompts
