@echo off
setlocal
echo ================================================================
echo        ANONYMIZER PROJECT - STOP ALL SERVICES
echo ================================================================
echo.
echo This script will stop all running services for the Anonymizer project
echo.

REM Останавливаем через PowerShell с таймаутом
echo Stopping services via PowerShell...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Get-Process python,streamlit -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue" 2>nul

REM Дополнительная проверка через taskkill
echo Stopping Python processes...
taskkill /f /im python.exe 2>nul
taskkill /f /im streamlit.exe 2>nul

echo.
echo Stopping processes by port (with timeout)...

REM Функция остановки с таймаутом
for %%p in (8003 8004 8009 8006 8002 8501) do (
    echo Checking port %%p...
    for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :%%p') do (
        taskkill /f /pid %%a 2>nul
    )
)

echo.
echo ================================================================
echo                 ALL SERVICES STOPPED
echo ================================================================
echo.
echo You can now safely restart services using start_all_services.bat
echo.
pause