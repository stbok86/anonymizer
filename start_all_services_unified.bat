@echo off
REM ============================================================================
REM Document Anonymizer - Unified Terminal Launcher
REM Запускает PowerShell скрипт в одном окне
REM ============================================================================

REM Запускаем PowerShell скрипт
PowerShell.exe -ExecutionPolicy Bypass -File "%~dp0start_all_services_unified.ps1"

REM Если PowerShell недоступен или возникла ошибка, показываем сообщение
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to run PowerShell script
    echo.
    echo Please try running start_all_services.bat instead
    echo or execute: PowerShell.exe -ExecutionPolicy Bypass -File start_all_services_unified.ps1
    echo.
    pause
)
