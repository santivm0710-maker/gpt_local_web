@echo off
setlocal
cd /d "%~dp0"
python -m backend.server
if errorlevel 1 (
    echo.
    echo No se pudo iniciar Chat local. Comprueba que Python y las dependencias esten instalados.
    pause
)
