@echo off
chcp 65001 >nul 2>&1
title Arabic Book Analyzer - برنامج تحليل الكتب العربية
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║     برنامج تحليل الكتب العربية بالذكاء الاصطناعي      ║
echo ║     Arabic Book Analyzer - Local AI Analysis            ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

:: ── Check Python ──────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH.
    echo          Telechargez Python depuis: https://python.org
    echo          Cochez "Add Python to PATH" lors de l'installation.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version') do echo [OK] %%v detecte

:: ── Check pip ──────────────────────────────────────────────────
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] pip n'est pas disponible.
    pause
    exit /b 1
)
echo [OK] pip disponible

:: ── Create virtual environment if needed ───────────────────────
if not exist "venv" (
    echo.
    echo [*] Creation de l'environnement virtuel...
    python -m venv venv
    if errorlevel 1 (
        echo [ERREUR] Impossible de creer l'environnement virtuel.
        pause
        exit /b 1
    )
    echo [OK] Environnement virtuel cree
)

:: ── Activate virtual environment ───────────────────────────────
call venv\Scripts\activate.bat
echo [OK] Environnement virtuel active

:: ── Install/upgrade dependencies ──────────────────────────────
echo.
echo [*] Verification des dependances...
pip install --upgrade pip -q
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [ERREUR] Erreur lors de l'installation des dependances.
    pause
    exit /b 1
)
echo [OK] Toutes les dependances sont installees

:: ── Check Ollama ──────────────────────────────────────────────
echo.
echo [*] Verification d'Ollama...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo [ATTENTION] Ollama n'est pas detecte dans le PATH.
    echo             Assurez-vous qu'Ollama est installe et demarre.
    echo             Telechargement: https://ollama.com
    echo.
    echo             Appuyez sur une touche pour continuer quand meme...
    pause >nul
) else (
    for /f "tokens=*" %%v in ('ollama --version') do echo [OK] %%v detecte
    
    :: Check if model is available
    ollama list | findstr /i "llama3" >nul 2>&1
    if errorlevel 1 (
        echo.
        echo [*] Le modele llama3 n'est pas trouve. Telechargement...
        echo     Cela peut prendre plusieurs minutes...
        ollama pull llama3
        if errorlevel 1 (
            echo [ATTENTION] Impossible de telecharger le modele automatiquement.
            echo             Executez manuellement: ollama pull llama3
        ) else (
            echo [OK] Modele llama3 pret
        )
    ) else (
        echo [OK] Modele llama3 disponible
    )
)

:: ── Create data directories ───────────────────────────────────
if not exist "data" mkdir data
if not exist "data\index" mkdir data\index
if not exist "data\chroma_db" mkdir data\chroma_db
if not exist "data\exports" mkdir data\exports

:: ── Launch application ────────────────────────────────────────
echo.
echo ══════════════════════════════════════════════════════════
echo   Lancement de l'application...
echo ══════════════════════════════════════════════════════════
echo.

python main.py

:: ── On exit ───────────────────────────────────────────────────
echo.
echo [*] L'application est fermee.
call venv\Scripts\deactivate.bat >nul 2>&1
pause
