@echo off
REM NewsInsight Full Stack Startup Script for Windows

echo 🚀 Starting NewsInsight Full Stack Application
echo ==============================================

REM Function to check if port is in use
:check_port
netstat -an | find ":%1 " | find "LISTENING" >nul
if %errorlevel% == 0 (
    echo ⚠️  Port %1 is already in use
    exit /b 1
)
exit /b 0

REM Check prerequisites
echo 🔍 Checking prerequisites...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed
    pause
    exit /b 1
)

node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed
    pause
    exit /b 1
)

npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm is not installed
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo ❌ Virtual environment not found. Run setup-backend.py first.
    pause
    exit /b 1
)

REM Check if node_modules exists
if not exist "node_modules" (
    echo ❌ Node modules not found. Run 'npm install' first.
    pause
    exit /b 1
)

REM Start backend
echo 🔧 Starting Backend Server...
call venv\Scripts\activate
start "NewsInsight Backend" cmd /k "python backend.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

echo ✅ Backend starting on port 8000
echo    API available at: http://localhost:8000
echo    API docs at: http://localhost:8000/docs
echo.

REM Start frontend
echo 🎨 Starting React Frontend...
start "NewsInsight Frontend" cmd /k "npm start"

echo ✅ Frontend starting on port 3000
echo.
echo 🎉 NewsInsight is now starting!
echo ================================
echo 📱 Frontend: http://localhost:3000
echo 🔧 Backend:  http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo Both services are starting in separate windows.
echo Close those windows to stop the services.
echo.
pause