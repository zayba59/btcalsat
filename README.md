# Binance Futures AI Scalping Analyzer

Binance USDT-M canlı piyasa verilerini analiz eden ve yalnızca sanal işlem yapan Windows masaüstü uygulaması.

## Güvenlik kapsamı

- Gerçek emir göndermez.
- Binance API anahtarı veya işlem yetkisi istemez.
- Sinyal puanı kazanma olasılığı değildir; analiz skorudur.

## Başlatma

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

İlk sürüm canlı fiyat ve temel order book analiziyle başlar. Sanal işlem, raporlar ve EXE paketleme sonraki aşamalarda tamamlanacaktır.
