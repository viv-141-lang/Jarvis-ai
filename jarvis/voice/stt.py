"""Speech-to-text using faster-whisper, fully local."""

import io

from jarvis import config

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        _model = WhisperModel(config.WHISPER_MODEL_SIZE, device="auto", compute_type="auto")
    return _model


def transcribe(audio_bytes: bytes) -> str:
    """Transcribe an audio file (wav/webm/ogg bytes) to text."""
    segments, _info = _get_model().transcribe(io.BytesIO(audio_bytes), beam_size=5)
    return " ".join(seg.text.strip() for seg in segments).strip()
