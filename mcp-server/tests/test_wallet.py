import threading
from datetime import datetime, timedelta, timezone

import pytest

from app import config, db, wallet


# --- Input validation -------------------------------------------------

def test_rejects_unknown_asset(seeded_wallet):
    with pytest.raises(ValueError, match="Unknown tradable asset"):
        wallet.execute_trade("DOGE", "buy", usd_amount=100)


def test_rejects_invalid_side(seeded_wallet):
    with pytest.raises(ValueError, match="side must be"):
        wallet.execute_trade("BTC", "hold", usd_amount=100)


def test_rejects_both_quantity_and_usd_amount(seeded_wallet):
    with pytest.raises(ValueError, match="exactly one"):
        wallet.execute_trade("BTC", "buy", quantity=1, usd_amount=100)


def test_rejects_neither_quantity_nor_usd_amount(seeded_wallet):
    with pytest.raises(ValueError, match="exactly one"):
        wallet.execute_trade("BTC", "buy")


@pytest.mark.parametrize("bad_amount", [0, -50, float("nan"), float("inf")])
def test_rejects_invalid_usd_amount(seeded_wallet, bad_amount):
    with pytest.raises(ValueError, match="finite positive"):
        wallet.execute_trade("BTC", "buy", usd_amount=bad_amount)


@pytest.mark.parametrize("bad_price", [0, -1, float("nan"), float("inf")])
def test_rejects_invalid_caller_supplied_price(seeded_wallet, bad_price):
    with pytest.raises(ValueError, match="price_usd must be"):
        wallet.execute_trade("BTC", "buy", usd_amount=100, price_usd=bad_price)


def test_rejects_equity_trade_while_market_closed(seeded_wallet, monkeypatch):
    monkeypatch.setattr(wallet, "market_open", lambda: False)
    with pytest.raises(ValueError, match="NSE is closed"):
        wallet.execute_trade("RELIANCE.NS", "buy", usd_amount=100)


# --- DRY_RUN behavior (the default) ------------------------------------

def test_dry_run_logs_without_mutating_state(seeded_wallet):
    before = wallet.get_portfolio()
    result = wallet.execute_trade("BTC", "buy", usd_amount=500, reason="test")

    assert result["dry_run"] is True
    assert result["executed"] is False

    after = wallet.get_portfolio()
    assert after["cash_usd"] == before["cash_usd"]
    by_asset_before = {p["asset"]: p["quantity"] for p in before["positions"]}
    by_asset_after = {p["asset"]: p["quantity"] for p in after["positions"]}
    assert by_asset_before["BTC"] == by_asset_after["BTC"]


def test_dry_run_reuses_supplied_price_instead_of_refetching(seeded_wallet):
    # 80_000 differs from conftest's mocked live BTC price -- if execute_trade
    # ignored the supplied price and fetched its own, this would fail.
    result = wallet.execute_trade("BTC", "buy", usd_amount=800, price_usd=80_000.0)
    assert result["price_usd"] == 80_000.0
    assert result["quantity"] == pytest.approx(800.0 / 80_000.0)


def test_risk_snapshot_stored_and_roundtrips(seeded_wallet):
    snapshot = {"any_breach": True, "triggers": {"daily_drawdown": {"breached": True}}}
    wallet.execute_trade("BTC", "buy", usd_amount=100, risk_snapshot=snapshot)
    log = wallet.get_transaction_log(limit=1)
    assert log[0]["risk_snapshot"] == snapshot


def test_transaction_log_risk_snapshot_is_none_when_not_given(seeded_wallet):
    wallet.execute_trade("BTC", "buy", usd_amount=100)
    log = wallet.get_transaction_log(limit=1)
    assert log[0]["risk_snapshot"] is None


# --- Live trading (DRY_RUN=false) ---------------------------------------
# live_trading fixture lives in conftest.py -- shared with test_risk.py.

def test_live_buy_moves_cash_to_holding(seeded_wallet, live_trading):
    before = wallet.get_portfolio()
    cash_before = before["cash_usd"]
    btc_before = next(p["quantity"] for p in before["positions"] if p["asset"] == "BTC")

    result = wallet.execute_trade("BTC", "buy", usd_amount=500, price_usd=80_000.0)

    assert result["executed"] is True
    after = wallet.get_portfolio()
    assert after["cash_usd"] == pytest.approx(cash_before - 500)
    btc_after = next(p["quantity"] for p in after["positions"] if p["asset"] == "BTC")
    assert btc_after == pytest.approx(btc_before + 500 / 80_000.0)


