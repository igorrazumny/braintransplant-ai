# Project: braintransplant-ai | File: src/llm/adapter.py

import os
import requests
from typing import List, Dict, Any

from config.keys import (
    GEMINI_1_5_PRO,
    GEMINI_2_5_PRO,  # Add this import
    ENV_GEMINI_STUDIO_API_KEY,
)

"""
Strict Gemini-only adapter (API mode).
- Supported provider: 'gemini' only.
- Supported models: 'gemini-1.5-pro' and 'gemini-2.5-pro'.
- No silent defaults; all requirements validated.

Required environment:
- LLM_PROVIDER=gemini
- LLM_MODEL=gemini-1.5-pro OR gemini-2.5-pro
- GEMINI_STUDIO_API_KEY=<your key>

Behavior:
- Sends a single turn with a system prompt and a user query via Google Generative Language REST API.
- Temperature fixed at 0 for deterministic output.
- timeout_s must be provided by the caller (seconds).
"""

MAX_OUTPUT_TOKENS = 1000000  # explicit constant
SUPPORTED_MODELS = [GEMINI_1_5_PRO, GEMINI_2_5_PRO]  # Add this list


def _req(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _extract_text(resp_json: Dict[str, Any]) -> str:
    candidates = resp_json.get("candidates", [])
    if not candidates:
        return ""
    parts: List[Dict[str, Any]] = candidates[0].get("content", {}).get("parts", [])
    texts = []
    for p in parts:
        t = p.get("text", "")
        if t:
            texts.append(t)
    return "\n".join(texts).strip()


def call_llm(system_prompt: str, user_query: str, timeout_s: int) -> str:
    provider = _req("LLM_PROVIDER").strip().lower()
    if provider != "gemini":
        raise RuntimeError(f"Unsupported LLM_PROVIDER='{provider}'. Only 'gemini' is allowed in braintransplant-ai.")

    model_id = _req("LLM_MODEL").strip()
    if model_id not in SUPPORTED_MODELS:  # Update this check
        raise RuntimeError(f"Unsupported LLM_MODEL='{model_id}'. Supported models: {', '.join(SUPPORTED_MODELS)}")

    api_key = _req(ENV_GEMINI_STUDIO_API_KEY)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}"
    payload = {
        "systemInstruction": {
            "role": "system",
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_query}]
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": MAX_OUTPUT_TOKENS
        }
    }

    r = requests.post(url, json=payload, timeout=timeout_s)
    r.raise_for_status()
    return _extract_text(r.json())
