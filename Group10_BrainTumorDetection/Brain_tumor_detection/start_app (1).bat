@echo off
setlocal
title Brain Tumor Detection - Launcher
cd /d "%~dp0"

echo ==========================================
echo   Brain Tumor Detection
echo ==========================================
echo.

if not exist "backend\venv\Scripts\activate.bat" (
    echo ERROR: Backend virtual environment not found:
    echo   backend\venv\Scripts\activate.bat
    echo.
    pause
    exit /b 1
)

if not exist "frontend\package.json" (
    echo ERROR: Frontend package.json not found.
    echo.
    pause
    exit /b 1
)

echo Starting backend at http://127.0.0.1:8000 ...
start "Brain Tumor Backend" cmd /k "cd /d ""%~dp0backend"" && call venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload"

timeout /t 3 /nobreak >nul

echo Starting frontend at http://localhost:5174 ...
start "Brain Tumor Frontend" cmd /k "cd /d ""%~dp0frontend"" && npm run dev -- --host 127.0.0.1 --port 5174"

timeout /t 4 /nobreak >nul
start "" "http://localhost:5174/"

echo.
echo Startup commands sent.
echo Keep both server windows open while using the app.
echo If Vite chooses a different port, use the Local URL shown in its window.
pause
endlocal
