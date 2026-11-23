import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication, QGridLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QVBoxLayout, QWidget

from app.analysis import calculate_metrics, signal_from_imbalance


ROOT = Path(__file__).resolve().parent.parent
SELECTED_SYMBOL_FILE = ROOT / "data" / "selected_symbol.txt"


class MarketWorker(QThread):
    metrics = Signal(dict)
    error = Signal(str)

    def __init__(self, symbol: str) -> None:
        super().__init__()
        self.symbol = symbol.lower()
        self.stop_requested = False

    def stop(self) -> None:
        self.stop_requested = True

    def run(self) -> None:
        try:
            import websockets
            asyncio.run(self._consume(websockets))
        except Exception as exc:
            self.error.emit(f"Bağlantı kullanılamıyor: {exc}")

    async def _consume(self, websockets) -> None:
        url = f"wss://stream.testnet.binance.vision/stream?streams={self.symbol}@depth20@100ms/{self.symbol}@aggTrade"
        while not self.stop_requested:
            try:
                async with websockets.connect(url, ping_interval=20, ping_timeout=20) as socket:
                    self.metrics.emit({"connection": "Bağlandı"})
                    async for raw in socket:
                        if self.stop_requested:
                            break
                        message = json.loads(raw).get("data", {})
                        if message.get("e") == "depthUpdate":
                            # Spot depth streams use bids/asks; futures streams use b/a.
                            bids = message.get("bids", message.get("b", []))
                            asks = message.get("asks", message.get("a", []))
                            values = calculate_metrics(bids, asks, 10)
                            direction, score = signal_from_imbalance(values.imbalance)
                            price = float(asks[0][0]) if asks else 0.0
                            self.metrics.emit({"price": price, "spread": values.spread, "bid": values.bid_volume, "ask": values.ask_volume, "obi": values.imbalance, "signal": direction, "score": score, "connection": "Bağlandı", "time": datetime.now().strftime("%H:%M:%S")})
            except Exception as exc:
                self.error.emit(f"Yeniden bağlanıyor: {exc}")
                await asyncio.sleep(3)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.worker: MarketWorker | None = None
        self.setWindowTitle("Binance Spot Testnet AI Analyzer")
        self.resize(1000, 650)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 24, 28, 24)
        title = QLabel("BINANCE SPOT TESTNET  |  AI ORDER FLOW ANALYZER")
        title.setObjectName("title")
        layout.addWidget(title)
        row = QGridLayout()
        row.addWidget(QLabel("Coin"), 0, 0)
        self.symbol = QLineEdit("BTCUSDT")
        self.symbol.setPlaceholderText("BTCUSDT")
        row.addWidget(self.symbol, 0, 1)
        self.start_button = QPushButton("CANLI VERİYİ BAŞLAT")
        self.start_button.clicked.connect(self.start_stream)
        row.addWidget(self.start_button, 0, 2)
        self.stop_button = QPushButton("DURDUR")
        self.stop_button.clicked.connect(self.stop_stream)
        row.addWidget(self.stop_button, 0, 3)
        layout.addLayout(row)
        self.connection = QLabel("Bağlantı bekleniyor")
        self.connection.setObjectName("connection")
        layout.addWidget(self.connection)
        self.cards: dict[str, QLabel] = {}
        card_layout = QGridLayout()
        fields = (("price", "CANLI FİYAT"), ("spread", "SPREAD"), ("bid", "ALIŞ HACMİ"), ("ask", "SATIŞ HACMİ"), ("obi", "OBI"), ("signal", "SİNYAL"), ("score", "ANALİZ PUANI"), ("time", "SON GÜNCELLEME"))
        for index, (key, label) in enumerate(fields):
            box = QWidget()
            box_layout = QVBoxLayout(box)
            caption = QLabel(label)
            caption.setObjectName("caption")
            value = QLabel("—")
            value.setObjectName("value")
            box_layout.addWidget(caption)
            box_layout.addWidget(value)
            card_layout.addWidget(box, index // 4, index % 4)
            self.cards[key] = value
        layout.addLayout(card_layout)
        note = QLabel("Solda seçilen coin sağdaki Spot Testnet botuna aktarılır. Gerçek emir gönderimi devre dışıdır.")
        note.setObjectName("note")
        layout.addWidget(note)
        self.setCentralWidget(root)
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #101923; color: #e7edf5; }
            QLabel#title { font-size: 22px; font-weight: 800; color: #7ec8ff; padding-bottom: 14px; }
            QLabel#connection { background: #152536; border: 1px solid #31516d; padding: 12px; color: #8be28b; }
            QLineEdit { background: #172433; border: 1px solid #41627d; color: white; padding: 10px; }
            QPushButton { background: #1a5f91; border: 1px solid #62b9f2; color: white; padding: 10px; font-weight: 700; }
            QPushButton:hover { background: #267db6; }
            QLabel#caption { color: #8da9be; font-size: 11px; }
            QLabel#value { color: #f4f8fb; font-size: 20px; font-weight: 700; }
            QLabel#note { color: #91a5b7; padding-top: 20px; }
        """)

    def start_stream(self) -> None:
        self.stop_stream()
        symbol = self.symbol.text().strip().upper()
        if not symbol:
            self.connection.setText("Coin sembolü girin")
            return
        SELECTED_SYMBOL_FILE.parent.mkdir(parents=True, exist_ok=True)
        SELECTED_SYMBOL_FILE.write_text(symbol, encoding="utf-8")
        self.worker = MarketWorker(symbol)
        self.worker.metrics.connect(self.update_metrics)
        self.worker.error.connect(self.show_error)
        self.worker.start()
        self.connection.setText(f"{symbol} için bağlantı başlatılıyor…")

    def stop_stream(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(1500)
        self.worker = None

    def update_metrics(self, values: dict) -> None:
        if values.get("connection"):
            self.connection.setText(values["connection"])
        for key, value in values.items():
            if key in self.cards:
                self.cards[key].setText(f"{value:.6f}" if isinstance(value, float) else str(value))

    def show_error(self, message: str) -> None:
        self.connection.setText(message)

    def closeEvent(self, event) -> None:
        self.stop_stream()
        event.accept()


def run() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
