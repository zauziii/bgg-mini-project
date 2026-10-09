@echo off
chcp 65001 >nul
title BGG Mini-Project - ML (3 Parts)
cd /d "%~dp0"

REM ============================================================
REM  ml_parts.bat - run the THREE split ML scripts, one after
REM  the other (each group member's part):
REM
REM     1) ml_part1_regression.py            (Aoxue Li)
REM     2) ml_part2_classification.py        (Ezeme Onyenezi Innocent)
REM     3) ml_part3_recommender.py           (Zhi Zhou)
REM
REM  Optional (Member 2's extra text task - uncomment below):
REM     scripts\ml_part2_discriminative_words.py
REM
REM  Requires: data\cleaned_games.csv   (run run.bat, then clean.bat)
REM
REM  Outputs:
REM     data\ml_charts\01_model_comparison.png
REM     data\ml_charts\02_feature_importance.png
REM     data\ml_charts\03_confusion_matrix.png
REM     data\recommendation_scores.csv
REM     data\similar_games.csv
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

REM --- 2b. check the ML scripts exist --------------------------
if not exist "scripts\ml_part1_regression.py" (
  echo [ERROR] scripts\ml_part1_regression.py not found.
  pause
  exit /b 1
)
if not exist "scripts\ml_part2_classification.py" (
  echo [ERROR] scripts\ml_part2_classification.py not found.
  pause
  exit /b 1
)
if not exist "scripts\ml_part3_recommender.py" (
  echo [ERROR] scripts\ml_part3_recommender.py not found.
  pause
  exit /b 1
)

REM --- 3. make sure the ML libraries are installed -------------
"%PY_CMD%" -c "import pandas, numpy, matplotlib, sklearn, scipy" >nul 2>nul
if errorlevel 1 (
  echo ML libraries not found - installing for the first time...
  "%PY_CMD%" -m pip install pandas numpy matplotlib scikit-learn scipy
  if errorlevel 1 (
    echo [ERROR] Could not install ML libraries.
    echo Try manually:  "%PY_CMD%" -m pip install pandas numpy matplotlib scikit-learn scipy
    pause
    exit /b 1
  )
)

REM --- 4. run the three parts, one after the other -------------
echo Using: %PY_CMD%
echo.

echo ============================================================
echo PART 1/3 - Aoxue Li: regression (predict popularity)
echo ============================================================
"%PY_CMD%" scripts\ml_part1_regression.py
if errorlevel 1 (
  echo [ERROR] Part 1 failed - check the messages above.
  pause
  exit /b 1
)
echo.

echo ============================================================
echo PART 2/3 - Ezeme Onyenezi Innocent: classification (good-game classifier)
echo ============================================================
"%PY_CMD%" scripts\ml_part2_classification.py
if errorlevel 1 (
  echo [ERROR] Part 2 failed - check the messages above.
  pause
  exit /b 1
)
echo.

REM --- Ezeme Onyenezi Innocent's text task (small, ~30 s) ------
REM Uncomment the next 3 lines to also run it:
REM echo ============================================================
REM echo Ezeme Onyenezi Innocent: discriminative words per category
REM echo ============================================================
REM "%PY_CMD%" scripts\ml_part2_discriminative_words.py

echo ============================================================
echo PART 3/3 - Zhi Zhou: recommender + similar games
echo ============================================================
"%PY_CMD%" scripts\ml_part3_recommender.py
if errorlevel 1 (
  echo [ERROR] Part 3 failed - check the messages above.
  pause
  exit /b 1
)
echo.

echo ============================================================
echo All three parts finished!
echo   Charts:  data\ml_charts\
echo   Web app: data\recommendation_scores.csv + data\similar_games.csv
echo ============================================================
pause