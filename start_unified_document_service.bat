@echo off
echo Starting Unified Document Service...
cd /d "c:\Projects\Anonymizer"

echo Activating virtual environment...
call venv_unified_document_service\Scripts\activate.bat

echo Installing dependencies...
pip install fastapi uvicorn pydantic python-docx lxml openpyxl regex python-multipart

echo Starting FastAPI application...
cd unified_document_service
uvicorn app.main:app --host 0.0.0.0 --port 8001

pause