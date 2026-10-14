@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Rode instalar_windows.bat primeiro.
  pause
  exit /b 1
)
start "Mercado Web" http://127.0.0.1:5000
.venv\Scripts\python.exe app.py
pause
