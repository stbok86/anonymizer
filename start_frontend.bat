@echo off
echo Starting Frontend Service...
cd /d "c:\Projects\Anonymizer"

echo Activating virtual environment...
call venv_frontend\Scripts\activate.bat

echo Installing dependencies...
pip install streamlit

echo Creating Streamlit config...
if not exist "%userprofile%\.streamlit" mkdir "%userprofile%\.streamlit"
echo [browser] > "%userprofile%\.streamlit\config.toml"
echo gatherUsageStats = false >> "%userprofile%\.streamlit\config.toml"

echo Starting Streamlit application...
cd frontend
streamlit run main.py --server.port=8501 --server.address=0.0.0.0

pause