def test_live_sell_moves_holding_to_cash(seeded_wallet, live_trading):
    before = wallet.get_portfolio()
    btc_before = next(p["quantity"] for p in before["positions"] if p["asset"] == "BTC")
    sell_qty = btc_before / 2

    wallet.execute_trade("BTC", "sell", quantity=sell_qty, price_usd=80_000.0)

    after = wallet.get_portfolio()
    btc_after = next(p["quantity"] for p in after["positions"] if p["asset"] == "BTC")
    assert btc_after == pytest.approx(btc_before - sell_qty)
    assert after["cash_usd"] == pytest.approx(before["cash_usd"] + sell_qty * 80_000.0)


def test_live_buy_rejects_insufficient_cash(seeded_wallet, live_trading):
    before = wallet.get_portfolio()
    with pytest.raises(ValueError, match="Insufficient cash"):
        wallet.execute_trade("BTC", "buy", usd_amount=before["cash_usd"] * 10, price_usd=80_000.0)
    # Rejected trades must not partially mutate state.
    assert wallet.get_portfolio()["cash_usd"] == before["cash_usd"]


def test_live_sell_rejects_insufficient_holding(seeded_wallet, live_trading):
    before = wallet.get_portfolio()
    btc_before = next(p["quantity"] for p in before["positions"] if p["asset"] == "BTC")
    with pytest.raises(ValueError, match="Insufficient BTC"):
        wallet.execute_trade("BTC", "sell", quantity=btc_before * 10, price_usd=80_000.0)
    after = wallet.get_portfolio()
    assert next(p["quantity"] for p in after["positions"] if p["asset"] == "BTC") == btc_before


def test_live_trade_records_an_equity_snapshot(seeded_wallet, live_trading):
    from app import db

    wallet.get_portfolio()  # warm up day-start rollover first -- it snapshots too
    before_count = isolated_count(db)
    wallet.execute_trade("BTC", "buy", usd_amount=100, price_usd=80_000.0)
    assert isolated_count(db) == before_count + 1


def test_dry_run_trade_also_records_an_equity_snapshot(seeded_wallet):
    from app import db

    wallet.get_portfolio()  # warm up day-start rollover first -- it snapshots too
    before_count = isolated_count(db)
    wallet.execute_trade("BTC", "buy", usd_amount=100)
    assert isolated_count(db) == before_count + 1


def test_first_trade_of_the_day_records_two_snapshots(seeded_wallet):
    # Day-start rollover snapshots once (lazily, on the first portfolio read
    # of a new day) and the trade itself snapshots again -- both real,
    # documented behavior, not double-counting.
    from app import db

    assert isolated_count(db) == 0
    wallet.execute_trade("BTC", "buy", usd_amount=100)
    assert isolated_count(db) == 2


