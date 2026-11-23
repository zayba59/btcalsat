import argparse
import json
import time
from datetime import date, datetime
from decimal import ROUND_DOWN, Decimal
from pathlib import Path

import yaml

from app.risk import DailyProfitGuard
from app.spot_client import BinanceSpotClient
from app.strategy import generate_signal


ROOT = Path(__file__).resolve().parent
POSITION_FILE = ROOT / "data" / "position.json"


def load_position() -> dict | None:
    try:
        return json.loads(POSITION_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return None


def save_position(position: dict | None) -> None:
    if position is None:
        POSITION_FILE.unlink(missing_ok=True)
        return
    POSITION_FILE.parent.mkdir(parents=True, exist_ok=True)
    POSITION_FILE.write_text(json.dumps(position), encoding="utf-8")


def sell_quantity(client: BinanceSpotClient, symbol: str, wanted: float) -> str:
    """Eldeki bakiyeyi aşmayan, LOT_SIZE stepSize'a yuvarlanmış satış miktarı."""
    info = client.exchange_info(symbol)["symbols"][0]
    step = next(f["stepSize"] for f in info["filters"] if f["filterType"] == "LOT_SIZE")
    free = next((float(b["free"]) for b in client.account()["balances"] if b["asset"] == info["baseAsset"]), 0.0)
    quantity = Decimal(str(min(wanted, free))).quantize(Decimal(step).normalize(), rounding=ROUND_DOWN)
    if quantity <= 0:
        raise RuntimeError(f"Satılabilir {info['baseAsset']} bakiyesi yok (free={free})")
    return format(quantity, "f")


def load_config() -> dict:
    with (ROOT / "config.yaml").open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def filled_values(order: dict) -> tuple[float, float]:
    quantity = float(order.get("executedQty", 0))
    quote = float(order.get("cummulativeQuoteQty", 0))
    return quantity, quote


def local_today() -> date:
    from zoneinfo import ZoneInfo

    return datetime.now(ZoneInfo("Europe/Istanbul")).date()


def run(dry_run: bool) -> None:
    config = load_config()
    simulation = config["simulation"]
    market = config["market"]
    symbol = market["default_symbol"]
    client = BinanceSpotClient(testnet=simulation.get("testnet", True))
    trading_enabled = dry_run or bool(simulation.get("trading_enabled", False))
    if not trading_enabled:
        print("Emirler kapalı: config.yaml içinde simulation.trading_enabled=true yapın veya --dry-run kullanın.")
        return
    guard = DailyProfitGuard(
        target_usdt=float(simulation["target_net_profit_usdt"]),
        max_loss_usdt=float(simulation["max_daily_loss_usdt"]),
        trading_enabled=True,
    )
    position: dict | None = load_position()
    if position:
        print(f"Kayıtlı açık pozisyon yüklendi: giriş={position['entry']:.2f}")
    fee_rate = float(simulation.get("fee_rate", 0.0004))
    take_profit = float(simulation.get("take_profit_pct", 0.004))
    stop_loss = float(simulation.get("stop_loss_pct", 0.003))
    quote_amount = float(simulation.get("order_quote_usdt", simulation["collateral_usdt"]))
    print(f"{symbol} Spot Testnet bot başlatıldı. dry_run={dry_run}")
    print("Not: Bu yazılım kâr garantisi vermez; önce Testnet ve küçük miktarla doğrulayın.")

    while True:
        try:
            closes = [float(row[4]) for row in client.klines(symbol, "5m", 100)]
            price = closes[-1]
            signal = generate_signal(closes, position is not None)
            today = local_today()
            if position:
                entry = position["entry"]
                if price >= entry * (1 + take_profit) or price <= entry * (1 - stop_loss) or signal.action == "SELL":
                    if dry_run:
                        quantity = position["quantity"]
                        proceeds = quantity * price
                        net = proceeds * (1 - fee_rate) - position["cost"]
                        guard.record_trade(net, today)
                        print(f"DRY SELL price={price:.2f} net={net:.4f} total={guard.realized_profit_usdt:.4f}")
                    else:
                        order = client.market_sell(symbol, sell_quantity(client, symbol, position["quantity"]))
                        quantity, proceeds = filled_values(order)
                        net = proceeds * (1 - fee_rate) - position["cost"]
                        guard.record_trade(net, today)
                        print(f"TESTNET SELL price={price:.2f} net={net:.4f} total={guard.realized_profit_usdt:.4f}")
                    position = None
                    save_position(None)
            elif guard.can_open_trade(today) and signal.action == "BUY":
                if dry_run:
                    cost = quote_amount
                    quantity = cost / price
                    position = {"entry": price, "quantity": quantity, "quantity_str": f"{quantity:.6f}", "cost": cost * (1 + fee_rate)}
                    save_position(position)
                    print(f"DRY BUY price={price:.2f} amount={cost:.2f} reason={signal.reason}")
                else:
                    order = client.market_buy(symbol, quote_amount)
                    quantity, cost = filled_values(order)
                    if quantity <= 0 or cost <= 0:
                        raise RuntimeError(f"Alış emri dolmadı: {json.dumps(order)}")
                    position = {"entry": cost / quantity, "quantity": quantity, "quantity_str": f"{quantity:.6f}", "cost": cost * (1 + fee_rate)}
                    save_position(position)
                    print(f"TESTNET BUY price={cost / quantity:.2f} amount={cost:.2f} reason={signal.reason}")
            print(f"price={price:.2f} signal={signal.action} rsi={signal.rsi:.1f} pnl={guard.realized_profit_usdt:.4f}")
            if position is None and (guard.target_reached or guard.loss_limit_reached):
                print("Günlük durma limiti oluştu; bot kapanıyor.")
                return
            time.sleep(60)
        except KeyboardInterrupt:
            print("Bot kullanıcı tarafından durduruldu.")
            return
        except Exception as error:
            print(f"HATA: {error}")
            time.sleep(15)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Binance Spot Testnet BTC bot")
    parser.add_argument("--dry-run", action="store_true", help="Emir göndermez; sinyali ve sanal işlemi gösterir")
    args = parser.parse_args()
    run(args.dry_run)
