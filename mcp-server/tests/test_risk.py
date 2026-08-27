import pytest

from app import risk, wallet

# live_trading and clean_btc_cost_basis fixtures live in conftest.py --
# shared with test_wallet.py.


# --- Individual triggers --------------------------------------------------

def test_no_breach_for_a_small_ordinary_trade(seeded_wallet):
    result = risk.check_risk_limits("BTC", "buy", usd_amount=50)
    assert result["any_breach"] is False
    assert result["triggers"]["daily_drawdown"]["breached"] is False
    assert result["triggers"]["concentration"]["breached"] is False
    assert result["triggers"]["sell_all"]["breached"] is False
    assert result["triggers"]["consecutive_losses"]["breached"] is False


def test_concentration_breach(seeded_wallet):
    # Seeded BTC is ~$1,800 of a $10,000 portfolio (18%); buying enough to
    # push it past 50% must trip the trigger.
    result = risk.check_risk_limits("BTC", "buy", usd_amount=4_000)
    assert result["triggers"]["concentration"]["breached"] is True
    assert result["triggers"]["concentration"]["projected_pct"] > 50.0
    assert result["any_breach"] is True


def test_sell_all_breach(seeded_wallet):
    btc_qty = next(p["quantity"] for p in wallet.get_portfolio()["positions"] if p["asset"] == "BTC")
    result = risk.check_risk_limits("BTC", "sell", quantity=btc_qty)
    assert result["triggers"]["sell_all"]["breached"] is True
    assert result["any_breach"] is True


def test_selling_most_but_not_all_does_not_trip_sell_all(seeded_wallet):
    btc_qty = next(p["quantity"] for p in wallet.get_portfolio()["positions"] if p["asset"] == "BTC")
    result = risk.check_risk_limits("BTC", "sell", quantity=btc_qty * 0.5)
    assert result["triggers"]["sell_all"]["breached"] is False


def test_daily_drawdown_breach_via_force_trigger(seeded_wallet):
    risk.force_daily_drawdown_breach()
    result = risk.check_risk_limits("BTC", "buy", usd_amount=50)
    assert result["triggers"]["daily_drawdown"]["breached"] is True
    assert result["triggers"]["daily_drawdown"]["current_pct"] >= 5.0
    assert result["any_breach"] is True
    assert result["recommend_sandbox_stress_test"] is True


def test_force_daily_drawdown_breach_margin(seeded_wallet):
    result = risk.force_daily_drawdown_breach(margin_pct=2.0)
    assert result["synthetic_drawdown_pct"] == pytest.approx(7.0)
    assert result["forced"] is True


def test_consecutive_losses_breach(seeded_wallet, live_trading):
    # Three real losing sells in a row (avg cost 100, sold below it each time).
    wallet.execute_trade("BTC", "buy", quantity=3.0, price_usd=100.0)
    for _ in range(3):
        wallet.execute_trade("BTC", "sell", quantity=1.0, price_usd=50.0)

    result = risk.check_risk_limits("ETH", "buy", usd_amount=50)
    assert result["triggers"]["consecutive_losses"]["streak"] == 3
    assert result["triggers"]["consecutive_losses"]["breached"] is True
    assert result["any_breach"] is True


def test_consecutive_losses_resets_on_a_win(clean_btc_cost_basis):
    # clean_btc_cost_basis's own clearing sell is itself a zero-P&L entry
    # (neither win nor loss), so the streak below is unaffected by it.
    wallet.execute_trade("BTC", "buy", quantity=3.0, price_usd=100.0)
    wallet.execute_trade("BTC", "sell", quantity=1.0, price_usd=50.0)   # loss
    wallet.execute_trade("BTC", "sell", quantity=1.0, price_usd=50.0)   # loss
    wallet.execute_trade("BTC", "sell", quantity=1.0, price_usd=500.0)  # win -- resets streak

    result = risk.check_risk_limits("ETH", "buy", usd_amount=50)
    assert result["triggers"]["consecutive_losses"]["streak"] == 0
    assert result["triggers"]["consecutive_losses"]["breached"] is False


# --- Validation ------------------------------------------------------------

def test_check_risk_limits_exposes_price_usd(seeded_wallet):
    result = risk.check_risk_limits("BTC", "buy", usd_amount=100)
    assert result["price_usd"] == pytest.approx(80_000.0)  # conftest's mocked BTC price


@pytest.mark.parametrize("bad_amount", [0, -50, float("nan"), float("inf")])
def test_rejects_invalid_amount(seeded_wallet, bad_amount):
    with pytest.raises(ValueError, match="finite positive"):
        risk.check_risk_limits("BTC", "buy", usd_amount=bad_amount)


def test_rejects_unknown_asset(seeded_wallet):
    with pytest.raises(ValueError, match="Unknown tradable asset"):
        risk.check_risk_limits("DOGE", "buy", usd_amount=100)


def test_refuses_to_compute_with_an_unpriced_position(seeded_wallet, monkeypatch):
    # get_portfolio catches per-symbol quote errors and reports price_usd=None
    # for that position rather than failing the whole read -- check_risk_limits
    # must refuse to compute risk on that partial data, not silently proceed.
    def flaky_equity_price(symbol):
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

    monkeypatch.setattr(wallet, "get_equity_price", flaky_equity_price)
    with pytest.raises(ValueError, match="no live quote"):
        risk.check_risk_limits("BTC", "buy", usd_amount=100)
