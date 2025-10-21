@echo off
echo Starting Rule Engine Service...
cd /d "c:\Projects\Anonymizer"

echo Activating virtual environment...
call venv_rule_engine\Scripts\activate.bat

echo Installing dependencies...
pip install fastapi uvicorn pydantic openpyxl regex

echo Starting FastAPI application...
cd rule_engine
uvicorn app.main:app --host 0.0.0.0 --port 8004

pause