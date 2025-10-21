@echo off
REM Windows startup script
REM Usage: start.bat

echo.
echo 🚀 NewsInsight.ai Startup Script
echo ================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python found: %PYTHON_VERSION%
echo.

REM Check venv
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

echo ✓ Virtual environment exists
echo.

REM Activate venv
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate venv
    exit /b 1
)

echo ✓ Activated venv
echo.

REM Install dependencies
echo 📚 Installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ⚠️  Some dependencies failed to install (may still work)
)
echo ✓ Dependencies installed
echo.

REM Set defaults
if not defined AWS_REGION set AWS_REGION=us-west-2
if not defined DDB_TABLE set DDB_TABLE=news_metadata
if not defined DEBUG_MODE set DEBUG_MODE=false

echo ⚙️  Configuration:
echo    AWS_REGION: %AWS_REGION%
echo    DDB_TABLE: %DDB_TABLE%
echo    DEBUG_MODE: %DEBUG_MODE%
echo.

echo 🔍 Checking AWS credentials...
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo ⚠️  AWS credentials not found
    echo    Run: aws configure
) else (
    echo ✓ AWS credentials found
)
echo.

REM Start Streamlit
echo 🎯 Starting Streamlit app...
echo    Open: http://localhost:8501
echo    Press Ctrl+C to stop
echo.

streamlit run app.py
