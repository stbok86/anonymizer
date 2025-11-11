@echo off
echo ================================================================
echo          ANONYMIZER PROJECT - START ALL SERVICES
echo ================================================================
echo.
echo This script will start all microservices for the Anonymizer project
echo Each service will run in a separate command window
echo.
echo Services to start:
echo   - Gateway                    : Port 8000  
echo   - Unified Document Service   : Port 8001
echo   - Orchestrator               : Port 8002
echo   - NLP Service               : Port 8003
echo   - Rule Engine               : Port 8004
echo   - Frontend (Streamlit)       : Port 8501 (starts last)
echo.
echo Starting backend services first...
echo.

echo [1/6] Starting Gateway Service...
start "Gateway-8000" cmd /k "cd /d %~dp0gateway && venv\Scripts\activate && cd app && py -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak > nul

echo [2/6] Starting Unified Document Service...
start "UnifiedDocService-8001" cmd /k "cd /d %~dp0unified_document_service && venv\Scripts\activate && cd app && py -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload"
timeout /t 3 /nobreak > nul

echo [3/6] Starting Orchestrator Service...
start "Orchestrator-8002" cmd /k "cd /d %~dp0orchestrator && venv\Scripts\activate && cd app && py -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload"
timeout /t 3 /nobreak > nul

echo [4/6] Starting NLP Service...
start "NLP-8003" cmd /k "cd /d %~dp0nlp_service && venv\Scripts\activate && cd app && py -m uvicorn main:app --host 0.0.0.0 --port 8003 --reload"
timeout /t 3 /nobreak > nul

echo [5/6] Starting Rule Engine Service...
start "RuleEngine-8004" cmd /k "cd /d %~dp0rule_engine && venv\Scripts\activate && cd app && py -m uvicorn main:app --host 0.0.0.0 --port 8004 --reload"
timeout /t 3 /nobreak > nul

echo.
echo Waiting for backend services to initialize...
timeout /t 5 /nobreak > nul

echo [6/6] Starting Frontend Service (will open in browser)...
start "Frontend-8501" cmd /k "cd /d %~dp0frontend && venv\Scripts\activate && py -m streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --browser.gatherUsageStats false --server.headless false"
timeout /t 5 /nobreak > nul

echo.
echo ================================================================
echo                    ALL SERVICES STARTED!
echo ================================================================
echo.
echo Backend services (APIs) started in order:
echo   ✓ Gateway                    : http://localhost:8000
echo   ✓ Unified Document Service   : http://localhost:8001
echo   ✓ Orchestrator               : http://localhost:8002
echo   ✓ NLP Service               : http://localhost:8003
echo   ✓ Rule Engine               : http://localhost:8004
echo.
echo Frontend application:
echo   ✓ Streamlit Web App         : http://localhost:8501
echo.
echo The browser should open automatically with the Streamlit interface.
echo If not, manually navigate to: http://localhost:8501
echo.
echo API Documentation available at:
echo   - Gateway API:     http://localhost:8000/docs
echo   - Doc Service API: http://localhost:8001/docs
echo   - Orchestrator:    http://localhost:8002/docs
echo   - NLP Service:     http://localhost:8003/docs
echo   - Rule Engine:     http://localhost:8004/docs
echo.
echo All services are now running. You can close this window.
echo To stop services, close their individual command windows.
echo.
timeout /t 10 /nobreak > nul
echo Launcher will close in 10 seconds...
exit /b 0