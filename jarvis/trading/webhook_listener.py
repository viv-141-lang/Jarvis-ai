"""Trading pipeline live execution — TradingView alert webhook → Zerodha order.

Run as a standalone background service on your PC:

    uvicorn jarvis.trading.webhook_listener:app --host 0.0.0.0 --port 8080

Point your TradingView alert webhook at  http://<public-url>/tradingview
(use ngrok or similar to expose the port). The alert message must be the JSON
payload produced by the generated Pine Script, including the shared secret.

Safety rails (configure in .env):
- DRY_RUN=true (default): orders are logged, NOT sent to Zerodha. Set
  DRY_RUN=false only when you have verified everything end to end.
- TRADINGVIEW_WEBHOOK_SECRET must match the alert payload.
- MAX_ORDER_QUANTITY, MAX_ORDERS_PER_DAY, ALLOWED_SYMBOLS hard limits.
"""

import hmac
import logging
from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from jarvis import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("jarvis.executor")

app = FastAPI(title="Jarvis TradingView → Zerodha executor")

_kite = None
_orders_today = {"date": date.today(), "count": 0}


class TradingViewAlert(BaseModel):
    secret: str
    symbol: str
    action: str = Field(pattern="^(BUY|SELL)$")
    quantity: int = Field(gt=0)
    order_type: str = "MARKET"
    exchange: str = "NSE"
    product: str = "MIS"  # intraday by default


def _get_kite():
    global _kite
    if _kite is None:
        from kiteconnect import KiteConnect

        if not config.KITE_API_KEY or not config.KITE_ACCESS_TOKEN:
            raise RuntimeError("KITE_API_KEY / KITE_ACCESS_TOKEN not configured")
        _kite = KiteConnect(api_key=config.KITE_API_KEY)
        _kite.set_access_token(config.KITE_ACCESS_TOKEN)
    return _kite


def _check_limits(alert: TradingViewAlert) -> None:
    today = date.today()
    if _orders_today["date"] != today:
        _orders_today["date"] = today
        _orders_today["count"] = 0

    if _orders_today["count"] >= config.MAX_ORDERS_PER_DAY:
        raise HTTPException(429, f"Daily order limit reached ({config.MAX_ORDERS_PER_DAY})")
    if alert.quantity > config.MAX_ORDER_QUANTITY:
        raise HTTPException(400, f"Quantity {alert.quantity} exceeds MAX_ORDER_QUANTITY")
    if config.ALLOWED_SYMBOLS and alert.symbol.upper() not in config.ALLOWED_SYMBOLS:
        raise HTTPException(400, f"Symbol {alert.symbol} not in ALLOWED_SYMBOLS")


@app.get("/health")
def health():
    return {"status": "ok", "dry_run": config.DRY_RUN}


@app.post("/tradingview")
def tradingview_webhook(alert: TradingViewAlert):
    if not config.TRADINGVIEW_WEBHOOK_SECRET or not hmac.compare_digest(
        alert.secret, config.TRADINGVIEW_WEBHOOK_SECRET
    ):
        raise HTTPException(403, "Invalid webhook secret")

    _check_limits(alert)
    symbol = alert.symbol.upper()

    if config.DRY_RUN:
        _orders_today["count"] += 1
        log.info("[DRY RUN] %s %s x%s (%s)", alert.action, symbol, alert.quantity, alert.order_type)
        return {"status": "dry_run", "action": alert.action, "symbol": symbol,
                "quantity": alert.quantity}

    kite = _get_kite()
    try:
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=alert.exchange,
            tradingsymbol=symbol,
            transaction_type=alert.action,
            quantity=alert.quantity,
            product=alert.product,
            order_type=alert.order_type,
        )
    except Exception as exc:
        log.error("Order failed for %s %s: %s", alert.action, symbol, exc)
        raise HTTPException(502, f"Zerodha order failed: {exc}")

    _orders_today["count"] += 1
    log.info("Placed order %s: %s %s x%s", order_id, alert.action, symbol, alert.quantity)
    return {"status": "placed", "order_id": order_id}
