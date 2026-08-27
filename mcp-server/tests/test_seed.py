import pytest

from app import seed, wallet


def test_seed_wallet_produces_target_allocation(isolated_db, mock_prices):
    seed.seed_wallet()
    portfolio = wallet.get_portfolio()

    assert portfolio["cash_usd"] == 5_000.0
    assert portfolio["total_usd"] == 10_000.0

    by_asset = {p["asset"]: p for p in portfolio["positions"]}
    # Crypto bucket is $3,000 total, 60/40 BTC/ETH
    assert by_asset["BTC"]["usd_value"] == pytest.approx(1_800.0)
    assert by_asset["ETH"]["usd_value"] == pytest.approx(1_200.0)
    # Equity bucket is $2,000 total, split equally across 4 tickers
    for symbol in ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]:
        assert by_asset[symbol]["usd_value"] == pytest.approx(500.0)


def test_seed_wallet_is_idempotent(isolated_db, mock_prices):
    seed.seed_wallet()
    first_log = wallet.get_transaction_log(limit=50)
    seed.seed_wallet()  # must no-op, not duplicate rows
    second_log = wallet.get_transaction_log(limit=50)
    assert len(first_log) == len(second_log)


def test_is_initialized_reflects_seed_state(isolated_db, mock_prices):
    assert seed.is_initialized() is False
    seed.seed_wallet()
    assert seed.is_initialized() is True


def test_reset_and_reseed_restores_target_allocation(seeded_wallet, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "DRY_RUN", False)
    wallet.execute_trade("BTC", "sell", quantity=0.001, price_usd=80_000.0)
    assert wallet.get_portfolio()["cash_usd"] != 5_000.0  # confirm the sell actually mutated state

    seed.reset_and_reseed()

    portfolio = wallet.get_portfolio()
    assert portfolio["cash_usd"] == 5_000.0
    assert len(wallet.get_transaction_log(limit=50)) == 7  # cash + 2 crypto + 4 equities
