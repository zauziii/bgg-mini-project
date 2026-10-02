@echo off
title BGG data downloader
cd /d "%~dp0"

REM --- 1. try Anaconda first, then any Python on PATH ---
set "PY_CMD="
for %%P in (
  "%USERPROFILE%\anaconda3\python.exe"
  "%USERPROFILE%\miniconda3\python.exe"
  "C:\ProgramData\Anaconda3\python.exe"
  "C:\Anaconda3\python.exe"
) do (
  if exist %%P set "PY_CMD=%%~P"
)
if not defined PY_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PY_CMD=python"
)
if not defined PY_CMD (
  echo [ERROR] Python not found.
  echo Install Python from https://www.python.org/downloads/
  echo and check "Add Python to PATH" during install.
  pause
  exit /b 1
)

REM --- 2. get the API token ---
if "%BGG_API_TOKEN%"=="" (
    set /p BGG_API_TOKEN=Enter your BGG API token: 
)

echo Using: %PY_CMD%
echo Starting download (about 20 minutes)...
echo.

"%PY_CMD%" scripts\fetch_bgg.py --out data

echo.
echo Exit code: %errorlevel%
if errorlevel 1 (
    echo FAILED - check the messages above for the reason.
) else (
    echo SUCCESS! Your data is in the data\games.csv file.
)
pause