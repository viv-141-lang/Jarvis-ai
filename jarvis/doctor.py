"""Jarvis setup checker — run `python -m jarvis.doctor` after editing .env.

Verifies every integration and prints exactly what is missing or broken.
"""

import sys

from jarvis import config

OK = "[ OK ]"
FAIL = "[FAIL]"
WARN = "[WARN]"
SKIP = "[SKIP]"


def check_anthropic() -> bool:
    if not config.ANTHROPIC_API_KEY:
        print(f"{FAIL} Anthropic: ANTHROPIC_API_KEY not set (required — Claude is the Main Brain)")
        return False
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        client.models.retrieve(config.CLAUDE_MODEL)
        print(f"{OK} Anthropic: key valid, model '{config.CLAUDE_MODEL}' available")
        return True
    except Exception as exc:
        print(f"{FAIL} Anthropic: {exc}")
        return False


def check_gemini() -> bool:
    if not config.GEMINI_API_KEY:
        print(f"{WARN} Gemini: GEMINI_API_KEY not set — delegation to Gemini will fail")
        return False
    try:
        from jarvis.brains.gemini_brain import ask_gemini

        ask_gemini("Reply with the single word: ok")
        print(f"{OK} Gemini: key valid, model '{config.GEMINI_MODEL}' responding")
        return True
    except Exception as exc:
        print(f"{FAIL} Gemini ({config.GEMINI_MODEL}): {exc}")
        print("       Tip: if this is a quota/model error, set GEMINI_MODEL=gemini-2.5-flash in .env")
        return False


def check_ollama() -> bool:
    from jarvis.brains.ollama_brain import is_available

    if is_available():
        print(f"{OK} Ollama: server reachable at {config.OLLAMA_HOST} (model: {config.OLLAMA_MODEL})")
        return True
    print(f"{WARN} Ollama: not reachable at {config.OLLAMA_HOST} — start it with `ollama serve` "
          f"and `ollama pull {config.OLLAMA_MODEL}`. Jarvis will fall back to Gemini.")
    return False


def check_google_search() -> bool:
    if not config.GOOGLE_SEARCH_API_KEY or not config.GOOGLE_SEARCH_CX:
        print(f"{WARN} Google Search: GOOGLE_SEARCH_API_KEY / GOOGLE_SEARCH_CX not set — "
              "live news will be unavailable")
        return False
    from jarvis.tools.google_search import google_search

    result = google_search("test", 1)
    if result.startswith("Error"):
        print(f"{FAIL} Google Search: {result}")
        return False
    print(f"{OK} Google Search: working")
    return True


def check_trading() -> bool:
    if not config.KITE_API_KEY or not config.KITE_ACCESS_TOKEN:
        print(f"{SKIP} Zerodha: KITE_API_KEY / KITE_ACCESS_TOKEN not set — only needed for live execution")
        return True
    if not config.TRADINGVIEW_WEBHOOK_SECRET:
        print(f"{FAIL} Zerodha: keys set but TRADINGVIEW_WEBHOOK_SECRET is empty — "
              "the webhook listener rejects everything without it")
        return False
    mode = "DRY RUN (safe)" if config.DRY_RUN else "LIVE ORDERS ENABLED"
    print(f"{OK} Zerodha: configured — mode: {mode}")
    if not config.DRY_RUN:
        print(f"{WARN} DRY_RUN is false: the executor WILL place real orders on Zerodha.")
    return True


def main() -> int:
    print("Jarvis doctor — checking configuration\n")
    core_ok = check_anthropic()
    check_gemini()
    check_ollama()
    check_google_search()
    check_trading()
    print()
    if core_ok:
        print("Core is ready. Launch the UI with:  chainlit run app.py -w")
        return 0
    print("Fix the [FAIL] items above (at minimum ANTHROPIC_API_KEY), then re-run.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
