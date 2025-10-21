@echo off
echo Starting Orchestrator Service...
cd /d "c:\Projects\Anonymizer"

echo Activating virtual environment...
call venv_orchestrator\Scripts\activate.bat

echo Installing dependencies...
pip install fastapi uvicorn pydantic

echo Starting FastAPI application...
cd orchestrator
uvicorn app.main:app --host 0.0.0.0 --port 8002

pause