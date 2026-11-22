from dataclasses import dataclass


@dataclass(frozen=True)
class OrderBookMetrics:
    bid_volume: float
    ask_volume: float
    imbalance: float
    spread: float


def calculate_metrics(bids: list[list[str]], asks: list[list[str]], levels: int = 10) -> OrderBookMetrics:
    bid_rows = bids[:levels]
    ask_rows = asks[:levels]
    bid_volume = sum(float(row[1]) for row in bid_rows)
    ask_volume = sum(float(row[1]) for row in ask_rows)
    total = bid_volume + ask_volume
    imbalance = (bid_volume - ask_volume) / total if total else 0.0
    spread = float(asks[0][0]) - float(bids[0][0]) if bids and asks else 0.0
    return OrderBookMetrics(bid_volume, ask_volume, imbalance, spread)


def signal_from_imbalance(imbalance: float) -> tuple[str, int]:
    score = round(min(abs(imbalance), 1.0) * 100)
    if imbalance >= 0.2:
        return "LONG", score
    if imbalance <= -0.2:
        return "SHORT", score
    return "BEKLE", score
