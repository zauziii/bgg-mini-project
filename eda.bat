@echo off
chcp 65001 >nul
title BGG Mini-Project - EDA
cd /d "%~dp0"

REM ============================================================
REM  eda.bat - exploratory data analysis for the BGG mini-project
REM
REM  Finds Python, makes sure the plotting libraries are
REM  installed, then runs:
REM      python scripts\eda.py
REM
REM  Requires: data\cleaned_games.csv   (run run.bat, then clean.bat)
REM  Output:   14 charts saved to data\charts\
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

REM --- 2. check the cleaned data exists ------------------------
if not exist "data\cleaned_games.csv" (
  echo [ERROR] data\cleaned_games.csv not found.
  echo Run run.bat first, then clean.bat, then try again.
  pause
  exit /b 1
)

REM --- 2b. check the EDA script exists -------------------------
if not exist "scripts\eda.py" (
  echo [ERROR] scripts\eda.py not found.
  pause
  exit /b 1
)

REM --- 3. make sure the plotting libraries are installed -------
"%PY_CMD%" -c "import pandas, numpy, matplotlib" >nul 2>nul
if errorlevel 1 (
  echo Plotting libraries not found - installing for the first time...
  "%PY_CMD%" -m pip install pandas numpy matplotlib
  if errorlevel 1 (
    echo [ERROR] Could not install dependencies.
    echo Try manually:  "%PY_CMD%" -m pip install pandas numpy matplotlib
    pause
    exit /b 1
  )
)

REM --- 4. run the EDA ------------------------------------------
echo Using: %PY_CMD%
echo Running EDA - takes about a minute...
echo Charts will be saved to data\charts\
echo.
"%PY_CMD%" scripts\eda.py
echo.
echo Exit code: %errorlevel%
if errorlevel 1 (
  echo [ERROR] EDA failed - check the messages above.
) else (
  echo SUCCESS! EDA finished. Open data\charts\ to see the 14 charts.
)
pause