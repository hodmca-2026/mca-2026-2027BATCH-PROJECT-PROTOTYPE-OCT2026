@echo off
setlocal EnableDelayedExpansion
title Market AI Platform [RUNNING]
color 0B
cd /d "%~dp0"

echo ===============================================================================
echo            MARKET AI - STOCK AND CRYPTO PREDICTION PLATFORM
echo ===============================================================================
echo.
echo [1/3] Checking environment prerequisites...

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found in your system PATH!
    echo Please install Python 3.10+ and add it to PATH.
    echo.
    pause
    exit /b 1
)

node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js was not found in your system PATH!
    echo Please install Node.js and npm to run the frontend.
    echo.
    pause
    exit /b 1
)

echo [OK] Python and Node.js detected.
echo.

echo [2/3] Checking Backend Service on Port 8000...
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo [LAUNCH] Starting Backend Server...
    start "Market AI Backend" /min cmd /k "cd /d "%~dp0" && python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"
    timeout /t 3 /nobreak >nul
) else (
    echo [OK] Backend is already running on port 8000.
)

echo.
echo [3/3] Checking Frontend Service on Port 5173...
netstat -ano | findstr ":5173" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo [LAUNCH] Starting Frontend UI...
    start "Market AI Frontend" /min cmd /k "cd /d "%~dp0frontend" && npm run dev -- --host 127.0.0.1 --port 5173"
    timeout /t 3 /nobreak >nul
) else (
    echo [OK] Frontend is already running on port 5173.
)

echo.
echo Launching Market AI in your default web browser...
start http://localhost:5173

cls
echo ===============================================================================
echo            MARKET AI - STOCK AND CRYPTO PREDICTION PLATFORM
echo ===============================================================================
echo.
echo  [STATUS] MARKET AI IS ACTIVELY RUNNING!
echo.
echo  - Frontend Web App:   http://localhost:5173
echo  - Backend API:        http://127.0.0.1:8000
echo  - Swagger API Docs:   http://127.0.0.1:8000/docs
echo.
echo ===============================================================================
echo  KEEP THIS WINDOW OPEN!
echo  This window keeps Market AI online. It will NOT close automatically.
echo.
echo  To STOP the platform:
echo  Simply close this window or press Ctrl+C.
echo ===============================================================================
echo.

:loop
echo [%time:~0,8%] Market AI is running. Type Q and press Enter to stop, or keep this window open:
set /p USER_INPUT="> "
if /i "%USER_INPUT%"=="Q" goto shutdown
goto loop

:shutdown

echo.
echo Stopping services...
for /f "tokens=5" %%p in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /f /pid %%p >nul 2>&1
for /f "tokens=5" %%p in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do taskkill /f /pid %%p >nul 2>&1
echo [OK] Services stopped cleanly.
timeout /t 2 /nobreak >nul
exit /b 0
