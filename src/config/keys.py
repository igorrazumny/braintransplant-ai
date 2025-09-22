# Project: braintransplant-ai — File: src/config/keys.py
"""
Public, non-secret constants for Gemini model identifiers and env var names.
Keep secrets only in the environment (e.g., GEMINI_STUDIO_API_KEY).
"""

# ---- Canonical Gemini model identifiers (match provider’s API model ids exactly)
GEMINI_1_5_PRO   = "gemini-1.5-pro"
GEMINI_1_5_FLASH = "gemini-1.5-flash"

# ---- Environment variable names (secrets live in .env / Cloud Run)
ENV_GEMINI_STUDIO_API_KEY = "GEMINI_STUDIO_API_KEY"   # required for Gemini 1.5 API mode
