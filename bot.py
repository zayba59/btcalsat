import argparse
import json
import time
from datetime import date, datetime
from pathlib import Path

import yaml

from app.risk import DailyProfitGuard
from app.spot_client import BinanceSpotClient
from app.strategy import generate_signal
from app.analysis import calculate_metrics


ROOT = Path(__file__).resolve().parent
SELECTED_SYMBOL_FILE = ROOT / "data" / "selected_symbol.txt"


def load_config() -> dict:
    with (ROOT / "config.yaml").open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def filled_values(order: dict) -> tuple[float, float]:
    quantity = float(order.get("executedQty", 0))
    quote = float(order.get("cummulativeQuoteQty", 0))
    return quantity, quote


def selected_symbol(default: str) -> str:
    if SELECTED_SYMBOL_FILE.exists():
        value = SELECTED_SYMBOL_FILE.read_text(encoding="utf-8").strip().upper()
        if value:
            return value
    return default


def local_today() -> date:
    from zoneinfo import ZoneInfo

    return datetime.now(ZoneInfo("Europe/Istanbul")).date()


def run(dry_run: bool, requested_symbol: str | None = None) -> None:
    config = load_config()
    simulation = config["simulation"]
    market = config["market"]
    symbol = (requested_symbol or selected_symbol(market["default_symbol"])).upper()
    client = BinanceSpotClient(testnet=simulation.get("testnet", True))
    guard = DailyProfitGuard(
        target_usdt=float(simulation["target_net_profit_usdt"]),
        max_loss_usdt=float(simulation["max_daily_loss_usdt"]),
        trading_enabled=dry_run or bool(simulation.get("trading_enabled", False)),
    )
    position: dict | None = None
    fee_rate = float(simulation.get("fee_rate", 0.001))
    take_profit = float(simulation.get("take_profit_pct", 0.008))
    stop_loss = float(simulation.get("stop_loss_pct", 0.004))
    quote_amount = float(simulation.get("order_quote_usdt", simulation["collateral_usdt"]))
    candle_interval = str(simulation.get("candle_interval", "5m"))
    higher_interval = str(simulation.get("higher_interval", "15m"))
    poll_seconds = int(simulation.get("poll_seconds", 15))
    fast_period = int(simulation.get("ema_fast_period", 9))
    slow_period = int(simulation.get("ema_slow_period", 21))
    rsi_period = int(simulation.get("rsi_period", 14))
    min_imbalance = float(simulation.get("min_imbalance", 0.10))
    cooldown_seconds = int(simulation.get("cooldown_seconds", 300))
    max_trades_per_day = int(simulation.get("max_trades_per_day", 20))
    trades_today = 0
    last_trade_at = 0.0
    trade_date = local_today()
    print(f"{symbol} Spot Testnet bot başlatıldı. dry_run={dry_run}")
    print("Not: Bu yazılım kâr garantisi vermez; önce Testnet ve küçük miktarla doğrulayın.")

    while True:
        try:
            new_symbol = selected_symbol(symbol)
            if position is None and new_symbol != symbol:
                symbol = new_symbol
                print(f"Seçili coin değişti: {symbol}")
            closes = [float(row[4]) for row in client.klines(symbol, candle_interval, 100)]
            higher_closes = [float(row[4]) for row in client.klines(symbol, higher_interval, 100)]
            depth = client.depth(symbol, 20)
            metrics = calculate_metrics(depth.get("bids", []), depth.get("asks", []), 10)
            higher_trend_up = higher_closes[-1] > __import__("app.strategy", fromlist=["ema"]).ema(higher_closes, slow_period)
            price = closes[-1]
            signal = generate_signal(closes, position is not None, fast_period, slow_period, rsi_period, higher_trend_up, metrics.imbalance, min_imbalance)
            today = local_today()
            if today != trade_date:
                trade_date = today
                trades_today = 0
                last_trade_at = 0.0
            if position:
                entry = position["entry"]
                if price >= entry * (1 + take_profit) or price <= entry * (1 - stop_loss) or signal.action == "SELL":
                    if dry_run:
                        quantity = position["quantity"]
                        proceeds = quantity * price
                        net = proceeds * (1 - fee_rate) - position["cost"]
                        guard.record_trade(net, today)
                        trades_today += 1
                        last_trade_at = time.time()
                        print(f"DRY SELL price={price:.2f} net={net:.4f} total={guard.realized_profit_usdt:.4f}")
                    else:
                        order = client.market_sell(symbol, position["quantity_str"])
                        quantity, proceeds = filled_values(order)
                        net = proceeds * (1 - fee_rate) - position["cost"]
                        guard.record_trade(net, today)
                        trades_today += 1
                        last_trade_at = time.time()
                        print(f"TESTNET SELL price={price:.2f} net={net:.4f} total={guard.realized_profit_usdt:.4f}")
                    position = None
            elif (
                guard.can_open_trade(today)
                and signal.action == "BUY"
                and trades_today < max_trades_per_day
                and time.time() - last_trade_at >= cooldown_seconds
            ):
                if dry_run:
                    cost = quote_amount
                    quantity = cost / price
                    position = {"entry": price, "quantity": quantity, "quantity_str": f"{quantity:.6f}", "cost": cost * (1 + fee_rate)}
                    last_trade_at = time.time()
                    print(f"DRY BUY price={price:.2f} amount={cost:.2f} reason={signal.reason}")
                else:
                    order = client.market_buy(symbol, quote_amount)
                    quantity, cost = filled_values(order)
                    if quantity <= 0 or cost <= 0:
                        raise RuntimeError(f"Alış emri dolmadı: {json.dumps(order)}")
                    position = {"entry": cost / quantity, "quantity": quantity, "quantity_str": f"{quantity:.6f}", "cost": cost * (1 + fee_rate)}
                    last_trade_at = time.time()
                    print(f"TESTNET BUY price={cost / quantity:.2f} amount={cost:.2f} reason={signal.reason}")
            print(f"symbol={symbol} price={price:.2f} signal={signal.action} rsi={signal.rsi:.1f} obi={metrics.imbalance:.3f} trend={'UP' if higher_trend_up else 'DOWN'} trades={trades_today} pnl={guard.realized_profit_usdt:.4f}")
            if guard.target_reached or guard.loss_limit_reached:
                print("Günlük durma limiti oluştu; bot kapanıyor.")
                return
            time.sleep(poll_seconds)
        except KeyboardInterrupt:
            print("Bot kullanıcı tarafından durduruldu.")
            return
        except Exception as error:
            print(f"HATA: {error}")
            time.sleep(15)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Binance Spot Testnet BTC bot")
    parser.add_argument("--dry-run", action="store_true", help="Emir göndermez; sinyali ve sanal işlemi gösterir")
    parser.add_argument("--symbol", help="İşlem sembolü; verilmezse sol analiz panelindeki seçim kullanılır")
    args = parser.parse_args()
    run(args.dry_run, args.symbol)
