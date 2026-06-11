"""Text-to-speech using Microsoft Edge neural voices (free, high quality)."""

import re

import edge_tts

from jarvis import config


def _strip_markdown(text: str) -> str:
    """Remove markdown noise so the spoken output sounds natural."""
    text = re.sub(r"```.*?```", " I've put the code on screen. ", text, flags=re.DOTALL)
    text = re.sub(r"[*_#`>|]", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # links -> anchor text
    return re.sub(r"\s+", " ", text).strip()


async def synthesize(text: str) -> bytes:
    """Convert text to MP3 audio bytes."""
    speakable = _strip_markdown(text)
    if not speakable:
        return b""
    communicate = edge_tts.Communicate(speakable, config.TTS_VOICE)
    chunks = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])
    return b"".join(chunks)
