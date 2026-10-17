#!/usr/bin/env bash
# ============================================================
#  run.sh - download BGG board game data
#
#  Finds Python, asks for your BGG API token, then runs:
#      python scripts/fetch_bgg.py --out data
#
#  Output: data/games.csv  (raw XML cache in data/raw/)
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

# --- 2. get the BGG API token -------------------------------
if [ -z "$BGG_API_TOKEN" ]; then
  read -r -p "Enter your BGG API token: " BGG_API_TOKEN
fi
if [ -z "$BGG_API_TOKEN" ]; then
  echo "[ERROR] No token entered. Please run again and paste your BGG API token."
  echo "You can also set it in advance:  export BGG_API_TOKEN=your-token"
  exit 1
fi
export BGG_API_TOKEN

# --- 3. run the downloader ----------------------------------
echo "Using: $PY_CMD"
echo "Starting download (about 20 minutes)..."
echo
if "$PY_CMD" scripts/fetch_bgg.py --out data; then
  echo
  echo "SUCCESS! Your data is in the data/games.csv file."
else
  rc=$?
  echo
  echo "Exit code: $rc"
  echo "[ERROR] Download failed - check the messages above."
  exit $rc
fi