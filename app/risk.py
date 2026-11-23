from dataclasses import dataclass
from datetime import date


@dataclass
class DailyProfitGuard:
    target_usdt: float = 10.0
    max_loss_usdt: float = 10.0
    trading_enabled: bool = False
    session_date: date | None = None
    realized_profit_usdt: float = 0.0

    def _reset_if_new_day(self, today: date) -> None:
        if self.session_date != today:
            self.session_date = today
            self.realized_profit_usdt = 0.0

    def record_trade(self, net_profit_usdt: float, today: date | None = None) -> None:
        current_date = today or date.today()
        self._reset_if_new_day(current_date)
        self.realized_profit_usdt += net_profit_usdt

    def can_open_trade(self, today: date | None = None) -> bool:
        current_date = today or date.today()
        self._reset_if_new_day(current_date)
        if not self.trading_enabled:
            return False
        return (
            self.realized_profit_usdt < self.target_usdt
            and self.realized_profit_usdt > -self.max_loss_usdt
        )

    @property
    def target_reached(self) -> bool:
        return self.realized_profit_usdt >= self.target_usdt

    @property
    def loss_limit_reached(self) -> bool:
        return self.realized_profit_usdt <= -self.max_loss_usdt
