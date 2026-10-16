@echo off
title ObjectLens
cd /d "%~dp0"

rem ---- 1. virtual environment (first run only) ----
if not exist venv\Scripts\python.exe (
    echo First run: creating virtual environment...
    python -m venv venv
    if errorlevel 1 goto nopython
)
call venv\Scripts\activate.bat

rem ---- 2. install packages (first run only, 5-10 minutes) ----
if not exist venv\installed.txt (
    echo Installing packages. This takes a few minutes...
    python -m pip install --upgrade pip
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    if errorlevel 1 goto fail
    pip install -r requirements.txt
    if errorlevel 1 goto fail
    echo ok> venv\installed.txt
)

rem ---- 3. start the app and open the browser ----
echo.
echo Starting ObjectLens. Keep this window open while you use the site.
echo Close this window to stop the app.
start "" cmd /c "timeout /t 10 >nul & start http://127.0.0.1:5000"
python app.py
pause
goto :eof

:nopython
echo.
echo Python was not found. Install Python 3.10, 3.11 or 3.12 from python.org
echo and tick "Add Python to PATH" during installation. Then run this again.
pause
goto :eof

:fail
echo.
echo Something went wrong above. Copy the red error text and ask for help.
pause
