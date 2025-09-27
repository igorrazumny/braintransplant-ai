import os
import requests
from typing import List, Dict, Any

import vertexai
from vertexai.generative_models import GenerativeModel

from utils.logger import get_logger

from config.keys import (
    GEMINI_1_5_PRO,
    GEMINI_2_5_PRO,  # Add this import
    ENV_GEMINI_STUDIO_API_KEY,
)

MAX_OUTPUT_TOKENS = 65536  # explicit constant
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

def call_llm(system_prompt: str, user_query: str, timeout_s: int = 30) -> str:
    logger = get_logger("btai.llm.adapter")
    provider = _req("LLM_PROVIDER").strip().lower()
    if provider != "gemini":
        raise RuntimeError(f"Unsupported LLM_PROVIDER='{provider}'.")

    model_id = _req("LLM_MODEL").strip()

    logger.info(f"Using model_id: {model_id}...")

    if model_id not in SUPPORTED_MODELS:
        raise RuntimeError(f"Unsupported LLM_MODEL='{model_id}'. Supported models: {', '.join(SUPPORTED_MODELS)}")

    if model_id == GEMINI_2_5_PRO:
        logger.info("Using Vertex AI to call the model.")
        
        project_id = os.getenv("GCP_PROJECT_ID", "fresh-myth-471317-j9")
        location = "europe-west4"
        
        vertexai.init(project=project_id, location=location)

        model = GenerativeModel(
            model_name=model_id,
            system_instruction=system_prompt,
        )
        response = model.generate_content(
            contents=[{"role": "user", "parts": [{"text": user_query}]}],
            generation_config={
                "temperature": 0,
                "max_output_tokens": MAX_OUTPUT_TOKENS,
            },
        )
        logger.info(f"Vertex AI response: {str(response)[:200]}")
        return response.text

    # Fallback to REST API for other supported models
    logger.info("Using Gemini API (REST) to call the model.")
    api_key = _req(ENV_GEMINI_STUDIO_API_KEY)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}"

    logger.info(f"Calling Gemini API with url: {url}...")

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
    data = r.json()

    logger.info(f"Gemini API response: {str(data)[:100]}")

    if "error" in data:
        error_msg = data["error"].get("message", "Unknown error")
        raise RuntimeError(f"Gemini API error: {error_msg}")

    return _extract_text(data)
