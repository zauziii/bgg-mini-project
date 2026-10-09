@echo off
chcp 65001 >nul
title BGG Mini-Project - Clean Data
cd /d "%~dp0"

REM ============================================================
REM  clean.bat - clean the downloaded BGG data
REM
REM  Finds Python, makes sure pandas is installed, then runs:
REM      python clean_bgg_data.py
REM
REM  Requires: data\games.csv        (run run.bat first)
REM  Output:   data\cleaned_games.csv
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

REM --- 2. check the raw data exists ----------------------------
if not exist "data\games.csv" (
  echo [ERROR] data\games.csv not found.
  echo Run run.bat first to download the data.
  pause
  exit /b 1
)

REM --- 3. make sure pandas is installed ------------------------
"%PY_CMD%" -c "import pandas" >nul 2>nul
if errorlevel 1 (
  echo pandas not found - installing for the first time...
  "%PY_CMD%" -m pip install pandas
  if errorlevel 1 (
    echo [ERROR] Could not install pandas.
    echo Try manually:  "%PY_CMD%" -m pip install pandas
    pause
    exit /b 1
  )
)

REM --- 4. locate clean_bgg_data.py (prefer scripts\) -----------
set "CLEAN_SCRIPT="
if exist "scripts\clean_bgg_data.py" (
  set "CLEAN_SCRIPT=scripts\clean_bgg_data.py"
) else if exist "clean_bgg_data.py" (
  set "CLEAN_SCRIPT=clean_bgg_data.py"
)
if not defined CLEAN_SCRIPT (
  echo [ERROR] clean_bgg_data.py not found.
  echo Put it in the project root or in scripts\.
  pause
  exit /b 1
)

REM --- 5. run the cleaning pipeline ----------------------------
echo Using: %PY_CMD%
echo Cleaning data\games.csv ...
echo.
"%PY_CMD%" "%CLEAN_SCRIPT%"
echo.
echo Exit code: %errorlevel%
if errorlevel 1 (
  echo [ERROR] Cleaning failed - check the messages above.
) else (
  echo SUCCESS! Your cleaned data is in data\cleaned_games.csv
)
pause