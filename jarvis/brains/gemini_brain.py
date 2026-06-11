"""Gemini brain — cloud workhorse for routine delegated tasks."""

from google import genai

from jarvis import config

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not config.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set")
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


def ask_gemini(prompt: str, system: str | None = None) -> str:
    """Run a single prompt against Gemini and return plain text."""
    client = _get_client()
    contents = prompt if system is None else f"{system}\n\n{prompt}"
    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=contents,
    )
    return response.text or ""
