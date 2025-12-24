@echo off
REM Wrapper script to run Streamlit with correct Python paths

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Set Python to use from .venv
set PYTHON_EXE=%SCRIPT_DIR%python\python-3.11.0-embed-amd64\python.exe

REM CRITICAL: Tell Python subsystems to use THIS python.exe


REM Change to frontend directory
cd /d "%SCRIPT_DIR%frontend"

REM Run Streamlit directly through Python
"%PYTHON_EXE%" -m streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --browser.gatherUsageStats false --server.headless false
