@echo off
setlocal
cd /d "%~dp0"

start "" ollama serve

timeout /t 3 /nobreak >nul

python -m backend.server
if errorlevel 1 (
    echo.
    echo No se pudo iniciar Chat local. Comprueba que Python y las dependencias esten instalados.
    pause
)
