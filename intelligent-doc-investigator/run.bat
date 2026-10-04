@echo off
TITLE DocInvestigator - Intelligent Document Investigator (ALG-AI-02)
echo =====================================================================
echo  Starting Intelligent Document Investigator (Algothon '26 ALG-AI-02)
echo =====================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was not found in your system PATH.
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

echo Starting application server on http://localhost:8000 ...
python app.py
pause
