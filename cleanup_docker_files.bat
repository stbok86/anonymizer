@echo off
echo ================================================================
echo          CLEANUP DOCKER FILES - REMOVE UNUSED DOCKER FILES
echo ================================================================
echo.
echo This script will remove all Docker-related files since we now use
echo a Python virtual environment solution instead of Docker.
echo.
echo Files to be removed:
echo   - docker-compose.yml
echo   - All Dockerfile files
echo   - All .dockerignore files
echo.
echo Files to keep:
echo   - NO_DOCKER_SOLUTION.md (documentation)
echo   - All .bat startup scripts
echo   - All Python virtual environments
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause
echo.

echo Removing docker-compose.yml...
if exist docker-compose.yml (
    del docker-compose.yml
    echo ✅ Removed docker-compose.yml
) else (
    echo ❌ docker-compose.yml not found
)

echo.
echo Removing Dockerfile files...
for /d %%d in (frontend gateway orchestrator unified_document_service nlp_service rule_engine) do (
    if exist %%d\Dockerfile (
        del %%d\Dockerfile
        echo ✅ Removed %%d\Dockerfile
    ) else (
        echo ❌ %%d\Dockerfile not found
    )
)

echo.
echo Removing .dockerignore files...
for /d %%d in (frontend gateway orchestrator unified_document_service nlp_service rule_engine) do (
    if exist %%d\.dockerignore (
        del %%d\.dockerignore
        echo ✅ Removed %%d\.dockerignore
    ) else (
        echo ❌ %%d\.dockerignore not found
    )
)

echo.
echo ================================================================
echo Docker cleanup completed!
echo.
echo Your project now uses only Python virtual environments.
echo Use start_all_services.bat to run the complete system.
echo.
echo Remaining solution files:
echo   - start_*.bat files
echo   - venv_* directories  
echo   - Python source code
echo   - Documentation files
echo ================================================================
echo.
pause