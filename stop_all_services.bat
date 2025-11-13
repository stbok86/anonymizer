@echo off
echo ================================================================
echo        ANONYMIZER PROJECT - STOP ALL SERVICES
echo ================================================================
echo.
echo This script will stop all running services for the Anonymizer project
echo.

echo Stopping Python processes...
taskkill /f /im python.exe 2>nul
if %errorlevel%==0 (
    echo ✅ Python processes stopped
) else (
    echo ℹ️ No Python processes were running
)

echo.
echo Stopping processes by port (if any remain)...

echo Checking port 8003 (Rule Engine)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8003') do (
    taskkill /f /pid %%a 2>nul
)

echo Checking port 8004 (Orchestrator)...  
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8004') do (
    taskkill /f /pid %%a 2>nul
)

echo Checking port 8009 (Unified Document Service)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8009') do (
    taskkill /f /pid %%a 2>nul
)

echo Checking port 8006 (NLP Service)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8006') do (
    taskkill /f /pid %%a 2>nul
)

echo Checking port 8002 (Gateway)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8002') do (
    taskkill /f /pid %%a 2>nul
)

echo Checking port 8501 (Frontend)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8501') do (
    taskkill /f /pid %%a 2>nul
)

echo.
echo ================================================================
echo                 ALL SERVICES STOPPED
echo ================================================================
echo.
echo You can now safely restart services using start_all_services.bat
echo.
pause