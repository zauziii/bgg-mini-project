@echo off
title BGG data downloader (Anaconda)
cd /d "%~dp0"

REM --- find the Anaconda python.exe ---
set PY_CMD=
if exist "%USERPROFILE%\anaconda3\python.exe" set PY_CMD=%USERPROFILE%\anaconda3\python.exe
if exist "%USERPROFILE%\miniconda3\python.exe" set PY_CMD=%USERPROFILE%\miniconda3\python.exe
if exist "C:\ProgramData\Anaconda3\python.exe" set PY_CMD=C:\ProgramData\Anaconda3\python.exe
if exist "C:\Anaconda3\python.exe" set PY_CMD=C:\Anaconda3\python.exe
if "%PY_CMD%"=="" (
    echo [ERROR] Anaconda python.exe not found in the usual places.
    echo Open Anaconda Prompt instead and run:
    echo   python scripts\fetch_bgg.py --out data
    pause
    exit /b 1
)

REM --- get the API token ---
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