import sys
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Binance Futures AI Scalping Analyzer")
        self.resize(900, 600)
        label = QLabel("Canlı veri bağlantısı hazırlanıyor…\n\nGerçek emir gönderimi devre dışıdır.")
        label.setStyleSheet("font-size: 20px; padding: 40px; color: #e7edf5;")
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(label)
        self.setCentralWidget(container)
        self.setStyleSheet("QMainWindow { background: #10151c; }")


def run() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
