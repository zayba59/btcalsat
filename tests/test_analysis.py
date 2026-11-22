from app.analysis import calculate_metrics, signal_from_imbalance


def test_order_book_imbalance():
    metrics = calculate_metrics([["100", "3"]], [["101", "1"]])
    assert metrics.imbalance == 0.5
    assert metrics.spread == 1


def test_signal_is_not_probability():
    assert signal_from_imbalance(0.5) == ("LONG", 50)
    assert signal_from_imbalance(-0.5) == ("SHORT", 50)
    assert signal_from_imbalance(0.0) == ("BEKLE", 0)
