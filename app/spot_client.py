import hashlib
import hmac
import os
import time
from urllib.parse import urlencode

import httpx


class BinanceSpotClient:
    def __init__(self, testnet: bool = True) -> None:
        self.base_url = "https://testnet.binance.vision" if testnet else "https://api.binance.com"
        self.api_key = os.getenv("BINANCE_API_KEY", "")
        self.api_secret = os.getenv("BINANCE_API_SECRET", "")

    def _request(self, method: str, path: str, params: dict | None = None, signed: bool = False) -> dict | list:
        values = dict(params or {})
        headers = {}
        if signed:
            if not self.api_key or not self.api_secret:
                raise RuntimeError("BINANCE_API_KEY ve BINANCE_API_SECRET tanımlı değil")
            values["timestamp"] = int(time.time() * 1000)
            values["recvWindow"] = 5000
            query = urlencode(values)
            values["signature"] = hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
            headers["X-MBX-APIKEY"] = self.api_key
        response = httpx.request(method, self.base_url + path, params=values, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

    def klines(self, symbol: str, interval: str = "5m", limit: int = 100) -> list[list]:
        return self._request("GET", "/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": limit})

    def exchange_info(self, symbol: str) -> dict:
        return self._request("GET", "/api/v3/exchangeInfo", {"symbol": symbol})

    def account(self) -> dict:
        return self._request("GET", "/api/v3/account", signed=True)

    def market_buy(self, symbol: str, quote_amount: float) -> dict:
        return self._request("POST", "/api/v3/order", {"symbol": symbol, "side": "BUY", "type": "MARKET", "quoteOrderQty": f"{quote_amount:.2f}"}, signed=True)

    def market_sell(self, symbol: str, quantity: str) -> dict:
        return self._request("POST", "/api/v3/order", {"symbol": symbol, "side": "SELL", "type": "MARKET", "quantity": quantity}, signed=True)
