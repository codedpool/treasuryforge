"""The paper wallet. This module is the only place that mutates wallet
state -- every other module (pricing, seed) only reads or is read from here.
"""

import json
import math
import threading
from datetime import datetime, timezone

from . import config, db, seed
from .pricing_crypto import get_crypto_price, get_crypto_prices
from .pricing_equity import NSE_TICKERS, get_equity_price, market_open

CRYPTO_ASSETS = ["BTC", "ETH"]
TRADABLE_ASSETS = CRYPTO_ASSETS + NSE_TICKERS

# How often get_portfolio may opportunistically top up the equity curve with
# a "periodic" snapshot, on top of the existing trade/day-start events -- see
# _record_periodic_snapshot_if_due.
PERIODIC_SNAPSHOT_INTERVAL_SECONDS = 5 * 60

# Serializes every operation that mutates wallet state: trades, the first
# seed, and reset/reseed. Each thread has its own sqlite connection (see
# db.py), so without this, two overlapping calls could read the same
# starting state and one write could clobber the other -- e.g. a reset
# racing a trade, or two first requests both seeding (seed_wallet() is
# idempotent on its own, but only once serialized; see difficulties.md).
_trade_lock = threading.Lock()


def _ensure_seeded() -> None:
    if not seed.is_initialized():
        with _trade_lock:
            seed.seed_wallet()


def read_day_start() -> tuple[str | None, float | None]:
    """(date, value_usd) of the current daily-drawdown baseline, or (None,
    None) if it's never been set. Stored as one JSON meta value so a
    concurrent reader can never observe today's date paired with a stale or
    missing value -- two separate meta writes would leave exactly that
    window open (a real Qodo finding on the first cut of this)."""
    raw = db.get_meta("day_start")
    if not raw:
        return None, None
    try:
        data = json.loads(raw)
        return data.get("date"), data.get("value_usd")
    except (ValueError, TypeError):
        return None, None


def write_day_start(date_str: str, value_usd: float) -> None:
    db.set_meta("day_start", json.dumps({"date": date_str, "value_usd": value_usd}))


def record_equity_snapshot(total_usd: float, reason: str) -> None:
    """Appends one point to the equity curve metrics.max_drawdown/sharpe_ratio
    read from. Recorded on every execute_trade call (DRY_RUN or live -- both
    reflect real market movement the agent observed, which is what a
    drawdown curve should track) and on each daily-baseline rollover, so the
    curve has real granularity within a single demo session instead of at
    most one point per day."""
    conn = db.get_conn()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO equity_snapshots (timestamp, total_usd, reason) VALUES (?, ?, ?)",
        (now, total_usd, reason),
    )
    conn.commit()


def set_holding_quantity(asset: str, quantity: float) -> None:
    """Directly overwrites a holding's quantity, bypassing execute_trade's
    cash/validation/lock-scoped accounting entirely -- cash is left
    untouched. Debug/demo only: used by risk.py's force_concentration_breach
    and force_sell_all_breach to put a known, specific quantity of a real
    asset in place on demand, the same way force_daily_drawdown_breach
    overwrites the day_start baseline directly rather than trading toward
    it. Never called from the agent's own decision loop or execute_trade."""
    asset = asset.upper()
    with _trade_lock:
        conn = db.get_conn()
        conn.execute(
            "INSERT INTO holdings (asset, quantity) VALUES (?, ?) "
            "ON CONFLICT(asset) DO UPDATE SET quantity = excluded.quantity",
            (asset, quantity),
        )
        conn.commit()


def record_synthetic_transaction(asset: str, side: str, quantity: float, price_usd: float, reason: str) -> None:
    """Inserts a transaction row directly (dry_run=0), skipping
    execute_trade's cash/holdings mutation and validation entirely. Debug/
    demo only: used by risk.py's force_consecutive_losses_breach to write a
    realized-loss streak straight into the data realized_pnl_and_cost_basis
    reads, which is otherwise nearly unreachable on demand -- a real losing
    streak needs real losing live trades, and DRY_RUN sells are correctly
    excluded from realized P&L. Never called from the agent's own decision
    loop; asset is deliberately not validated against TRADABLE_ASSETS so
    callers can use an isolated synthetic ticker that can't blend into any
    real position's cost basis (see force_consecutive_losses_breach)."""
    asset = asset.upper()
    with _trade_lock:
        conn = db.get_conn()
        now = datetime.now(timezone.utc).isoformat()
        usd_value = quantity * price_usd
        conn.execute(
            "INSERT INTO transactions "
            "(timestamp, asset, side, quantity, price_usd, usd_value, reason, dry_run) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 0)",
            (now, asset, side, quantity, price_usd, usd_value, reason),
        )
        conn.commit()


