@echo off
chcp 65001 >nul
title BGG Mini-Project - EDA

REM ============================================================
REM  eda.bat - one-click EDA for the BGG mini-project
REM
REM  Finds your Anaconda Python and runs scripts\eda.py
REM  Requires: data\cleaned_games.csv
REM            (run run.bat first, then clean.bat)
REM
REM  Output: 14 charts saved to data\charts\
REM ============================================================

cd /d "%~dp0"

REM --- 1. locate Anaconda Python -------------------------------
set "PY_CMD="
for %%P in (
  "%USERPROFILE%\anaconda3\python.exe"
  "%USERPROFILE%\Anaconda3\python.exe"
  "C:\ProgramData\anaconda3\python.exe"
  "C:\Anaconda3\python.exe"
) do (
  if exist %%P set "PY_CMD=%%~P"
)

REM --- 2. fallback: plain python on PATH ----------------------
if not defined PY_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PY_CMD=python"
)

if not defined PY_CMD (
  echo [ERROR] Python not found.
  echo Install Anaconda or add Python to your PATH.
  pause
  exit /b 1
)

REM --- 3. check the cleaned data exists -----------------------
if not exist "data\cleaned_games.csv" (
  echo [WARN] data\cleaned_games.csv not found.
  echo Run run.bat first, then clean.bat, then try again.
  pause
  exit /b 1
)

REM --- 4. run the EDA ------------------------------------------
echo Using: %PY_CMD%
echo Running EDA - takes about a minute...
echo Charts will be saved to data\charts\
echo.

"%PY_CMD%" scripts\eda.py

if errorlevel 1 (
  echo.
  echo Something went wrong - check the messages above.
) else (
  echo.
  echo EDA finished! Open data\charts\ to see the 14 charts.
)
pause