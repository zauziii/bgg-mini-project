@echo off
chcp 65001 >nul
title BGG Mini-Project - Combine Charts
cd /d "%~dp0"

REM ============================================================
REM  combine_charts.bat - combine EDA / ML charts into the three
REM  combined figures used in the technical report.
REM  Output: data\combined\fig1_evaluation.png
REM          data\combined\fig2_importance.png
REM          data\combined\fig3_eda_distributions.png
REM  To change what gets combined, edit the call below or run:
REM      python scripts\combine_charts.py --help
REM ============================================================

REM --- 1. locate Python (Anaconda first, then PATH) ---
set "PY_CMD="
if exist "%USERPROFILE%\anaconda3\python.exe" set "PY_CMD=%USERPROFILE%\anaconda3\python.exe"
if exist "%USERPROFILE%\miniconda3\python.exe" set "PY_CMD=%USERPROFILE%\miniconda3\python.exe"
if exist "C:\ProgramData\Anaconda3\python.exe" set "PY_CMD=C:\ProgramData\Anaconda3\python.exe"
if exist "C:\Anaconda3\python.exe" set "PY_CMD=C:\Anaconda3\python.exe"
if not "%PY_CMD%"=="" goto pyfound

where python >nul 2>nul
if errorlevel 1 goto nopython
set "PY_CMD=python"

:pyfound
REM --- 2. check the chart folders exist ---
if exist "data\charts" goto chartsok
echo [ERROR] data\charts not found.
echo Make sure you are in the project root (bbg-mini-project).
pause
exit /b 1

:chartsok
if exist "data\ml_charts" goto mlok
echo [ERROR] data\ml_charts not found.
pause
exit /b 1

:mlok
REM --- 3. make sure Pillow is installed ---
"%PY_CMD%" -c "import PIL" >nul 2>nul
if errorlevel 1 goto install_deps
goto depsok

:install_deps
echo Pillow not found - installing for the first time...
"%PY_CMD%" -m pip install pillow
if errorlevel 1 goto depsfail
goto depsok

:depsfail
echo [ERROR] Could not install Pillow.
echo Try manually:  "%PY_CMD%" -m pip install pillow
pause
exit /b 1

:depsok
REM --- 4. combine the three report figures ---
echo Using: %PY_CMD%
echo Combining charts - the three report figures will be saved to data\combined\
echo.
"%PY_CMD%" scripts\combine_charts.py --report all
echo.
echo Exit code: %errorlevel%
if errorlevel 1 goto combfail
echo SUCCESS! See data\combined\ for:
echo   fig3_eda_distributions.png   (EDA, report Figure 1)
echo   fig1_evaluation.png          (model evaluation, report Figure 2)
echo   fig2_importance.png          (feature importance, report Figure 3)
pause
exit /b 0

:combfail
echo [ERROR] Combining failed - check the messages above.
pause
exit /b 1

:nopython
echo [ERROR] Python not found.
echo Install Python from https://www.python.org/downloads/
echo and tick "Add Python to PATH" during install.
pause
exit /b 1
