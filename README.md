# J.A.R.V.I.S. — Multi-Model Voice Assistant

A local voice assistant that fuses three AI brains — **Claude** (Main Brain & chief
manager), **Gemini** (cloud workhorse) and **Ollama** (free local model) — behind a
Chainlit voice interface, with live Google News search and a Claude-managed
trading pipeline (research → Pine Script → validation → Zerodha execution).

## How the Multi-Model Hub works

Every request goes to **Claude first**. Claude decides, via tool use, how to spend
tokens:

| Task type | Handled by |
|---|---|
| Deep research, financial modelling, final trading decisions | Claude itself |
| Routine cloud tasks (summaries, drafting, translation) | → delegated to Gemini |
| Trivial tasks (rewording, formatting, chit-chat) | → delegated to local Ollama (free) |
| Current events / world news | → Google Search, then a spoken summary |

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env    # then fill in your keys
```

You need:
- `ANTHROPIC_API_KEY` — https://console.anthropic.com
- `GEMINI_API_KEY` — https://aistudio.google.com
- [Ollama](https://ollama.com) running locally (`ollama pull llama3`)
- `GOOGLE_SEARCH_API_KEY` + `GOOGLE_SEARCH_CX` — Google Programmable Search Engine
- (Trading) `KITE_API_KEY`, `KITE_ACCESS_TOKEN`, `TRADINGVIEW_WEBHOOK_SECRET`

After filling in `.env`, verify your setup:

```bash
python -m jarvis.doctor    # checks every key/integration and tells you what's missing
```

## Run the voice chat

```bash
chainlit run app.py -w
```

On Windows you can instead use the one-shot scripts (they create the venv,
install deps, run the doctor, then launch):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-jarvis.ps1     # voice UI
powershell -ExecutionPolicy Bypass -File scripts\start-executor.ps1   # trading executor
```

Prefer the terminal? `python -m jarvis.cli` gives you the same brain in
text-only mode.

Open http://localhost:8000, click the microphone and talk. Jarvis transcribes you
locally with Whisper, replies in text, and speaks the answer aloud (edge-tts).

## The Trading Workflow

Ask Jarvis e.g. *"Research NIFTY volatility and build me an intraday strategy."*
Claude runs the strict three-step pipeline:

1. **Market research** — live Google data + Claude builds a volatility-based
   mathematical financial model.
2. **Strategy coding & validation** — the model is translated into Pine Script v5,
   then a risk-manager pass returns an `APPROVED` / `REJECTED` verdict. Only
   approved strategies should be deployed.
3. **Live execution** — paste the approved script into TradingView, create an alert
   pointing at the webhook listener:

   ```bash
   uvicorn jarvis.trading.webhook_listener:app --host 0.0.0.0 --port 8080
   # expose it publicly, e.g.:  ngrok http 8080
   ```

   TradingView alert → webhook → order placed on Zerodha via Kite Connect.

### ⚠️ Safety rails (read before going live)

- **`DRY_RUN=true` by default** — orders are logged, not sent. Flip to `false`
  only after end-to-end verification.
- Shared-secret check on every webhook, plus `MAX_ORDER_QUANTITY`,
  `MAX_ORDERS_PER_DAY` and an optional `ALLOWED_SYMBOLS` whitelist.
- Automated trading carries real financial risk. A model verdict of `APPROVED`
  is an analysis aid, not financial advice — backtest on TradingView and start
  with tiny position sizes.

## Project layout

```
app.py                          Chainlit voice UI (mic in, spoken answers out)
jarvis/config.py                All settings, loaded from .env
jarvis/router.py                Claude Main Brain + smart routing (tool use)
jarvis/brains/                  Gemini + Ollama delegates
jarvis/tools/google_search.py   Live news via Google Custom Search
jarvis/trading/research.py      Step 1: market research + volatility model
jarvis/trading/pinescript.py    Step 2: Pine Script v5 generation
jarvis/trading/validator.py     Step 3: safety/profitability verdict
jarvis/trading/webhook_listener.py  TradingView → Zerodha executor (FastAPI)
jarvis/voice/                   Whisper STT + edge-tts TTS
jarvis_web.py                   Legacy Streamlit prototype
```
