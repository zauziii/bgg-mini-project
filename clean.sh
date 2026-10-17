#!/usr/bin/env bash
# ============================================================
#  clean.sh - clean the downloaded BGG data
#
#  Finds Python, makes sure pandas is installed, then runs:
#      python clean_bgg_data.py
#
#  Requires: data/games.csv        (run run.sh first)
#  Output:   data/cleaned_games.csv
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

# --- 2. check the raw data exists ---------------------------
if [ ! -f "data/games.csv" ]; then
  echo "[ERROR] data/games.csv not found."
  echo "Run run.sh first to download the data."
  exit 1
fi

# --- 3. make sure pandas is installed -----------------------
if ! "$PY_CMD" -c "import pandas" >/dev/null 2>&1; then
  echo "pandas not found - installing for the first time..."
  if ! "$PY_CMD" -m pip install pandas; then
    echo "[ERROR] Could not install pandas."
    echo "Try manually:  $PY_CMD -m pip install pandas"
    exit 1
  fi
fi

# --- 4. locate clean_bgg_data.py (prefer scripts/) ----------
CLEAN_SCRIPT=""
if [ -f "scripts/clean_bgg_data.py" ]; then
  CLEAN_SCRIPT="scripts/clean_bgg_data.py"
elif [ -f "clean_bgg_data.py" ]; then
  CLEAN_SCRIPT="clean_bgg_data.py"
fi
if [ -z "$CLEAN_SCRIPT" ]; then
  echo "[ERROR] clean_bgg_data.py not found."
  echo "Put it in the project root or in scripts/."
  exit 1
fi

# --- 5. run the cleaning pipeline ---------------------------
echo "Using: $PY_CMD"
echo "Cleaning data/games.csv ..."
echo
if "$PY_CMD" "$CLEAN_SCRIPT"; then
  echo
  echo "SUCCESS! Your cleaned data is in data/cleaned_games.csv"
else
  rc=$?
  echo
  echo "Exit code: $rc"
  echo "[ERROR] Cleaning failed - check the messages above."
  exit $rc
fi