@echo off
echo ================================================================
echo        ANONYMIZER PROJECT - SERVICE STATUS CHECK
echo ================================================================
echo.

echo Checking service ports...
echo.

echo [1/6] Rule Engine (Port 8003):
netstat -ano | findstr :8003 > nul 2>&1
if %errorlevel%==0 (
    echo   ✅ Port 8003 is active
    curl -s http://localhost:8003/healthz > nul 2>&1
    if %errorlevel%==0 (
        echo   ✅ Rule Engine is responding
    ) else (
        echo   ⚠️ Port occupied but service not responding
    )
) else (
    echo   ❌ Rule Engine not running
)

echo.
echo [2/6] Orchestrator (Port 8004):
netstat -ano | findstr :8004 > nul 2>&1
if %errorlevel%==0 (
    echo   ✅ Port 8004 is active
    curl -s http://localhost:8004/healthz > nul 2>&1
    if %errorlevel%==0 (
        echo   ✅ Orchestrator is responding
    ) else (
        echo   ⚠️ Port occupied but service not responding
    )
) else (
    echo   ❌ Orchestrator not running
)

echo.
echo [3/6] Unified Document Service (Port 8009):
netstat -ano | findstr :8009 > nul 2>&1
if %errorlevel%==0 (
    echo   ✅ Port 8009 is active
    curl -s http://localhost:8009/health > nul 2>&1
    if %errorlevel%==0 (
        echo   ✅ Unified Document Service is responding
    ) else (
        echo   ⚠️ Port occupied but service not responding
    )
) else (
    echo   ❌ Unified Document Service not running
)

echo.
echo [4/6] NLP Service (Port 8006):
netstat -ano | findstr :8006 > nul 2>&1
if %errorlevel%==0 (
    echo   ✅ Port 8006 is active
    curl -s http://localhost:8006/healthz > nul 2>&1
    if %errorlevel%==0 (
        echo   ✅ NLP Service is responding
    ) else (
        echo   ⚠️ Port occupied but service not responding
    )
) else (
    echo   ❌ NLP Service not running
)

echo.
echo [5/6] Gateway (Port 8002):
netstat -ano | findstr :8002 > nul 2>&1
if %errorlevel%==0 (
    echo   ✅ Port 8002 is active
    curl -s http://localhost:8002/health > nul 2>&1
    if %errorlevel%==0 (
        echo   ✅ Gateway is responding
        echo   📊 Getting service health summary...
        curl -s http://localhost:8002/health
        echo.
    ) else (
        echo   ⚠️ Port occupied but service not responding
    )
) else (
    echo   ❌ Gateway not running
)

echo.
echo [6/6] Frontend (Port 8501):
netstat -ano | findstr :8501 > nul 2>&1
if %errorlevel%==0 (
    echo   ✅ Frontend (Streamlit) is running on port 8501
    echo   🌐 Access at: http://localhost:8501
) else (
    echo   ❌ Frontend not running
)

echo.
echo ================================================================
echo                    STATUS CHECK COMPLETE
echo ================================================================
echo.
echo If all services show ✅, you can proceed with testing.
echo If any service shows ❌, run start_all_services.bat first.
echo.
pause