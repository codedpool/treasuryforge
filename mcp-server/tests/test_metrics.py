import pytest

from app import metrics, wallet


# --- max_drawdown_pct -------------------------------------------------

def test_max_drawdown_known_curve():
    # peak 10500, trough 9500 -> (10500-9500)/10500 = 9.524%
    series = [10_000, 10_500, 9_800, 10_100, 9_500, 9_900]
    assert metrics.max_drawdown_pct(series) == pytest.approx(9.524, abs=1e-3)


def test_max_drawdown_monotonically_rising_series_is_zero():
    assert metrics.max_drawdown_pct([100, 200, 300]) == 0.0


def test_max_drawdown_empty_series_is_none():
    assert metrics.max_drawdown_pct([]) is None


# --- sharpe_ratio -------------------------------------------------------

def test_sharpe_needs_at_least_three_points():
    assert metrics.sharpe_ratio([100, 110]) is None  # only 1 return observation
    assert metrics.sharpe_ratio([100, 110, 90]) is not None  # 2 varying observations, computable


def test_sharpe_zero_variance_is_none():
    # Constant % returns each step -> zero stdev -> undefined Sharpe, not
    # a division-by-zero crash.
    assert metrics.sharpe_ratio([100, 110, 121, 133.1]) is None


def test_sharpe_is_unannualized_mean_over_stdev():
    import statistics

    series = [100, 110, 90, 120]
    returns = [(110 - 100) / 100, (90 - 110) / 110, (120 - 90) / 90]
    expected = statistics.mean(returns) / statistics.stdev(returns)
    # sharpe_ratio rounds to 4 decimal places -- match that granularity
    # rather than asserting exact-float equality against an unrounded value.
    assert metrics.sharpe_ratio(series) == pytest.approx(expected, abs=1e-4)


# --- get_wallet_metrics integration -------------------------------------

def test_get_wallet_metrics_on_a_fresh_wallet(seeded_wallet):
    result = metrics.get_wallet_metrics()
    assert result["realized_pnl_usd"] == 0.0
    assert result["closed_trades"] == 0
    assert result["win_rate"] is None
    assert result["current_total_usd"] == pytest.approx(10_000.0)


def test_get_wallet_metrics_reflects_realized_trades(clean_btc_cost_basis):
    wallet.execute_trade("BTC", "buy", quantity=1.0, price_usd=100.0)
    wallet.execute_trade("BTC", "sell", quantity=1.0, price_usd=150.0)  # +50 win

    result = metrics.get_wallet_metrics()
    assert result["realized_pnl_usd"] == pytest.approx(50.0)
    assert result["closed_trades"] == 2  # the clearing sell (0.0) + this one
    assert result["win_rate"] == pytest.approx(0.5)  # one zero (not a win), one win


def test_get_wallet_metrics_win_rate_all_wins(clean_btc_cost_basis):
    wallet.execute_trade("BTC", "buy", quantity=1.0, price_usd=100.0)
    wallet.execute_trade("BTC", "sell", quantity=1.0, price_usd=150.0)  # win

    pnl_series, _ = wallet.realized_pnl_and_cost_basis()
    wins = sum(1 for p in pnl_series if p > 0)
    result = metrics.get_wallet_metrics()
    assert result["win_rate"] == pytest.approx(wins / len(pnl_series))


# --- get_equity_curve -------------------------------------------------

def test_equity_curve_has_timestamps_and_a_trailing_now_point(seeded_wallet):
    wallet.get_portfolio()  # records at least one snapshot (day-start rollover)
    curve = metrics.get_equity_curve()

    assert len(curve) >= 1
    for point in curve:
        assert "timestamp" in point and "total_usd" in point and "reason" in point
    assert curve[-1]["reason"] == "now"


def test_equity_curve_values_match_the_bare_series(seeded_wallet):
    wallet.get_portfolio()
    curve = metrics.get_equity_curve()
    bare = metrics._equity_series()
    assert [p["total_usd"] for p in curve] == bare
