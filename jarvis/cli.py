"""Text-mode Jarvis for the terminal — run `python -m jarvis.cli`.

Same Claude-orchestrated multi-model brain as the Chainlit UI, without
voice. Useful for quick tests and low-overhead sessions.
"""

import sys

from jarvis.router import ask_jarvis

BANNER = """\
J.A.R.V.I.S. terminal mode — type your request, 'exit' to quit.
(Trading pipeline, Gemini/Ollama delegation and Google news all work here.)
"""


def main() -> int:
    print(BANNER)
    history: list[dict] = []
    while True:
        try:
            user_text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not user_text:
            continue
        if user_text.lower() in {"exit", "quit"}:
            return 0

        history.append({"role": "user", "content": user_text})
        try:
            reply, history = ask_jarvis(history, on_status=lambda s: print(f"  … {s}"))
        except Exception as exc:
            history.pop()  # keep history consistent after a failed turn
            print(f"jarvis> error: {exc}", file=sys.stderr)
            continue
        print(f"jarvis> {reply}\n")


if __name__ == "__main__":
    sys.exit(main())
