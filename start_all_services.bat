@echo off
echo ================================================================
echo          ANONYMIZER PROJECT - START ALL SERVICES
echo ================================================================
echo.
echo This script will start all microservices for the Anonymizer project
echo Each service will run in a separate command window
echo.
echo Services to start:
echo   - Frontend (Streamlit)       : Port 8501
echo   - Gateway                    : Port 8000  
echo   - Orchestrator               : Port 8002
echo   - Unified Document Service   : Port 8001
echo   - NLP Service               : Port 8003
echo   - Rule Engine               : Port 8004
echo.
echo Press any key to start all services...
pause
echo.

echo Starting Frontend Service...
start "Frontend-8501" cmd /k "start_frontend.bat"
timeout /t 2 /nobreak > nul

echo Starting Gateway Service...
start "Gateway-8000" cmd /k "start_gateway.bat"
timeout /t 2 /nobreak > nul

echo Starting Orchestrator Service...
start "Orchestrator-8002" cmd /k "start_orchestrator.bat"
timeout /t 2 /nobreak > nul

echo Starting Unified Document Service...
start "UnifiedDocService-8001" cmd /k "start_unified_document_service.bat"
timeout /t 2 /nobreak > nul

echo Starting NLP Service...
start "NLP-8003" cmd /k "start_nlp_service.bat"
timeout /t 2 /nobreak > nul

echo Starting Rule Engine Service...
start "RuleEngine-8004" cmd /k "start_rule_engine.bat"
timeout /t 2 /nobreak > nul

echo.
echo ================================================================
echo All services are starting...
echo.
echo Check the individual command windows for each service status
echo.
echo Access points:
echo   Frontend: http://localhost:8501
echo   Gateway:  http://localhost:8000
echo   API Docs: http://localhost:8001/docs (and others)
echo.
echo Press any key to exit this launcher...
pause