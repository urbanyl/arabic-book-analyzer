@echo off
chcp 65001 >nul 2>&1
title Arabic Book Analyzer
color 0A

echo.
echo ==========================================================
echo       Arabic Book Analyzer - Local AI Analysis
echo ==========================================================
echo.

cd /d "%~dp0"

:: -- Check Python --
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    echo         Download from: https://python.org
    echo         Check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version') do echo [OK] %%v detected

:: -- Check pip --
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip not available.
    pause
    exit /b 1
)
echo [OK] pip available

:: -- Create virtual environment if needed --
if not exist "venv" (
    echo.
    echo [*] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)

:: -- Activate virtual environment --
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated

:: -- Install/upgrade dependencies --
echo.
echo [*] Checking dependencies...
python -m pip install --upgrade pip --quiet 2>nul
python -m pip install -r requirements.txt --quiet --no-cache-dir
if errorlevel 1 (
    echo [ERROR] Error installing dependencies.
    pause
    exit /b 1
)
echo [OK] All dependencies installed

:: -- Check Ollama --
echo.
echo [*] Checking Ollama...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama not detected in PATH.
    echo           Make sure Ollama is installed and running.
    echo           Download: https://ollama.com
    echo.
    echo           Press any key to continue anyway...
    pause >nul
) else (
    for /f "tokens=*" %%v in ('ollama --version') do echo [OK] %%v detected
    
    ollama list 2>nul | findstr /i "llama3" >nul 2>&1
    if errorlevel 1 (
        echo.
        echo [*] Model llama3 not found. Downloading...
        echo     This may take several minutes...
        ollama pull llama3
        if errorlevel 1 (
            echo [WARNING] Could not download model automatically.
            echo           Run manually: ollama pull llama3
        ) else (
            echo [OK] Model llama3 ready
        )
    ) else (
        echo [OK] Model llama3 available
    )
)

:: -- Create data directories --
if not exist "data" mkdir data
if not exist "data\index" mkdir data\index
if not exist "data\chroma_db" mkdir data\chroma_db
if not exist "data\exports" mkdir data\exports

:: -- Launch application --
echo.
echo ==========================================================
echo   Launching application...
echo ==========================================================
echo.

python main.py

:: -- On exit --
echo.
echo [*] Application closed.
call venv\Scripts\deactivate.bat >nul 2>&1
pause
