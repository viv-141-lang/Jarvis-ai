"""Trading pipeline step 2 — translate a financial model into Pine Script v5."""

import anthropic

from jarvis import config

PINE_SYSTEM = """You are an expert TradingView Pine Script v5 developer. Translate \
the given financial model into a complete, compilable `strategy()` script.

Requirements:
- `//@version=5` with a `strategy()` declaration (sensible `default_qty_type`, \
`initial_capital`, `commission_type`/`commission_value` for Indian equity markets).
- Implement the model's entry/exit/stop/position-sizing rules faithfully. If the \
model leaves something unspecified, choose a conservative default and mark it with \
a `// ASSUMPTION:` comment.
- Always include a hard stop-loss and a max-position guard. Never use martingale \
or unbounded pyramiding.
- Wire alert messages for the webhook executor using alert_message in \
strategy.entry/strategy.exit, with this exact JSON payload shape:
  {"secret": "{{WEBHOOK_SECRET}}", "symbol": "<SYMBOL>", "action": "BUY"|"SELL", \
"quantity": {{strategy.order.contracts}}, "order_type": "MARKET"}
- Output the full script in one ```pinescript code block, followed by a short \
plain-text section listing the assumptions made and the inputs a user may tune."""


def generate_pine_script(model_description: str, symbol: str) -> str:
    """Generate Pine Script v5 strategy code for the given model."""
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY or None)
    with client.messages.stream(
        model=config.CLAUDE_MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=PINE_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Target symbol: {symbol}\n\n"
                    f"Financial model to implement:\n{model_description}"
                ),
            }
        ],
    ) as stream:
        message = stream.get_final_message()
    return "".join(b.text for b in message.content if b.type == "text")
