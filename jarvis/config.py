"""Central configuration for Jarvis, loaded from environment / .env file."""

import os

from dotenv import load_dotenv

load_dotenv()

# --- AI brains ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-8")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# --- Google Programmable Search (live news) ---
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "")
GOOGLE_SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX", "")  # Programmable Search Engine ID

# --- Voice ---
TTS_VOICE = os.getenv("TTS_VOICE", "en-US-GuyNeural")  # edge-tts voice
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")

# --- Zerodha / TradingView execution ---
KITE_API_KEY = os.getenv("KITE_API_KEY", "")
KITE_ACCESS_TOKEN = os.getenv("KITE_ACCESS_TOKEN", "")
TRADINGVIEW_WEBHOOK_SECRET = os.getenv("TRADINGVIEW_WEBHOOK_SECRET", "")

# Safety rails for live execution
DRY_RUN = os.getenv("DRY_RUN", "true").lower() != "false"  # paper mode unless explicitly disabled
MAX_ORDER_QUANTITY = int(os.getenv("MAX_ORDER_QUANTITY", "50"))
MAX_ORDERS_PER_DAY = int(os.getenv("MAX_ORDERS_PER_DAY", "20"))
ALLOWED_SYMBOLS = [
    s.strip().upper() for s in os.getenv("ALLOWED_SYMBOLS", "").split(",") if s.strip()
]
