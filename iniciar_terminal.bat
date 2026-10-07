@echo off
cd /d "%~dp0"

:: Ativa o venv se existir
if exist "venv\Scripts\activate.bat" call "venv\Scripts\activate.bat"

:: Abre o navegador
start http://localhost:8000

:: Inicia o Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000