def test_equity_snapshot_failure_does_not_fail_the_trade(seeded_wallet, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("simulated network failure")

    monkeypatch.setattr(wallet, "record_equity_snapshot", boom)
    # Covers both call sites: the day-start rollover (inside get_portfolio,
    # the first call of the test) and execute_trade's own trade-completion
    # snapshot -- neither may crash the trade.
    result = wallet.execute_trade("BTC", "buy", usd_amount=100)
    assert result["dry_run"] is True  # did not raise


def isolated_count(db_module) -> int:
    return db_module.get_conn().execute("SELECT COUNT(*) FROM equity_snapshots").fetchone()[0]


# --- Debug-only state mutation primitives ---------------------------------
# Used by risk.py's force_* helpers (test_risk.py) to put the wallet in a
# specific state on demand for a demo.

def test_set_holding_quantity_overwrites_without_touching_cash(seeded_wallet):
    before_cash = wallet.get_portfolio()["cash_usd"]
    wallet.set_holding_quantity("BTC", 12.5)
    after = wallet.get_portfolio()
    btc = next(p["quantity"] for p in after["positions"] if p["asset"] == "BTC")
    assert btc == pytest.approx(12.5)
    assert after["cash_usd"] == pytest.approx(before_cash)


def test_set_holding_quantity_creates_a_holding_row_for_a_new_asset(isolated_db):
    # Queries the holdings table directly, not via get_portfolio -- a
    # get_portfolio call would trigger _ensure_seeded on this never-seeded
    # db and overwrite this with the seed's own target quantity.
    wallet.set_holding_quantity("ETH", 3.0)
    row = isolated_db.execute("SELECT quantity FROM holdings WHERE asset = 'ETH'").fetchone()
    assert row["quantity"] == pytest.approx(3.0)


def test_record_synthetic_transactions_does_not_touch_holdings(seeded_wallet):
    before = wallet.get_portfolio()
    holdings_before = {p["asset"]: p["quantity"] for p in before["positions"]}

    wallet.record_synthetic_transactions([("DEMO_LOSS", "sell", 0.01, 50.0, "test")])

    log = wallet.get_transaction_log(limit=1)
    assert log[0]["asset"] == "DEMO_LOSS"
    assert log[0]["side"] == "sell"
    assert log[0]["dry_run"] == 0

    after = wallet.get_portfolio()
    holdings_after = {p["asset"]: p["quantity"] for p in after["positions"]}
    assert holdings_before == holdings_after


def test_record_synthetic_transactions_writes_multiple_rows(seeded_wallet):
    wallet.record_synthetic_transactions([
        ("DEMO_LOSS", "buy", 0.02, 100.0, "test"),
        ("DEMO_LOSS", "sell", 0.01, 50.0, "test"),
        ("DEMO_LOSS", "sell", 0.01, 50.0, "test"),
    ])
    log = wallet.get_transaction_log(limit=3)
    assert [entry["side"] for entry in reversed(log)] == ["buy", "sell", "sell"]


# --- Day-start baseline --------------------------------------------------

def test_day_start_established_on_first_read(isolated_db, mock_prices):
    date_before, value_before = wallet.read_day_start()
    assert date_before is None and value_before is None

    portfolio = wallet.get_portfolio()  # triggers _ensure_seeded + rollover

    date_after, value_after = wallet.read_day_start()
    assert date_after is not None
    assert value_after == portfolio["total_usd"]


def test_day_start_stable_within_the_same_day(seeded_wallet, live_trading):
    first = wallet.get_portfolio()["day_start_value_usd"]
    wallet.execute_trade("BTC", "buy", usd_amount=100, price_usd=80_000.0)
    second = wallet.get_portfolio()["day_start_value_usd"]
    assert first == second  # a trade moving the total must not move the baseline


def test_write_and_read_day_start_roundtrip(isolated_db):
    wallet.write_day_start("2026-08-27", 12_345.67)
    date, value = wallet.read_day_start()
    assert date == "2026-08-27"
    assert value == 12_345.67


def test_day_start_rollover_is_thread_safe(tmp_path, monkeypatch):
    # The /ui/* routes run get_portfolio concurrently in FastAPI's
    # threadpool (see server.py's module docstring) -- on the first read of
    # a new UTC day, several real OS threads could each see the stale
    # stored date before any of them writes, each recording its own
    # duplicate "day_start" snapshot, without _day_start_lock serializing
    # the read-check-write sequence.
    #
    # A single shared sqlite3.Connection (the isolated_db fixture's usual
    # model) isn't safe for genuinely concurrent use even with
    # check_same_thread=False -- Python's sqlite3 module itself isn't
    # thread-safe for concurrent statement execution on one Connection
    # object, which produced a spurious sqlite3.InterfaceError unrelated to
    # the lock this test actually exercises. Giving each thread its own
    # connection to the same file matches how db.get_conn() really behaves
    # in production (threading.local(), one connection per thread).
    import sqlite3

    from conftest import _crypto_price, _crypto_prices, _equity_price
    from app import db, seed as seed_module

    db_path = tmp_path / "thread_test.db"
    local = threading.local()

    def get_conn():
        conn = getattr(local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(db.SCHEMA)
            conn.commit()
            db._run_migrations(conn)
            local.conn = conn
        return conn

    monkeypatch.setattr(db, "get_conn", get_conn)
    monkeypatch.setattr(wallet, "get_crypto_price", _crypto_price)
    monkeypatch.setattr(wallet, "get_crypto_prices", _crypto_prices)
    monkeypatch.setattr(wallet, "get_equity_price", _equity_price)
    monkeypatch.setattr(wallet, "market_open", lambda: True)
    monkeypatch.setattr(seed_module, "get_crypto_prices", _crypto_prices)
    monkeypatch.setattr(seed_module, "get_equity_price", _equity_price)

    wallet._ensure_seeded()  # seed once, single-threaded, before racing --
    # isolates the (already-tested, already-locked) seeding race from the
    # day-start race this test targets. day_start itself is still unset.

    barrier = threading.Barrier(6)
    errors = []

    def worker():
        try:
            barrier.wait()  # all six threads hit the rollover check together
            wallet.get_portfolio()
        except Exception as exc:  # pragma: no cover - surfaced via `errors`
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"worker thread(s) raised: {errors}"

    day_start_snapshots = get_conn().execute(
        "SELECT COUNT(*) FROM equity_snapshots WHERE reason = 'day_start'"
    ).fetchone()[0]
    assert day_start_snapshots == 1


# --- Realized P&L / cost basis -------------------------------------------
# clean_btc_cost_basis fixture lives in conftest.py -- sells the seeded BTC
# position first (at its own seed price, contributing an exact-zero P&L
# entry) so tests below can reason about a clean cost basis.

def test_realized_pnl_excludes_dry_run_trades(clean_btc_cost_basis, monkeypatch):
    # Real loss: sell at a lower price than the live-trading buy above it.
    wallet.execute_trade("BTC", "buy", quantity=1.0, price_usd=100.0)
    wallet.execute_trade("BTC", "sell", quantity=1.0, price_usd=90.0)  # real loss: -10

    # Now a DRY_RUN "win" that must NOT show up in realized P&L.
    monkeypatch.setattr(config, "DRY_RUN", True)
    wallet.execute_trade("BTC", "sell", quantity=0.001, price_usd=999_999.0)

    pnl_series, _ = wallet.realized_pnl_and_cost_basis()
    assert pnl_series == [pytest.approx(0.0), pytest.approx(-10.0)]


def test_realized_pnl_uses_average_cost_basis(clean_btc_cost_basis):
    wallet.execute_trade("BTC", "buy", quantity=1.0, price_usd=100.0)
    wallet.execute_trade("BTC", "buy", quantity=1.0, price_usd=120.0)  # avg cost now 110
    wallet.execute_trade("BTC", "sell", quantity=0.5, price_usd=90.0)  # (90-110)*0.5 = -10
    wallet.execute_trade("BTC", "sell", quantity=0.5, price_usd=200.0)  # (200-110)*0.5 = +45

    pnl_series, cost_basis = wallet.realized_pnl_and_cost_basis()
    assert pnl_series == [pytest.approx(0.0), pytest.approx(-10.0), pytest.approx(45.0)]
    remaining_qty, remaining_cost = cost_basis["BTC"]
    assert remaining_qty == pytest.approx(1.0)  # 2 bought - 1 sold, from a cleared position


# --- Periodic equity snapshot ---------------------------------------------

def _backdate_latest_snapshot(seconds_ago: float) -> None:
    conn = db.get_conn()
    stale = (datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)).isoformat()
    conn.execute(
        "UPDATE equity_snapshots SET timestamp = ? WHERE id = (SELECT MAX(id) FROM equity_snapshots)",
        (stale,),
    )
    conn.commit()


def test_periodic_snapshot_recorded_when_stale(isolated_db, mock_prices):
    wallet.get_portfolio()  # seeds + day-start rollover -- one snapshot already
    _backdate_latest_snapshot(wallet.PERIODIC_SNAPSHOT_INTERVAL_SECONDS + 1)
    before = isolated_count(db)

    wallet.get_portfolio()

    after = isolated_count(db)
    assert after == before + 1
    latest_reason = isolated_db.execute(
        "SELECT reason FROM equity_snapshots ORDER BY id DESC LIMIT 1"
    ).fetchone()["reason"]
    assert latest_reason == "periodic"


def test_periodic_snapshot_not_recorded_when_recent(isolated_db, mock_prices):
    wallet.get_portfolio()  # seeds + day-start rollover -- one snapshot already
    before = isolated_count(db)

    wallet.get_portfolio()  # only a moment later -- well under the interval

    after = isolated_count(db)
    assert after == before


def test_periodic_snapshot_does_not_double_up_with_day_start_snapshot(isolated_db, mock_prices):
    # First-ever get_portfolio call on a fresh wallet: day-start rollover
    # fires its own snapshot, and the periodic check runs immediately after
    # in the same call -- must see that snapshot as "just happened" and
    # skip, not add a second row.
    wallet.get_portfolio()
    assert isolated_count(db) == 1


def _flaky_equity_price(symbol: str) -> dict:
    if symbol == "TCS.NS":
        raise RuntimeError("simulated quote outage")
    price_inr = {"RELIANCE.NS": 2_500.0, "INFY.NS": 1_500.0, "HDFCBANK.NS": 1_600.0}[symbol]
    return {
        "symbol": symbol,
        "price_inr": price_inr,
        "price_usd": price_inr / 83.0,
        "change_24h_pct": 0.0,
        "market_open": True,
        "source": "mock",
    }


def test_safe_record_equity_snapshot_skips_when_any_position_unpriced(isolated_db):
    positions = [
        {"asset": "BTC", "price_usd": 80_000.0},
        {"asset": "TCS.NS", "price_usd": None},
    ]
    wallet._safe_record_equity_snapshot(10_000.0, "test", positions)
    assert isolated_count(db) == 0


def test_periodic_snapshot_skipped_when_a_position_is_unpriced(isolated_db, mock_prices, monkeypatch):
    # A stored snapshot outlives the outage that produced it -- total_usd
    # silently excludes an unpriced position's value (see get_portfolio), so
    # recording it as-is would permanently understate the equity curve even
    # after the quote source recovers.
    wallet.get_portfolio()  # seeds + day-start rollover -- one snapshot already
    _backdate_latest_snapshot(wallet.PERIODIC_SNAPSHOT_INTERVAL_SECONDS + 1)
    before = isolated_count(db)

    monkeypatch.setattr(wallet, "get_equity_price", _flaky_equity_price)
    wallet.get_portfolio()  # due for a periodic snapshot, but TCS.NS is unpriced

    assert isolated_count(db) == before
