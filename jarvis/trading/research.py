"""Trading pipeline step 1 — market research & volatility-based financial modelling.

Claude (the Main Brain) does the heavy reasoning here, grounded in fresh
Google Search results so the model reflects current market conditions.
"""

import anthropic

from jarvis import config
from jarvis.tools.google_search import google_search

RESEARCH_SYSTEM = """You are a quantitative market researcher. Using the supplied \
live search results plus your own knowledge, produce a research report containing:

1. Current market conditions for the target market (trend, sentiment, key drivers, \
upcoming events/risks).
2. A volatility assessment (realised vs implied where known, regime: low/normal/high).
3. A mathematical financial model built on that volatility — define every variable, \
give the formulas explicitly (e.g. ATR-scaled position sizing, Bollinger/Keltner \
bands, GARCH-style regime notes, expected-value of the setup), and state entry, \
exit, stop-loss and position-sizing rules precisely enough that they can be \
translated directly into Pine Script.
4. Honest limitations of the model.

Be rigorous and explicit. This report feeds an automated strategy-coding step."""


def run_market_research(market: str, focus: str = "") -> str:
    """Research a market and return a report with a volatility-based model."""
    queries = [
        f"{market} market outlook today",
        f"{market} volatility analysis",
    ]
    if focus:
        queries.append(f"{market} {focus}")

    search_digest = []
    for q in queries:
        search_digest.append(f"### Search: {q}\n{google_search(q, 4)}")
    live_context = "\n\n".join(search_digest)

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY or None)
    with client.messages.stream(
        model=config.CLAUDE_MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=RESEARCH_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Target market: {market}\n"
                    f"Extra focus: {focus or 'none'}\n\n"
                    f"Live search results:\n{live_context}"
                ),
            }
        ],
    ) as stream:
        message = stream.get_final_message()
    return "".join(b.text for b in message.content if b.type == "text")
