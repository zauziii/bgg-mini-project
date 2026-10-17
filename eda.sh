#!/usr/bin/env bash
# ============================================================
#  eda.sh - exploratory data analysis for the BGG mini-project
#
#  Finds Python, makes sure the plotting libraries are
#  installed, then runs:
#      python scripts/eda.py
#
#  Requires: data/cleaned_games.csv   (run run.sh, then clean.sh)
#  Output:   14 charts saved to data/charts/
# ============================================================

cd "$(dirname "$0")" || exit 1

# --- 1. locate Python ---------------------------------------
if command -v python3 >/dev/null 2>&1; then
  PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PY_CMD="python"
else
  echo "[ERROR] Python not found."
  echo "Install Python from https://www.python.org/downloads/"
  exit 1
fi

# --- 2. check the cleaned data exists -----------------------
if [ ! -f "data/cleaned_games.csv" ]; then
  echo "[ERROR] data/cleaned_games.csv not found."
  echo "Run run.sh first, then clean.sh, then try again."
  exit 1
fi

# --- 2b. check the EDA script exists ------------------------
if [ ! -f "scripts/eda.py" ]; then
  echo "[ERROR] scripts/eda.py not found."
  exit 1
fi

# --- 3. make sure the plotting libraries are installed ------
if ! "$PY_CMD" -c "import pandas, numpy, matplotlib" >/dev/null 2>&1; then
  echo "Plotting libraries not found - installing for the first time..."
  if ! "$PY_CMD" -m pip install pandas numpy matplotlib; then
    echo "[ERROR] Could not install dependencies."
    echo "Try manually:  $PY_CMD -m pip install pandas numpy matplotlib"
    exit 1
  fi
fi

# --- 4. run the EDA -----------------------------------------
echo "Using: $PY_CMD"
echo "Running EDA - takes about a minute..."
echo "Charts will be saved to data/charts/"
echo
if "$PY_CMD" scripts/eda.py; then
  echo
  echo "SUCCESS! EDA finished. Open data/charts/ to see the 14 charts."
else
  rc=$?
  echo
  echo "Exit code: $rc"
  echo "[ERROR] EDA failed - check the messages above."
  exit $rc
fi