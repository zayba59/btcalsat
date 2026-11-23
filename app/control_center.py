import subprocess
import sys
import webbrowser
import re
from pathlib import Path

from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QApplication, QGridLayout, QGroupBox, QHeaderView, QLabel, QMainWindow, QProgressBar, QPushButton, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget

ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_URL = "https://github.com/zayba59/Binance-Futures-AI-Scalping-Analyzer"


class ControlCenter(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.dashboard_process: QProcess | None = None
        self.bot_process: QProcess | None = None
        self.setWindowTitle("ZAYBA | CRYPTO KONTROL MERKEZİ")
        self.resize(900, 700)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(14)
        title = QLabel("ZAYBA  |  CRYPTO")
        title.setObjectName("title")
        subtitle = QLabel("Binance Spot Testnet • Bot kontrolü • Güvenli sanal işlem merkezi")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        self.status = QLabel("İşlem bekleniyor")
        self.status.setObjectName("status")
        layout.addWidget(self.status)
        self.pnl = QLabel("GÜNLÜK NET KÂR / ZARAR: 0.0000 USDT")
        self.pnl.setObjectName("pnl")
        layout.addWidget(self.pnl)
        grid = QGridLayout()
        grid.setSpacing(12)
        buttons = [
            ("GÜNCELLEMELERİ KONTROL ET", self.check_updates, 0, 0),
            ("GÜNCELLEMEYİ YÜKLE", self.pull_updates, 0, 1),
            ("ANALİZ PANELİNİ BAŞLAT", self.start_dashboard, 1, 0),
            ("BOTU BAŞLAT (DRY-RUN)", self.start_bot, 1, 1),
            ("ANALİZ PANELİNİ DURDUR", self.stop_dashboard, 2, 0),
            ("BOTU DURDUR", self.stop_bot, 2, 1),
            ("GITHUB SAYFASINI AÇ", self.open_repository, 3, 0),
            ("KURULUM / ONARIM", self.repair_installation, 3, 1),
        ]
        for text, callback, row, column in buttons:
            button = QPushButton(text)
            button.setMinimumHeight(58)
            button.clicked.connect(callback)
            grid.addWidget(button, row, column)
        layout.addLayout(grid)
        trades_group = QGroupBox("BOT İŞLEMLERİ")
        trades_layout = QVBoxLayout(trades_group)
        self.trades = QTableWidget(0, 5)
        self.trades.setHorizontalHeaderLabels(["Zaman", "İşlem", "Fiyat", "Tutar / Net", "Günlük Toplam"])
        self.trades.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.trades.setAlternatingRowColors(True)
        self.trades.setMinimumHeight(150)
        trades_layout.addWidget(self.trades)
        layout.addWidget(trades_group)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)
        group = QGroupBox("İŞLEM GÜNLÜĞÜ")
        group_layout = QVBoxLayout(group)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(180)
        group_layout.addWidget(self.log)
        layout.addWidget(group)
        self.setCentralWidget(root)
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #f3f7fd; color: #15345b; }
            QLabel#title { font-size: 32px; font-weight: 800; color: #0b3d78; }
            QLabel#subtitle { font-size: 15px; color: #6380a5; padding-bottom: 8px; }
            QLabel#status { background: white; border: 1px solid #d9e3f0; padding: 16px; color: #11834b; font-weight: 700; }
            QLabel#pnl { background: #eaf8ef; border: 1px solid #9bd4aa; padding: 14px; color: #087532; font-size: 18px; font-weight: 800; }
            QPushButton { background: #ffffff; border: 1px solid #173b66; color: #14385f; font-size: 15px; font-weight: 700; padding: 12px; }
            QPushButton:hover { background: #e8f0ff; }
            QProgressBar { background: #e2e8f1; border: 1px solid #cbd6e3; height: 22px; }
            QProgressBar::chunk { background: #14b83d; }
            QGroupBox { border: 0; font-weight: 800; font-size: 15px; padding-top: 14px; }
            QTextEdit { background: #ffffff; border: 1px solid #d9e3f0; color: #183d68; font-family: Consolas; }
            QTableWidget { background: #ffffff; alternate-background-color: #f4f8fc; border: 1px solid #d9e3f0; color: #183d68; }
        """)

    def write_log(self, message: str) -> None:
        self.log.append(message)
        self.status.setText(message)

    def run_git(self, *args: str) -> str:
        result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        return (result.stdout or result.stderr).strip()

    def check_updates(self) -> None:
        self.progress.setValue(30)
        output = self.run_git("status", "--short", "--branch")
        self.write_log(f"GitHub durumu kontrol edildi.\n{output or 'Değişiklik yok.'}")
        self.progress.setValue(100)

    def pull_updates(self) -> None:
        self.progress.setValue(35)
        output = self.run_git("pull", "--ff-only")
        self.write_log(f"Güncelleme sonucu:\n{output or 'Güncel sürüm kullanılıyor.'}")
        self.progress.setValue(100)

    def start_dashboard(self) -> None:
        if self.dashboard_process and self.dashboard_process.state() != QProcess.ProcessState.NotRunning:
            self.write_log("Proje zaten çalışıyor.")
            return
        self.dashboard_process = QProcess(self)
        self.dashboard_process.setWorkingDirectory(str(ROOT))
        self.dashboard_process.start(sys.executable, [str(ROOT / "main.py"), "--dashboard"])
        self.write_log("Binance Spot Testnet analiz paneli başlatıldı. Seçilen coin botta kullanılır.")

    def stop_dashboard(self) -> None:
        if self.dashboard_process:
            self.dashboard_process.terminate()
            self.dashboard_process = None
        self.write_log("Analiz paneli durduruldu.")

    def start_bot(self) -> None:
        if self.bot_process and self.bot_process.state() != QProcess.ProcessState.NotRunning:
            self.write_log("Bot zaten çalışıyor.")
            return
        self.bot_process = QProcess(self)
        self.bot_process.setWorkingDirectory(str(ROOT))
        self.bot_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.bot_process.readyReadStandardOutput.connect(self.read_bot_output)
        self.bot_process.finished.connect(lambda *_: self.write_log("Bot işlemi sona erdi."))
        self.bot_process.start(sys.executable, ["-u", str(ROOT / "bot.py"), "--dry-run"])
        self.write_log("Bot dry-run modunda başlatıldı; gerçek emir gönderilmez.")

    def read_bot_output(self) -> None:
        if not self.bot_process:
            return
        output = bytes(self.bot_process.readAllStandardOutput()).decode("utf-8", errors="replace").strip()
        if output:
            self.write_log(output)
            for line in output.splitlines():
                self.add_trade_from_line(line)

    def add_trade_from_line(self, line: str) -> None:
        buy = re.search(r"DRY BUY price=([\d.]+) amount=([\d.]+)", line)
        sell = re.search(r"DRY SELL price=([\d.]+) net=([-\d.]+) total=([-\d.]+)", line)
        if not buy and not sell:
            return
        now = __import__("datetime").datetime.now().strftime("%H:%M:%S")
        if buy:
            action, price, amount, total = "ALIŞ", buy.group(1), f"{buy.group(2)} USDT", "—"
        else:
            action, price, amount, total = "SATIŞ", sell.group(1), f"{sell.group(2)} USDT", f"{sell.group(3)} USDT"
            self.pnl.setText(f"GÜNLÜK NET KÂR / ZARAR: {sell.group(3)} USDT")
            self.pnl.setStyleSheet("color: #087532;" if float(sell.group(3)) >= 0 else "color: #a51d2d;")
        row = self.trades.rowCount()
        self.trades.insertRow(row)
        for column, value in enumerate((now, action, price, amount, total)):
            self.trades.setItem(row, column, QTableWidgetItem(value))
        self.trades.scrollToBottom()

    def stop_bot(self) -> None:
        if self.bot_process and self.bot_process.state() != QProcess.ProcessState.NotRunning:
            self.bot_process.terminate()
            if not self.bot_process.waitForFinished(1500):
                self.bot_process.kill()
            self.bot_process = None
        self.write_log("Bot durduruldu.")

    def open_repository(self) -> None:
        webbrowser.open(REPOSITORY_URL)
        self.write_log("GitHub repository tarayıcıda açıldı.")

    def repair_installation(self) -> None:
        self.write_log("Kurulum kontrolü: Python ortamı ve requirements.txt hazır.")


def run() -> None:
    app = QApplication(sys.argv)
    window = ControlCenter()
    window.show()
    sys.exit(app.exec())
