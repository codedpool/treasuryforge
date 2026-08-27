"""Wallet performance metrics: realized + unrealized P&L, win rate, max
drawdown, Sharpe ratio.

Two honestly-documented simplifications, both driven by what data this
paper wallet actually has (no historical price series for the whole
basket, no scheduler):

- max_drawdown / sharpe are computed from equity_snapshots
  (wallet.record_equity_snapshot), recorded on every execute_trade call,
  each daily-baseline rollover, and opportunistically on a timer checked
  lazily on every get_portfolio call (wallet._record_periodic_snapshot_if_due,
  every 5 minutes at most) -- not a true fixed-interval mark-to-market
  curve, since that periodic top-up only fires when something actually
  calls get_portfolio. A portfolio that moves and is never read during a
  gap that long still won't show up.
- sharpe_ratio is unannualized (mean/stdev of snapshot-to-snapshot % returns,
  not scaled by sqrt(periods per year)) -- annualizing implies a regular
  time interval between observations, which event-driven snapshots don't
  have. An annualized number computed from irregularly-spaced demo-session
  data would be more misleading than useful.

Read-only: only reads, never touches holdings/transactions/meta.
"""

import statistics
from datetime import datetime, timezone

from . import db, wallet


def _equity_series() -> list[float]:
    """equity_snapshots' total_usd, oldest first, with the current live
    portfolio value appended as the most recent point -- so metrics reflect
    right now, not just the last time something happened to trigger a
    snapshot."""
    conn = db.get_conn()
    rows = conn.execute(
        "SELECT total_usd FROM equity_snapshots ORDER BY id ASC"
    ).fetchall()
    series = [r["total_usd"] for r in rows]
    series.append(wallet.get_portfolio()["total_usd"])
    return series


def get_equity_curve() -> list[dict]:
    """Same series _equity_series() computes, but with timestamps and the
    recording reason attached -- max_drawdown_pct/sharpe_ratio only need the
    bare values, but the dashboard's P&L chart needs a time axis to plot
    against."""
    conn = db.get_conn()
    rows = conn.execute(
        "SELECT timestamp, total_usd, reason FROM equity_snapshots ORDER BY id ASC"
    ).fetchall()
    points = [{"timestamp": r["timestamp"], "total_usd": r["total_usd"], "reason": r["reason"]} for r in rows]
    points.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_usd": wallet.get_portfolio()["total_usd"],
        "reason": "now",
    })
    return points


def max_drawdown_pct(series: list[float] | None = None) -> float | None:
    """Largest peak-to-trough decline in the equity series, as a percentage.
    None if there's no data yet (a fresh, never-traded wallet)."""
    series = series if series is not None else _equity_series()
    if not series:
        return None
    peak = series[0]
    worst = 0.0
    for value in series:
        peak = max(peak, value)
        if peak > 0:
            worst = max(worst, (peak - value) / peak * 100)
    return round(worst, 3)


def sharpe_ratio(series: list[float] | None = None) -> float | None:
    """Unannualized mean/stdev of snapshot-to-snapshot % returns -- see
    module docstring for why this isn't scaled to an annualized figure.
    None if there are fewer than 3 equity points (need at least 2 returns
    to compute a standard deviation), or if returns have zero variance
    (division by zero -- a wallet that never moved)."""
    series = series if series is not None else _equity_series()
    if len(series) < 3:
        return None
    returns = [
        (series[i] - series[i - 1]) / series[i - 1]
        for i in range(1, len(series))
        if series[i - 1] > 0
    ]
    if len(returns) < 2:
        return None
    stdev = statistics.stdev(returns)
    # A truly *exact* 0.0 essentially never happens for real returns --
    # dividing floats that individually round to the same value (e.g. a
    # perfectly steady growth rate computed independently each step) still
    # leaves float noise on the order of 1e-16 in the stdev, which turns a
    # meaningless near-zero-variance ratio into an enormous, equally
    # meaningless Sharpe number instead of the None a genuinely flat series
    # should report. 1e-9 is comfortably above that noise floor and well
    # below any real percentage-return variance worth reporting.
    if stdev < 1e-9:
        return None
    return round(statistics.mean(returns) / stdev, 4)


def get_wallet_metrics() -> dict:
    """Realized + unrealized P&L, win rate, max drawdown, and (unannualized)
    Sharpe ratio, computed from actual transaction and equity-snapshot
    history -- not the LLM's own estimate. Meant for the self-audit
    subagent's periodic summaries and for get_transaction_log's
    risk_snapshot data to be checked against."""
    portfolio = wallet.get_portfolio()
    pnl_series, cost_basis = wallet.realized_pnl_and_cost_basis()

    realized_pnl_usd = sum(pnl_series)

    price_by_asset = {p["asset"]: p["price_usd"] for p in portfolio["positions"]}
    unrealized_pnl_usd = 0.0
    for asset, (remaining_qty, remaining_cost) in cost_basis.items():
        if remaining_qty <= 1e-12:
            continue
        current_price = price_by_asset.get(asset)
        if current_price is None:
            continue  # quote unavailable right now -- skip rather than misprice
        unrealized_pnl_usd += remaining_qty * current_price - remaining_cost

    wins = sum(1 for pnl in pnl_series if pnl > 0)
    total_closed = len(pnl_series)
    win_rate = round(wins / total_closed, 4) if total_closed > 0 else None

    series = _equity_series()

    return {
        "realized_pnl_usd": round(realized_pnl_usd, 2),
        "unrealized_pnl_usd": round(unrealized_pnl_usd, 2),
        "total_pnl_usd": round(realized_pnl_usd + unrealized_pnl_usd, 2),
        "win_rate": win_rate,
        "closed_trades": total_closed,
        "max_drawdown_pct": max_drawdown_pct(series),
        "sharpe_ratio_unannualized": sharpe_ratio(series),
        "equity_points": len(series),
        "current_total_usd": round(portfolio["total_usd"], 2),
    }
