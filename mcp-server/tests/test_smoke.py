"""Fixture sanity check -- if this fails, nothing else will pass either."""

from app import seed, wallet


def test_seeded_wallet_has_target_allocation(seeded_wallet):
    portfolio = wallet.get_portfolio()
    assert portfolio["cash_usd"] == 5_000.0
    assert portfolio["total_usd"] == 10_000.0


def test_isolated_db_does_not_leak_between_tests(isolated_db, mock_prices):
    # Each test gets its own tmp_path database -- if fixtures leaked state
    # between tests, this one (which never seeds) would see the previous
    # test's seeded wallet instead of a genuinely empty one.
    assert seed.is_initialized() is False
    assert isolated_db.execute("SELECT COUNT(*) FROM transactions").fetchone()[0] == 0
