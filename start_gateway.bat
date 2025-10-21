@echo off
echo Starting Gateway Service...
cd /d "c:\Projects\Anonymizer"

echo Activating virtual environment...
call venv_gateway\Scripts\activate.bat

echo Installing dependencies...
pip install fastapi uvicorn pydantic

echo Starting FastAPI application...
cd gateway
uvicorn app.main:app --host 0.0.0.0 --port 8000

pause