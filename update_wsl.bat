@echo off
echo Обновление WSL требует прав администратора...
echo.
echo Выполните эту команду в PowerShell от имени администратора:
echo.
echo     wsl --update --web-download
echo.
echo После обновления WSL выполните:
echo     wsl --install -d Ubuntu
echo.
echo Затем перезапустите Docker Desktop
echo.
pause