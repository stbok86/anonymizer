@echo off
echo ================================================================
echo          ANONYMIZER PROJECT - START ALL SERVICES
echo ================================================================
echo.
echo This script will start all microservices for the Anonymizer project
echo Each service will run in a separate command window
echo.
echo Services to start:
echo   - Rule Engine               : Port 8003  
echo   - Orchestrator               : Port 8004
echo   - Unified Document Service   : Port 8009
echo   - NLP Service               : Port 8006
echo   - Gateway                    : Port 8002
echo   - Frontend (Streamlit)       : Port 8501 (starts last)
echo.
echo Starting backend services first...
echo.

echo [1/6] Starting Rule Engine Service...
start "RuleEngine-8003" cmd /k "cd /d %~dp0rule_engine && venv\Scripts\activate && cd app && py -m uvicorn main:app --host 0.0.0.0 --port 8003 --reload"
timeout /t 3 /nobreak > nul

echo [2/6] Starting Orchestrator Service...
start "Orchestrator-8004" cmd /k "cd /d %~dp0orchestrator && venv\Scripts\activate && cd app && py -m uvicorn main:app --host 0.0.0.0 --port 8004 --reload"
timeout /t 3 /nobreak > nul

echo [3/6] Starting Unified Document Service...
start "UnifiedDocService-8009" cmd /k "cd /d %~dp0unified_document_service && venv\Scripts\activate && cd app && py -m uvicorn main:app --host 0.0.0.0 --port 8009 --reload"
timeout /t 3 /nobreak > nul

echo [4/6] Starting NLP Service...
start "NLP-8006" cmd /k "cd /d %~dp0nlp_service && venv\Scripts\activate && cd app && py -m uvicorn main:app --host 0.0.0.0 --port 8006 --reload"
timeout /t 3 /nobreak > nul

echo [5/6] Starting Gateway Service...
start "Gateway-8002" cmd /k "cd /d %~dp0gateway && venv\Scripts\activate && cd app && py -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload"
timeout /t 3 /nobreak > nul

echo.
echo Waiting for backend services to initialize...
timeout /t 8 /nobreak > nul

echo.
echo Checking services health...
echo   Checking Gateway health: http://localhost:8002/health
curl -s http://localhost:8002/health > nul 2>&1
if %errorlevel%==0 (
    echo   ✅ Gateway is responding
) else (
    echo   ⚠️ Gateway may still be starting...
)

echo.
echo [6/6] Starting Frontend Service (will open in browser)...
start "Frontend-8501" cmd /k "cd /d %~dp0frontend && venv\Scripts\activate && py -m streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --browser.gatherUsageStats false --server.headless false"
timeout /t 5 /nobreak > nul

echo.
echo ================================================================
echo                    ALL SERVICES STARTED!
echo ================================================================
echo.
echo Backend services (APIs) started in order:
echo   ✓ Rule Engine               : http://localhost:8003
echo   ✓ Orchestrator               : http://localhost:8004
echo   ✓ Unified Document Service   : http://localhost:8009
echo   ✓ NLP Service               : http://localhost:8006
echo   ✓ Gateway                    : http://localhost:8002
echo.
echo Frontend application:
echo   ✓ Streamlit Web App         : http://localhost:8501
echo.
echo The browser should open automatically with the Streamlit interface.
echo If not, manually navigate to: http://localhost:8501
echo.
echo 🔧 SYSTEM CAPABILITIES:
echo   • Rule Engine: Structured data analysis (patterns, regex)
echo   • NLP Service: Unstructured data analysis (spaCy + pymorphy3)  
echo   • Combined Analysis: Both engines work together for comprehensive detection
echo   • API Gateway: Centralized routing on port 8002
echo   • Frontend: Interactive document anonymization interface
echo.
echo 📖 TESTING WORKFLOW:
echo   1. Open http://localhost:8501 in your browser
echo   2. Upload a DOCX document in Step 1
echo   3. Click "Анализировать документ" to run Rule Engine + NLP analysis
echo   4. Review combined results in Step 2 (shows source: Rule Engine vs NLP Service)
echo   5. Select items to anonymize and proceed with anonymization
echo.
echo API Documentation available at:
echo   - Rule Engine:     http://localhost:8003/docs
echo   - Orchestrator:    http://localhost:8004/docs
echo   - Doc Service API: http://localhost:8009/docs
echo   - NLP Service:     http://localhost:8006/docs
echo   - Gateway API:     http://localhost:8002/docs
echo.
echo All services are now running. You can close this window.
echo To stop services, close their individual command windows.
echo.
timeout /t 10 /nobreak > nul
echo Launcher will close in 10 seconds...
exit /b 0