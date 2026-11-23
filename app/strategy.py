from dataclasses import dataclass


def ema(values: list[float], period: int) -> float:
    if len(values) < period:
        raise ValueError("EMA için yeterli veri yok")
    multiplier = 2 / (period + 1)
    result = sum(values[:period]) / period
    for value in values[period:]:
        result = (value - result) * multiplier + result
    return result


def rsi(values: list[float], period: int = 14) -> float:
    if len(values) < period + 1:
        raise ValueError("RSI için yeterli veri yok")
    gains = []
    losses = []
    for previous, current in zip(values[-period - 1:-1], values[-period:]):
        change = current - previous
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))
    average_gain = sum(gains) / period
    average_loss = sum(losses) / period
    if average_loss == 0:
        return 100.0
    return 100 - (100 / (1 + average_gain / average_loss))


@dataclass(frozen=True)
class Signal:
    action: str
    reason: str
    fast_ema: float
    slow_ema: float
    rsi: float


def generate_signal(
    closes: list[float],
    in_position: bool,
    fast_period: int = 9,
    slow_period: int = 21,
    rsi_period: int = 14,
) -> Signal:
    fast = ema(closes, fast_period)
    slow = ema(closes, slow_period)
    strength = rsi(closes, rsi_period)
    if not in_position and fast > slow and 50 <= strength <= 70:
        return Signal("BUY", "EMA9 > EMA21 ve RSI 50-70", fast, slow, strength)
    if in_position and (fast < slow or strength >= 75 or strength <= 35):
        return Signal("SELL", "Trend/RSI çıkış koşulu", fast, slow, strength)
    return Signal("HOLD", "Koşul oluşmadı", fast, slow, strength)
