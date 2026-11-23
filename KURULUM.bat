@echo off
cd /d "%~dp0"
py -m venv .venv
if errorlevel 1 (
  echo Python bulunamadi. Python 3.11 veya daha yeni bir surum kurun.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo Kutuphane kurulumu basarisiz oldu.
  pause
  exit /b 1
)
echo Kurulum tamamlandi. Simdi KONTROL_MERKEZI.bat dosyasina cift tiklayabilirsiniz.
pause
