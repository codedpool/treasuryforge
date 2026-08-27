"""market_open is a pure function of a datetime -- no fixtures, no mocking,
no network. get_equity_price itself (which does hit the network) isn't
tested here; wallet/risk tests exercise it through the mock_prices fixture
instead."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.pricing_equity import market_open

IST = ZoneInfo("Asia/Kolkata")


def test_open_during_regular_hours():
    # Wednesday 2026-08-19, 12:00 IST
    assert market_open(datetime(2026, 8, 19, 12, 0, tzinfo=IST)) is True


def test_closed_before_open():
    assert market_open(datetime(2026, 8, 19, 9, 0, tzinfo=IST)) is False


def test_closed_after_close():
    assert market_open(datetime(2026, 8, 19, 15, 31, tzinfo=IST)) is False


def test_open_at_exact_boundaries():
    assert market_open(datetime(2026, 8, 19, 9, 15, tzinfo=IST)) is True
    assert market_open(datetime(2026, 8, 19, 15, 30, tzinfo=IST)) is True


def test_closed_on_saturday():
    # 2026-08-22 is a Saturday
    assert market_open(datetime(2026, 8, 22, 12, 0, tzinfo=IST)) is False


def test_closed_on_sunday():
    # 2026-08-23 is a Sunday
    assert market_open(datetime(2026, 8, 23, 12, 0, tzinfo=IST)) is False
