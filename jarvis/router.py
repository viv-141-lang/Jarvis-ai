"""The Multi-Model Hub.

Claude is the Main Brain: every user request goes to Claude first. Claude
decides — via tool use — whether to answer itself (heavy research, trading
decisions), delegate to Gemini or local Ollama (routine work, to save tokens),
search Google for live information, or drive the trading pipeline.
"""

import anthropic

from jarvis import config
from jarvis.brains.gemini_brain import ask_gemini
from jarvis.brains.ollama_brain import ask_ollama
from jarvis.tools.google_search import google_search
from jarvis.trading import pinescript, research, validator

SYSTEM_PROMPT = """You are J.A.R.V.I.S., a voice assistant. You are the Main Brain \
and chief manager of a multi-model hub. Address the user as "Sir" sparingly and keep \
the Iron Man flavour light.

Your answers are spoken aloud via text-to-speech, so keep conversational replies \
concise and natural — no markdown tables, no code blocks unless the user explicitly \
asks to see code, no long bullet lists.

Token-economy routing policy. The user has FREE local Ollama and a Gemini Pro \
subscription with generous quota, while your own tokens are the most expensive — so \
delegate aggressively and reserve yourself for what only you should do:
- Handle yourself ONLY: multi-step reasoning that spans the whole conversation, \
financial modelling, final trading decisions, and synthesising delegated results.
- delegate_to_gemini (preferred default for substantial work): summarisation, \
translation, drafting, explanations, general knowledge Q&A, digesting search results, \
code explanations — anything self-contained that a strong cloud model handles well.
- delegate_to_ollama: simple, low-stakes tasks — quick rewording, casual chit-chat \
filler, formatting, short lists. It runs free on the user's local PC, so prefer it for \
trivial work. If it errors (server offline), fall back to Gemini.
- google_search: whenever the user asks about current events, news, prices, or \
anything after your knowledge cutoff. Search first, then give a spoken-style summary \
citing the sources briefly by name.

Trading pipeline (strict order — never skip a step):
1. run_market_research — research market conditions and build a volatility-based \
financial model.
2. generate_pine_script — translate an approved model into Pine Script v5.
3. validate_strategy — analyse the script for safety and profitability. Only a \
strategy you have validated may be deployed. Live execution happens via the separate \
TradingView→Zerodha webhook listener; you never place orders directly.

When you delegate, pass a fully self-contained prompt — the sub-model cannot see this \
conversation."""

TOOLS = [
    {
        "name": "delegate_to_gemini",
        "description": (
            "Delegate a task to Google Gemini Pro (the user has a Pro subscription "
            "with generous quota — prefer this for any substantial self-contained "
            "work to save Claude tokens): summarisation, translation, drafting, "
            "explanations, digesting search results, general knowledge questions. "
            "Pass a fully self-contained prompt."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Self-contained task prompt"}
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "delegate_to_ollama",
        "description": (
            "Delegate a simple, low-stakes task to the free local Ollama model on the "
            "user's PC. Use for trivial work: quick rewording, formatting, short "
            "lists, casual filler. Pass a fully self-contained prompt."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Self-contained task prompt"}
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "google_search",
        "description": (
            "Search Google for live information. Call this when the user asks about "
            "current events, world news, prices, or anything time-sensitive. Returns "
            "titles, snippets and source links for the top results."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
                "num_results": {
                    "type": "integer",
                    "description": "How many results to fetch (1-10, default 5)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "run_market_research",
        "description": (
            "Trading pipeline step 1. Research current global market conditions for a "
            "given instrument/market and build a mathematical financial model based "
            "on market volatility. Returns a research report with the model."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "market": {
                    "type": "string",
                    "description": "Instrument or market to research, e.g. 'NIFTY 50', 'RELIANCE'",
                },
                "focus": {
                    "type": "string",
                    "description": "Optional extra focus, e.g. 'intraday volatility breakout'",
                },
            },
            "required": ["market"],
        },
    },
    {
        "name": "generate_pine_script",
        "description": (
            "Trading pipeline step 2. Translate a financial model / strategy "
            "description into TradingView Pine Script v5 strategy code with an alert "
            "payload wired for the Zerodha webhook executor."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "model_description": {
                    "type": "string",
                    "description": "The financial model / strategy rules to implement",
                },
                "symbol": {"type": "string", "description": "Target trading symbol"},
            },
            "required": ["model_description", "symbol"],
        },
    },
    {
        "name": "validate_strategy",
        "description": (
            "Trading pipeline step 3. Analyse a Pine Script strategy for safety and "
            "profitability. Returns a structured verdict (APPROVED/REJECTED) with "
            "risk assessment. A strategy must be APPROVED before deployment."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pine_script": {"type": "string", "description": "The Pine Script code"},
                "strategy_context": {
                    "type": "string",
                    "description": "What the strategy is meant to do and on which market",
                },
            },
            "required": ["pine_script"],
        },
    },
]

MAX_TOOL_ROUNDS = 8

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY or None)
    return _client


def _execute_tool(name: str, args: dict) -> str:
    if name == "delegate_to_gemini":
        return ask_gemini(args["prompt"])
    if name == "delegate_to_ollama":
        return ask_ollama(args["prompt"])
    if name == "google_search":
        return google_search(args["query"], int(args.get("num_results", 5)))
    if name == "run_market_research":
        return research.run_market_research(args["market"], args.get("focus", ""))
    if name == "generate_pine_script":
        return pinescript.generate_pine_script(args["model_description"], args["symbol"])
    if name == "validate_strategy":
        return validator.validate_strategy(
            args["pine_script"], args.get("strategy_context", "")
        )
    return f"Unknown tool: {name}"


def ask_jarvis(history: list[dict], on_status=None) -> tuple[str, list[dict]]:
    """Run one Jarvis turn.

    `history` is a Messages-API message list ending with the new user message.
    Returns (final_text, updated_history). `on_status` is an optional callback
    receiving short progress strings ("Delegating to Gemini…") for the UI.
    """
    client = _get_client()
    messages = list(history)

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            final_text = "".join(b.text for b in response.content if b.type == "text")
            messages.append({"role": "assistant", "content": final_text})
            return final_text, messages

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            if on_status:
                on_status(_status_label(block.name))
            try:
                result = _execute_tool(block.name, dict(block.input))
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result}
                )
            except Exception as exc:  # surface failures so Claude can re-route
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Tool error: {exc}",
                        "is_error": True,
                    }
                )
        messages.append({"role": "user", "content": tool_results})

    fallback = "I hit my tool-use limit for this request, Sir. Could you rephrase or split it up?"
    messages.append({"role": "assistant", "content": fallback})
    return fallback, messages


def _status_label(tool_name: str) -> str:
    return {
        "delegate_to_gemini": "🧠 Delegating to Gemini…",
        "delegate_to_ollama": "💻 Delegating to local Ollama…",
        "google_search": "🌍 Searching Google for live information…",
        "run_market_research": "📊 Step 1/3 — Running market research…",
        "generate_pine_script": "📜 Step 2/3 — Writing Pine Script…",
        "validate_strategy": "🛡️ Step 3/3 — Validating strategy safety…",
    }.get(tool_name, f"Running {tool_name}…")
