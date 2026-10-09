@echo off
chcp 65001 >nul
title BGG Mini-Project - Web App
cd /d "%~dp0"

REM ============================================================
REM  run_webapp.bat - launch the interactive web app
REM  Simple style (same as run_webapp_debug.bat - proven to work).
REM  Starts streamlit and opens your browser automatically.
REM  Keep this window OPEN while you use the app.
REM ============================================================

REM --- 1. locate Python (first found wins) ---------------------
set "PY_CMD="
if not defined PY_CMD if exist "%USERPROFILE%\anaconda3\python.exe" set "PY_CMD=%USERPROFILE%\anaconda3\python.exe"
if not defined PY_CMD if exist "%USERPROFILE%\miniconda3\python.exe" set "PY_CMD=%USERPROFILE%\miniconda3\python.exe"
if not defined PY_CMD if exist "C:\ProgramData\Anaconda3\python.exe" set "PY_CMD=C:\ProgramData\Anaconda3\python.exe"
if not defined PY_CMD if exist "C:\Anaconda3\python.exe" set "PY_CMD=C:\Anaconda3\python.exe"
if not defined PY_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PY_CMD=python"
)
if not defined PY_CMD goto nopython

echo Using: %PY_CMD%

REM --- 2. check the files the app needs ---
if exist "data\cleaned_games.csv" goto file2
echo [ERROR] data\cleaned_games.csv not found.
echo Run run.bat first, then clean.bat.
pause
exit /b 1

:file2
if exist "data\similar_games.csv" goto file3
echo [ERROR] data\similar_games.csv not found.
echo Run ml_parts.bat first (Part 3 creates it).
pause
exit /b 1

:file3
if exist "webapp\app.py" goto filesok
echo [ERROR] webapp\app.py not found.
pause
exit /b 1

:filesok
REM --- 3. make sure streamlit is installed ---
"%PY_CMD%" -c "import streamlit" >nul 2>nul
if errorlevel 1 goto install_sl
goto sl_ok

:install_sl
echo streamlit not found - installing for the first time...
"%PY_CMD%" -m pip install streamlit
if errorlevel 1 goto sl_fail
goto sl_ok

:sl_fail
echo [ERROR] Could not install streamlit.
echo Try manually:  "%PY_CMD%" -m pip install streamlit
pause
exit /b 1

:sl_ok
REM --- 4. launch the app (streamlit opens your browser once) ---
echo.
echo Starting the web app...
echo Your browser will open automatically in a few seconds.
echo IMPORTANT: keep this black window OPEN while using the app.
echo Close this window (or press Ctrl+C) when you are done.
echo.

"%PY_CMD%" -m streamlit run webapp\app.py

echo.
echo The app has stopped.
pause
exit /b 0

:nopython
echo [ERROR] Python not found.
echo Install Python from https://www.python.org/downloads/
echo and tick "Add Python to PATH" during install.
pause
exit /b 1