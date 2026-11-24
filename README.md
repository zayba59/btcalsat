# Binance Spot Testnet BTC Trading Bot

Binance Spot Testnet canlı piyasa verilerini analiz eden, günlük net kâr hedefi ve zarar limiti bulunan Windows masaüstü uygulaması.

## Güvenlik kapsamı

- Varsayılan olarak gerçek emir göndermez (`simulation.trading_enabled: false`).
- Spot Testnet veri akışını kullanır; gerçek API anahtarı eklenmemiştir.
- Kaldıraç kullanılmaz.
- Net gerçekleşmiş kâr 10 USDT'ye ulaştığında o gün yeni işlem açılmaz.
- Günlük 10 USDT zarar limitinde yeni işlem açılmaz.
- Sinyal puanı kazanma olasılığı değildir; analiz skorudur.

## Başlatma

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Kontrol merkezi açıldıktan sonra `BOTU BAŞLAT (DRY-RUN)` ve `BOTU DURDUR` düğmeleriyle bot yönetilebilir. Kontrol merkezi botu varsayılan olarak gerçek emir göndermeyen dry-run modunda başlatır.

Analiz panelinde bir sembol seçip `CANLI VERİYİ BAŞLAT` düğmesine basıldığında seçim `data/selected_symbol.txt` içine yazılır. Bot her döngüde bu seçimi okur ve açık pozisyon yoksa aynı Spot Testnet sembolüne geçer. Açık pozisyon varken sembol değiştirmez; önce mevcut pozisyonu kapatır.

Kârlılık odaklı varsayılan ayar 5 dakikalık mum, 15 dakikalık üst trend, 15 saniyelik kontrol, EMA9/EMA21, RSI14 ve pozitif OBI onayı kullanır. İşlem başına bekleme, günlük işlem limiti ve gerçekçi komisyon varsayımı da uygulanır.

## Botu Testnet'te çalıştırma

Önce `.env.example` içindeki değişkenleri terminal ortamına girin. Testnet API anahtarında yalnızca okuma ve işlem izinleri verin; para çekme izni vermeyin.

Emir göndermeden sanal çalıştırma:

```powershell
python bot.py --dry-run
```

Testnet emri gönderen mod:

```powershell
$env:BINANCE_API_KEY = "TESTNET_API_KEY"
$env:BINANCE_API_SECRET = "TESTNET_API_SECRET"
python bot.py
```

`config.yaml` içindeki `trading_enabled` değeri varsayılan olarak `false` olduğu için Testnet emirleri de ayrıca etkinleştirilmelidir. Bunun için değeri yalnızca Testnet API anahtarlarıyla `true` yapın.

İlk sürüm canlı fiyat ve temel order book analiziyle başlar. Gerçek emirleri etkinleştirmeden önce Testnet üzerinde doğrulama yapılmalıdır.
