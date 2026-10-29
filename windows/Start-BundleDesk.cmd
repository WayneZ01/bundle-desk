@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title Bundle Desk - Android Workbench
set "BUNDLED_PYTHON=%~dp0runtime\windows-x86_64\python\python.exe"
if not exist "%BUNDLED_PYTHON%" (
  echo Please extract the COMPLETE ZIP before starting Bundle Desk.
  pause
  exit /b 1
)
echo Bundle Desk is starting. Your default browser will open automatically.
echo Keep this window open while using the tool. Press Ctrl+C to stop.
"%BUNDLED_PYTHON%" "%~dp0app\server.py"
if errorlevel 1 (
  echo.
  echo Startup failed. Please copy the error above for troubleshooting.
  pause
)
endlocal
