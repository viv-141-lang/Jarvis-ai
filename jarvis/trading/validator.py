"""Trading pipeline step 3 — safety & profitability validation of a strategy."""

import anthropic
from pydantic import BaseModel

from jarvis import config


class StrategyVerdict(BaseModel):
    verdict: str  # "APPROVED" or "REJECTED"
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    safety_issues: list[str]
    profitability_assessment: str
    required_fixes: list[str]
    summary: str


VALIDATOR_SYSTEM = """You are a ruthless risk manager reviewing a Pine Script \
strategy before it is allowed to trade real money on a Zerodha account.

Check at minimum:
- Hard stop-loss present and always active; bounded position size; no martingale, \
no unbounded pyramiding, no averaging-down into losers.
- Realistic assumptions: commissions/slippage modelled, no lookahead bias \
(request.security with lookahead, calc_on_every_tick abuse), no repainting signals.
- Logic actually matches the stated intent; alert payloads are wired correctly.
- Plausible profitability: positive expectancy logic, sane risk:reward, not an \
overfit indicator soup.

Verdict must be APPROVED only when you would genuinely let this trade live money. \
When in doubt, REJECT and list required fixes."""


def validate_strategy(pine_script: str, strategy_context: str = "") -> str:
    """Analyse a Pine Script strategy; returns a formatted verdict report."""
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY or None)
    response = client.messages.parse(
        model=config.CLAUDE_MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=VALIDATOR_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Strategy context: {strategy_context or 'not provided'}\n\n"
                    f"Pine Script to review:\n```pinescript\n{pine_script}\n```"
                ),
            }
        ],
        output_format=StrategyVerdict,
    )
    v: StrategyVerdict = response.parsed_output

    lines = [
        f"VERDICT: {v.verdict}",
        f"Risk level: {v.risk_level}",
        "",
        f"Summary: {v.summary}",
        "",
        f"Profitability assessment: {v.profitability_assessment}",
    ]
    if v.safety_issues:
        lines += ["", "Safety issues:"] + [f"- {s}" for s in v.safety_issues]
    if v.required_fixes:
        lines += ["", "Required fixes before deployment:"] + [f"- {f}" for f in v.required_fixes]
    return "\n".join(lines)