def _roll_day_start_if_needed(current_total_usd: float) -> float:
    """Lazily snapshots the portfolio's total value as the "start of day"
    baseline the first time it's checked on a new UTC calendar day, then
    returns whatever the current baseline is. Called from get_portfolio --
    not from risk.py's check_risk_limits -- specifically so the baseline gets
    set on the *first portfolio read of the day* (every agent turn starts
    with one) rather than only on the first risk check, which only happens
    once the agent already has a concrete trade in mind and could be well
    after an earlier same-day drop that would otherwise vanish from the
    baseline entirely (another real Qodo finding on the first cut). There's
    still no true midnight-UTC snapshot -- this is a paper wallet with no
    scheduler -- so a drop before the very first read of the day is still
    invisible; this only narrows that window, doesn't close it."""
    today = datetime.now(timezone.utc).date().isoformat()
    stored_date, stored_value = read_day_start()
    if stored_date != today:
        write_day_start(today, current_total_usd)
        # _safe_, not a raw call: this fires from inside get_portfolio, which
        # nearly everything else calls (execute_trade, check_risk_limits, a
        # plain portfolio read) -- an unguarded failure here would crash the
        # very first read of every new day, not just this one function.
        _safe_record_equity_snapshot(current_total_usd, "day_start")
        return current_total_usd
    return stored_value if stored_value is not None else current_total_usd


