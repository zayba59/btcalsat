import asyncio
import json
from collections.abc import AsyncIterator

import websockets


class BinanceMarketStream:
    def __init__(self, symbol: str = "BTCUSDT") -> None:
        self.symbol = symbol.lower()
        self.url = f"wss://fstream.binance.com/stream?streams={self.symbol}@depth20@100ms/{self.symbol}@aggTrade"

    async def messages(self) -> AsyncIterator[dict]:
        while True:
            try:
                async with websockets.connect(self.url, ping_interval=20, ping_timeout=20) as socket:
                    async for raw in socket:
                        yield json.loads(raw)
            except (OSError, asyncio.TimeoutError, websockets.WebSocketException):
                await asyncio.sleep(3)
