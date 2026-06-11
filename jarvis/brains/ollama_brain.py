"""Ollama brain — free local model for simple delegated tasks."""

import ollama

from jarvis import config

_client: ollama.Client | None = None


def _get_client() -> ollama.Client:
    global _client
    if _client is None:
        _client = ollama.Client(host=config.OLLAMA_HOST)
    return _client


def ask_ollama(prompt: str, system: str | None = None) -> str:
    """Run a single prompt against the local Ollama model and return plain text."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = _get_client().chat(model=config.OLLAMA_MODEL, messages=messages)
    return response["message"]["content"]


def is_available() -> bool:
    """True if the local Ollama server is reachable."""
    try:
        _get_client().list()
        return True
    except Exception:
        return False
