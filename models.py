"""
LLM Model Wrappers
Supports: OpenAI (GPT-4o), Anthropic (Claude), Google (Gemini)
"""

import os


def get_openai_response(prompt: str, model: str = "gpt-4o") -> str:
    """Query OpenAI API."""
    from openai import OpenAI

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1024,
    )

    return response.choices[0].message.content.strip()


def get_anthropic_response(prompt: str, model: str = "claude-sonnet-4-6") -> str:
    """Query Anthropic API."""
    from anthropic import Anthropic

    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    message = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text.strip()


def get_gemini_response(prompt: str, model: str = "gemini-2.5-flash") -> str:
    """Query Google Gemini API."""
    from google import genai

    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    return response.text.strip()


# Registry of available models
MODEL_REGISTRY = {
    "OpenAI (GPT-4o)": {
        "fn": get_openai_response,
        "default_model": "gpt-4o",
    },
    "Anthropic (Claude)": {
        "fn": get_anthropic_response,
        "default_model": "claude-sonnet-4-6",
    },
    "Google (Gemini)": {
        "fn": get_gemini_response,
        "default_model": "gemini-2.5-flash",
    },
}


def query_model(provider: str, prompt: str) -> str:
    """Unified interface to query any model."""
    if provider not in MODEL_REGISTRY:
        return f"Error: Unknown provider '{provider}'. Available: {list(MODEL_REGISTRY.keys())}"

    try:
        result = MODEL_REGISTRY[provider]["fn"](prompt)
        return result
    except Exception as e:
        return f"Error ({provider}): {type(e).__name__}: {e}"
