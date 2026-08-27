"""Computed risk checks for proposed trades.

TrueForge's approval checkpoint (`require_approval_for_tools`) is coarse: it
pauses *every* execute_trade call, unconditionally -- it has no concept of
"only pause if this breaches a limit" (verified against the vendored
TrueForge dist; the manifest only takes a tool name list, nothing
conditional). So the plan's four risk triggers can't be enforced by TrueForge
itself. What they *can* do is give the human at the checkpoint real computed
numbers instead of an LLM's unverified claim about them -- that's this
module's job. execute_trade stays the sole enforcement point for "does this
trade even execute"; check_risk_limits is read-only and advisory, meant to be
called (and its numbers cited) before every execute_trade proposal.

Read-only: never touches holdings/transactions, only meta (day-start
baseline rollover, via wallet.py) and reads.
"""

import math
from datetime import datetime, timezone

from . import db, wallet

DAILY_DRAWDOWN_LIMIT_PCT = 5.0
MAX_SINGLE_ASSET_PCT = 50.0
CONSECUTIVE_LOSS_LIMIT = 2
SELL_ALL_THRESHOLD_PCT = 99.0  # selling >= this much of a holding counts as "sell all"


def _realized_pnl_series() -> list[float]:
    """Realized P&L of every *executed* sell, oldest first, using running
    average cost per asset. Seed rows count toward cost basis (they
    represent a real acquisition price) but aren't sales themselves.
    DRY_RUN rows are excluded entirely -- they never touched holdings (see
    wallet.execute_trade), so counting them here would let simulated trades
    fabricate a consecutive-loss streak (and corrupt the cost basis used for
    real sells) under the default DRY_RUN=true config."""
    conn = db.get_conn()
    rows = conn.execute(
        "SELECT asset, side, quantity, price_usd FROM transactions "
        "WHERE side IN ('buy', 'sell', 'seed') AND asset != 'CASH' AND dry_run = 0 "
        "ORDER BY id ASC"
    ).fetchall()

    cost_basis: dict[str, tuple[float, float]] = {}  # asset -> (total_qty, total_cost)
    pnl_series: list[float] = []

    for r in rows:
        asset, side, qty, price = r["asset"], r["side"], r["quantity"], r["price_usd"]
        tot_qty, tot_cost = cost_basis.get(asset, (0.0, 0.0))
        if side in ("buy", "seed"):
            cost_basis[asset] = (tot_qty + qty, tot_cost + qty * price)
        else:  # sell
            avg_price = tot_cost / tot_qty if tot_qty > 1e-12 else price
            pnl_series.append((price - avg_price) * qty)
            new_qty = max(tot_qty - qty, 0.0)
            cost_basis[asset] = (new_qty, avg_price * new_qty)

    return pnl_series


def consecutive_losses() -> int:
    """How many of the most recent sells, walking backward, were losses --
    resets at the first winning sell (or the start of history)."""
    streak = 0
    for pnl in reversed(_realized_pnl_series()):
        if pnl < 0:
            streak += 1
        else:
            break
    return streak


def _project_trade(asset: str, side: str, quantity: float | None, usd_amount: float | None) -> dict:
    """Read-only projection of a trade's effect -- same validation and
    pricing as wallet.execute_trade, but never writes anything."""
    asset = asset.upper()
    side = side.lower()
    if asset not in wallet.TRADABLE_ASSETS:
        raise ValueError(f"Unknown tradable asset: {asset}. Supported: {wallet.TRADABLE_ASSETS}")
    if side not in ("buy", "sell"):
        raise ValueError(f"side must be 'buy' or 'sell', got {side!r}")
    if (quantity is None) == (usd_amount is None):
        raise ValueError("Provide exactly one of quantity or usd_amount")

    amount: float = quantity if quantity is not None else usd_amount  # type: ignore[assignment]
    if not math.isfinite(amount) or amount <= 0:
        raise ValueError(f"quantity/usd_amount must be a finite positive number, got {amount}")

    portfolio = wallet.get_portfolio()
    unpriced = [p["asset"] for p in portfolio["positions"] if p["price_usd"] is None]
    if unpriced:
        raise ValueError(
            f"Cannot compute risk: no live quote for {unpriced} right now, so portfolio "
            "total/concentration would silently exclude their value. Try again once their "
            "quote source recovers."
        )
    total_usd = portfolio["total_usd"]
    cash = portfolio["cash_usd"]
    position = next((p for p in portfolio["positions"] if p["asset"] == asset), None)
    current_qty = position["quantity"] if position else 0.0

    quote = wallet._price_usd(asset)
    price_usd = float(quote["price_usd"])

    if quantity is None:
        assert usd_amount is not None
        quantity = usd_amount / price_usd
    quantity = float(quantity)
    usd_value = quantity * price_usd

    if side == "buy":
        projected_qty = current_qty + quantity
        can_afford = usd_value <= cash + 1e-9
        is_sell_all = False
    else:
        projected_qty = max(current_qty - quantity, 0.0)
        can_afford = True  # affordability isn't a "buy" concept for sells
        is_sell_all = current_qty > 1e-12 and quantity >= current_qty * (SELL_ALL_THRESHOLD_PCT / 100)

    projected_asset_usd_value = projected_qty * price_usd
    projected_concentration_pct = (
        (projected_asset_usd_value / total_usd * 100) if total_usd > 0 else 0.0
    )

    return {
        "asset": asset,
        "side": side,
        "quantity": quantity,
        "price_usd": price_usd,
        "usd_value": usd_value,
        "current_holding_qty": current_qty,
        "total_usd": total_usd,
        "day_start_value_usd": portfolio["day_start_value_usd"],
        "can_afford": can_afford,
        "is_sell_all": is_sell_all,
        "projected_concentration_pct": projected_concentration_pct,
    }


