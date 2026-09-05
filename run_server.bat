@echo off
echo SINOPTIK HATA ARAMA SUNUCUSU BASLATILIYOR...
echo Bu pencereyi kapatabilirsiniz, sunucu arka planda calismaya devam edecektir.
set HEADLESS_MODE=1
pythonw web_server.py
exit

