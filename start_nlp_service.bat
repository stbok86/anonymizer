@echo off
echo Starting NLP Service...
cd /d "c:\Projects\Anonymizer"

echo Activating virtual environment...
call venv_nlp_service\Scripts\activate.bat

echo Installing dependencies...
pip install fastapi uvicorn pydantic spacy

echo Starting FastAPI application...
cd nlp_service
uvicorn app.main:app --host 0.0.0.0 --port 8003

pause