def check_risk_limits(
    asset: str,
    side: str,
    quantity: float | None = None,
    usd_amount: float | None = None,
) -> dict:
    """Computed answer to "would this trade breach a risk limit" -- call this
    with the exact same arguments you're about to pass to execute_trade,
    before proposing it. Read-only; safe to call as often as needed."""
    projection = _project_trade(asset, side, quantity, usd_amount)
    total_usd = projection["total_usd"]

    # The day-start baseline is rolled by wallet.get_portfolio (called inside
    # _project_trade above), not here -- see wallet.py's docstring on why.
    day_start = projection["day_start_value_usd"]
    drawdown_pct = max(0.0, (day_start - total_usd) / day_start * 100) if day_start > 0 else 0.0

    streak = consecutive_losses()

    triggers = {
        "daily_drawdown": {
            "breached": drawdown_pct >= DAILY_DRAWDOWN_LIMIT_PCT,
            "current_pct": round(drawdown_pct, 3),
            "limit_pct": DAILY_DRAWDOWN_LIMIT_PCT,
            "day_start_value_usd": round(day_start, 2),
            "current_total_usd": round(total_usd, 2),
        },
        "consecutive_losses": {
            "breached": streak > CONSECUTIVE_LOSS_LIMIT,
            "streak": streak,
            "limit": CONSECUTIVE_LOSS_LIMIT,
        },
        "concentration": {
            "breached": projection["projected_concentration_pct"] > MAX_SINGLE_ASSET_PCT,
            "asset": projection["asset"],
            "projected_pct": round(projection["projected_concentration_pct"], 3),
            "limit_pct": MAX_SINGLE_ASSET_PCT,
        },
        "sell_all": {
            "breached": projection["is_sell_all"],
            "asset": projection["asset"],
        },
    }
    any_breach = any(t["breached"] for t in triggers.values())

    return {
        "asset": projection["asset"],
        "side": projection["side"],
        "quantity": projection["quantity"],
        "projected_usd_value": round(projection["usd_value"], 2),
        "can_afford": projection["can_afford"],
        "triggers": triggers,
        "any_breach": any_breach,
        "recommend_sandbox_stress_test": any_breach,
    }


def force_daily_drawdown_breach(margin_pct: float = 1.0) -> dict:
    """Debug/demo only -- never called from the agent's own decision loop.
    Rolls the stored day-start baseline back far enough that the *next*
    check_risk_limits call reports a genuine daily_drawdown breach, so a demo
    can reliably show the approval gate firing over a real (if synthesized)
    computed number on cue instead of hoping the agent proposes a risky trade
    naturally. Cleared by POST /debug/reset (wipes the meta table)."""
    portfolio = wallet.get_portfolio()
    total_usd = portfolio["total_usd"]
    today = datetime.now(timezone.utc).date().isoformat()
    target_pct = DAILY_DRAWDOWN_LIMIT_PCT + margin_pct
    inflated_day_start = total_usd / (1 - target_pct / 100)

    wallet.write_day_start(today, inflated_day_start)

    return {
        "forced": True,
        "day_start_value_usd": round(inflated_day_start, 2),
        "current_total_usd": round(total_usd, 2),
        "synthetic_drawdown_pct": round(target_pct, 3),
        "note": (
            "Synthetic day-start baseline set so the next check_risk_limits call "
            "reports a daily_drawdown breach. Debug/demo only -- POST /debug/reset "
            "clears it."
        ),
    }