def _record_periodic_snapshot_if_due(current_total_usd: float) -> None:
    """Opportunistically appends an equity_snapshots row if it's been at
    least PERIODIC_SNAPSHOT_INTERVAL_SECONDS since the last one, checked
    lazily on every get_portfolio call -- same "no real scheduler" pattern
    as _roll_day_start_if_needed, just for a shorter interval. Without this,
    the equity curve only gets a point when a trade happens or the day
    rolls over, so a portfolio that moves purely from price drift between
    trades (or isn't traded for a while) leaves a gap in the drawdown/Sharpe
    curve as wide as that whole idle stretch. Piggybacks on whatever already
    calls get_portfolio -- an agent turn, a dashboard poll, a debug call --
    instead of a background thread or cron job, which this paper wallet has
    neither the need nor the process model for.

    Naturally self-throttling against the day-start snapshot: if that one
    just fired, the most recent row is a few milliseconds old, so this call
    sees elapsed well under the interval and skips -- no double-insert on
    the first read of a new day."""
    conn = db.get_conn()
    row = conn.execute(
        "SELECT timestamp FROM equity_snapshots ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if row is not None:
        last = datetime.fromisoformat(row["timestamp"])
        elapsed = (datetime.now(timezone.utc) - last).total_seconds()
        if elapsed < PERIODIC_SNAPSHOT_INTERVAL_SECONDS:
            return
    _safe_record_equity_snapshot(current_total_usd, "periodic")


def _price_usd(asset: str) -> dict:
    if asset in CRYPTO_ASSETS:
        return get_crypto_price(asset)
    if asset in NSE_TICKERS:
        return get_equity_price(asset)
    raise ValueError(f"Unknown tradable asset: {asset}")


def get_portfolio() -> dict:
    """Cash, every holding, current USD value of each, and portfolio total."""
    _ensure_seeded()
    conn = db.get_conn()
    rows = conn.execute("SELECT asset, quantity FROM holdings").fetchall()
    holdings_by_asset = {r["asset"]: r["quantity"] for r in rows}

    cash = holdings_by_asset.pop("CASH", 0.0)
    crypto_prices = get_crypto_prices(CRYPTO_ASSETS)

    positions = []
    total_usd = cash

    for asset in CRYPTO_ASSETS:
        quantity = holdings_by_asset.get(asset, 0.0)
        price = crypto_prices.get(asset, {}).get("price_usd")
        usd_value = quantity * price if price is not None else None
        if usd_value is not None:
            total_usd += usd_value
        positions.append({
            "asset": asset,
            "asset_class": "crypto",
            "quantity": quantity,
            "price_usd": price,
            "usd_value": usd_value,
            "change_24h_pct": crypto_prices.get(asset, {}).get("change_24h_pct"),
        })

    for asset in NSE_TICKERS:
        quantity = holdings_by_asset.get(asset, 0.0)
        try:
            quote = get_equity_price(asset)
        except Exception as exc:  # quote source down -- don't fail the whole portfolio
            positions.append({
                "asset": asset,
                "asset_class": "equity",
                "quantity": quantity,
                "price_usd": None,
                "usd_value": None,
                "change_24h_pct": None,
                "market_open": None,
                "error": str(exc),
            })
            continue
        usd_value = quantity * quote["price_usd"]
        total_usd += usd_value
        positions.append({
            "asset": asset,
            "asset_class": "equity",
            "quantity": quantity,
            "price_usd": quote["price_usd"],
            "price_inr": quote["price_inr"],
            "usd_value": usd_value,
            "change_24h_pct": quote["change_24h_pct"],
            "market_open": quote["market_open"],
        })

    day_start_value_usd = _roll_day_start_if_needed(total_usd)
    _record_periodic_snapshot_if_due(total_usd)

    return {
        "cash_usd": cash,
        "positions": positions,
        "total_usd": total_usd,
        "day_start_value_usd": day_start_value_usd,
        "dry_run": config.DRY_RUN,
    }


def get_transaction_log(limit: int = 50) -> list[dict]:
    """Most recent transactions, newest first. risk_snapshot is the
    check_risk_limits result computed at trade time (None for seed rows and
    for any trade made before this field existed), parsed back from JSON so
    a caller (or the self-audit subagent's sandbox backtests) can read the
    actual daily_drawdown/concentration/etc. numbers that were true at each
    decision, not just the free-text reason."""
    _ensure_seeded()
    conn = db.get_conn()
    rows = conn.execute(
        "SELECT id, timestamp, asset, side, quantity, price_usd, usd_value, reason, dry_run, risk_snapshot "
        "FROM transactions ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    results = []
    for r in rows:
        entry = dict(r)
        raw = entry.pop("risk_snapshot")
        entry["risk_snapshot"] = json.loads(raw) if raw else None
        results.append(entry)
    return results


def _safe_record_equity_snapshot(total_usd: float, reason: str) -> None:
    """record_equity_snapshot is best-effort observability, not part of the
    trade's own correctness -- a network hiccup fetching prices for the
    snapshot must never surface as a failed execute_trade after the trade
    (or its DRY_RUN log entry) has already committed. A caller that saw a
    failure here and retried the "failed" trade would double-execute it
    (a real Qodo finding)."""
    try:
        record_equity_snapshot(total_usd, reason)
    except Exception:
        pass


def execute_trade(
    asset: str,
    side: str,
    quantity: float | None = None,
    usd_amount: float | None = None,
    reason: str = "",
    risk_snapshot: dict | None = None,
    price_usd: float | None = None,
) -> dict:
    """The only tool that changes wallet state.

    Exactly one of quantity / usd_amount must be given. When DRY_RUN is on
    (the default), the trade is priced and logged with dry_run=1 but cash
    and holdings are left untouched.

    risk_snapshot is a check_risk_limits result computed by the caller (see
    server.py's execute_trade tool wrapper) for the *same* asset/side/
    quantity/usd_amount, stored alongside the transaction for the self-audit
    subagent's backtests. Not computed in here to avoid wallet.py importing
    risk.py (risk.py already imports wallet.py -- this module stays a leaf
    that only pricing/seed depend on, per its own module docstring).

    price_usd, if given, should be that same check_risk_limits call's price
    -- reused here instead of fetching a second, possibly different quote,
    so the stored risk_snapshot and the executed trade always agree on the
    price they describe (a real Qodo finding: two independent fetches could
    straddle a price move and disagree). Falls back to a fresh fetch if not
    given (e.g. a direct call with no risk_snapshot at all).
    """
    _ensure_seeded()

    asset = asset.upper()
    side = side.lower()
    if asset not in TRADABLE_ASSETS:
        raise ValueError(f"Unknown tradable asset: {asset}. Supported: {TRADABLE_ASSETS}")
    if side not in ("buy", "sell"):
        raise ValueError(f"side must be 'buy' or 'sell', got {side!r}")
    if (quantity is None) == (usd_amount is None):
        raise ValueError("Provide exactly one of quantity or usd_amount")

    amount: float = quantity if quantity is not None else usd_amount  # type: ignore[assignment]
    if not math.isfinite(amount) or amount <= 0:
        raise ValueError(f"quantity/usd_amount must be a finite positive number, got {amount}")

    if asset in NSE_TICKERS and not market_open():
        raise ValueError(
            f"NSE is closed (09:15-15:30 IST, weekdays). Cannot trade {asset} right now -- "
            "hold or monitor the existing position instead."
        )

    if price_usd is None:
        quote = _price_usd(asset)
        price_usd = float(quote["price_usd"])
    else:
        # A caller-supplied price (server.py passes through check_risk_limits'
        # own quote) skipped the amount validation above entirely -- it's a
        # separate value. Without this, a bad direct call (price_usd=0, NaN,
        # negative) would divide-by-zero or persist nonsensical transaction/
        # holding values, since this is the wallet's sole state-mutating
        # function and a caller isn't required to go through server.py.
        price_usd = float(price_usd)
        if not math.isfinite(price_usd) or price_usd <= 0:
            raise ValueError(f"price_usd must be a finite positive number, got {price_usd}")

    if quantity is None:
        assert usd_amount is not None
        quantity = usd_amount / price_usd
    quantity = float(quantity)
    usd_value = quantity * price_usd

    conn = db.get_conn()
    now = datetime.now(timezone.utc).isoformat()
    risk_snapshot_json = json.dumps(risk_snapshot) if risk_snapshot is not None else None

    if config.DRY_RUN:
        conn.execute(
            "INSERT INTO transactions "
            "(timestamp, asset, side, quantity, price_usd, usd_value, reason, dry_run, risk_snapshot) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)",
            (now, asset, side, quantity, price_usd, usd_value, reason, risk_snapshot_json),
        )
        conn.commit()
        _safe_record_equity_snapshot(get_portfolio()["total_usd"], f"trade:{asset}:{side}:dry_run")
        return {
            "dry_run": True,
            "executed": False,
            "asset": asset,
            "side": side,
            "quantity": quantity,
            "price_usd": price_usd,
            "usd_value": usd_value,
            "reason": reason,
            "message": "DRY_RUN is on: this trade was priced and logged but not executed.",
        }

    with _trade_lock:
        cash_row = conn.execute("SELECT quantity FROM holdings WHERE asset = 'CASH'").fetchone()
        cash = cash_row["quantity"] if cash_row else 0.0
        holding_row = conn.execute("SELECT quantity FROM holdings WHERE asset = ?", (asset,)).fetchone()
        holding_qty = holding_row["quantity"] if holding_row else 0.0

        if side == "buy":
            if usd_value > cash + 1e-9:
                raise ValueError(f"Insufficient cash: need ${usd_value:.2f}, have ${cash:.2f}")
            new_cash = cash - usd_value
            new_holding = holding_qty + quantity
        else:
            if quantity > holding_qty + 1e-9:
                raise ValueError(f"Insufficient {asset}: trying to sell {quantity}, hold {holding_qty}")
            new_cash = cash + usd_value
            new_holding = holding_qty - quantity

        conn.execute(
            "INSERT INTO holdings (asset, quantity) VALUES ('CASH', ?) "
            "ON CONFLICT(asset) DO UPDATE SET quantity = excluded.quantity",
            (new_cash,),
        )
        conn.execute(
            "INSERT INTO holdings (asset, quantity) VALUES (?, ?) "
            "ON CONFLICT(asset) DO UPDATE SET quantity = excluded.quantity",
            (asset, new_holding),
        )
        conn.execute(
            "INSERT INTO transactions "
            "(timestamp, asset, side, quantity, price_usd, usd_value, reason, dry_run, risk_snapshot) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)",
            (now, asset, side, quantity, price_usd, usd_value, reason, risk_snapshot_json),
        )
        conn.commit()
        # Recorded inside the same lock that serialized this trade's mutation
        # -- not after releasing it -- so a second concurrent trade can't
        # commit and snapshot first, which would insert equity_snapshots rows
        # out of true chronological order (a real Qodo finding; metrics.py
        # reads this table in insertion order).
        _safe_record_equity_snapshot(get_portfolio()["total_usd"], f"trade:{asset}:{side}:live")

    return {
        "dry_run": False,
        "executed": True,
        "asset": asset,
        "side": side,
        "quantity": quantity,
        "price_usd": price_usd,
        "usd_value": usd_value,
        "reason": reason,
        "cash_usd_after": new_cash,
        "holding_after": new_holding,
    }


def reset_wallet() -> dict:
    with _trade_lock:
        seed.reset_and_reseed()
    return get_portfolio()


def realized_pnl_and_cost_basis() -> tuple[list[float], dict[str, tuple[float, float]]]:
    """Walks the full *executed* (non-dry-run) transaction history in
    order, replaying running-average-cost-basis accounting per asset.
    Shared by risk.py (consecutive-loss streak) and metrics.py (realized +
    unrealized P&L) so both use the exact same accounting instead of two
    implementations drifting apart.

    Returns (realized P&L per sell, oldest first; final {asset:
    (remaining_qty, remaining_cost_basis_usd)} for every asset ever
    bought/seeded -- used to value open positions for unrealized P&L).

    Seed rows count toward cost basis (they record a real acquisition
    price) but aren't sales. DRY_RUN rows are excluded entirely -- they
    never touched holdings (see execute_trade), so counting them would let
    simulated trades fabricate realized losses/gains and corrupt the cost
    basis used for real sells, under the default DRY_RUN=true config."""
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

    return pnl_series, cost_basis
