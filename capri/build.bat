@echo off
echo === Capri Python Build ===
cd /d %~dp0

echo [1/3] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo PIP FAILED
    pause
    exit /b %errorlevel%
)

echo [2/3] Building with PyInstaller...
pyinstaller --noconfirm --windowed --name Capri ^
    --add-data "assets;assets" ^
    --add-data "core;core" ^
    --add-data "overlay;overlay" ^
    --add-data "audio;audio" ^
    --add-data "events;events" ^
    --add-data "dialogue;dialogue" ^
    --add-data "files;files" ^
    main.py
if %errorlevel% neq 0 (
    echo BUILD FAILED
    pause
    exit /b %errorlevel%
)

echo [3/3] Done!
echo.
echo Executable: dist\Capri\Capri.exe
echo Copy the whole dist\Capri folder to USB for portable use.
pause