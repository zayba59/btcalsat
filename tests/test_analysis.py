from app.analysis import calculate_metrics, signal_from_imbalance
from app.risk import DailyProfitGuard


def test_order_book_imbalance():
    metrics = calculate_metrics([["100", "3"]], [["101", "1"]])
    assert metrics.imbalance == 0.5
    assert metrics.spread == 1


def test_signal_is_not_probability():
    assert signal_from_imbalance(0.5) == ("LONG", 50)
    assert signal_from_imbalance(-0.5) == ("SHORT", 50)
    assert signal_from_imbalance(0.0) == ("BEKLE", 0)


def test_daily_profit_guard_stops_at_target():
    guard = DailyProfitGuard(target_usdt=10, max_loss_usdt=10, trading_enabled=True)
    guard.record_trade(6)
    assert guard.can_open_trade()
    guard.record_trade(4.01)
    assert guard.target_reached
    assert not guard.can_open_trade()


def test_daily_profit_guard_resets_on_new_day():
    from datetime import date, timedelta

    guard = DailyProfitGuard(target_usdt=10, max_loss_usdt=10, trading_enabled=True)
    day_one = date(2026, 1, 1)
    guard.record_trade(10, day_one)
    assert not guard.can_open_trade(day_one)
    assert guard.can_open_trade(day_one + timedelta(days=1))
