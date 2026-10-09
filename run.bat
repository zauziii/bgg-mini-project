@echo off
chcp 65001 >nul
title BGG Mini-Project - Download Data
cd /d "%~dp0"

REM ============================================================
REM  run.bat - download BGG board game data
REM
REM  Finds Python (Anaconda first, then any Python on PATH),
REM  asks for your BGG API token, then runs:
REM      python scripts\fetch_bgg.py --out data
REM
REM  Output: data\games.csv  (raw XML cache in data\raw\)
REM ============================================================

REM --- 1. locate Python (Anaconda first, then PATH) ------------
set "PY_CMD="
for %%P in (
  "%USERPROFILE%\anaconda3\python.exe"
  "%USERPROFILE%\miniconda3\python.exe"
  "C:\ProgramData\Anaconda3\python.exe"
  "C:\Anaconda3\python.exe"
) do (
  if not defined PY_CMD if exist %%P set "PY_CMD=%%~P"
)
if not defined PY_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PY_CMD=python"
)
if not defined PY_CMD (
  echo [ERROR] Python not found.
  echo Install Python from https://www.python.org/downloads/
  echo and tick "Add Python to PATH" during install.
  pause
  exit /b 1
)

REM --- 2. get the BGG API token --------------------------------
if not defined BGG_API_TOKEN (
  set /p BGG_API_TOKEN=Enter your BGG API token: 
)
if not defined BGG_API_TOKEN (
  echo [ERROR] No token entered. Please run again and paste your BGG API token.
  echo You can also set it in advance:  set BGG_API_TOKEN=your-token
  pause
  exit /b 1
)

REM --- 3. run the downloader -----------------------------------
echo Using: %PY_CMD%
echo Starting download (about 20 minutes)...
echo.
"%PY_CMD%" scripts\fetch_bgg.py --out data
echo.
echo Exit code: %errorlevel%
if errorlevel 1 (
  echo [ERROR] Download failed - check the messages above.
) else (
  echo SUCCESS! Your data is in the data\games.csv file.
)
pause