@echo off
setlocal
cd /d %~dp0
pyinstaller --noconfirm --windowed --name Capri ^
  --add-data "assets;assets" ^
  --add-data "capri_workspace;capri_workspace" ^
  main.py
echo Build done.
pause
