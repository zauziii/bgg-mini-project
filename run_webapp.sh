#!/usr/bin/env bash
# ============================================================
#  run_webapp.sh - launch the interactive web app
#
#  Starts streamlit and opens your browser automatically.
#  Keep this terminal OPEN while you use the app.
#  Press Ctrl+C when you are done.
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

echo "Using: $PY_CMD"

# --- 2. check the files the app needs -----------------------
if [ ! -f "data/cleaned_games.csv" ]; then
  echo "[ERROR] data/cleaned_games.csv not found."
  echo "Run run.sh first, then clean.sh."
  exit 1
fi

if [ ! -f "data/similar_games.csv" ]; then
  echo "[ERROR] data/similar_games.csv not found."
  echo "Run ml_parts.sh first (Part 3 creates it)."
  exit 1
fi

if [ ! -f "webapp/app.py" ]; then
  echo "[ERROR] webapp/app.py not found."
  exit 1
fi

# --- 3. make sure streamlit is installed --------------------
if ! "$PY_CMD" -c "import streamlit" >/dev/null 2>&1; then
  echo "streamlit not found - installing for the first time..."
  if ! "$PY_CMD" -m pip install streamlit; then
    echo "[ERROR] Could not install streamlit."
    echo "Try manually:  $PY_CMD -m pip install streamlit"
    exit 1
  fi
fi

# --- 4. launch the app (streamlit opens your browser once) --
echo
echo "Starting the web app..."
echo "Your browser will open automatically in a few seconds."
echo "IMPORTANT: keep this terminal OPEN while using the app."
echo "Press Ctrl+C when you are done."
echo

"$PY_CMD" -m streamlit run webapp/app.py

echo
echo "The app has stopped."