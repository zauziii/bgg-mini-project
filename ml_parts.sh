#!/usr/bin/env bash
# ============================================================
#  ml_parts.sh - run the THREE split ML scripts, one after
#  the other (each group member's part):
#
#     1) ml_part1_regression.py            (Aoxue Li)
#     2) ml_part2_classification.py        (Ezeme Onyenezi Innocent)
#     3) ml_part3_recommender.py           (Zhi Zhou)
#
#  Optional (Member 2's extra text task - uncomment below):
#     scripts/ml_part2_discriminative_words.py
#
#  Requires: data/cleaned_games.csv   (run run.sh, then clean.sh)
#
#  Outputs:
#     data/ml_charts/01_model_comparison.png
#     data/ml_charts/02_feature_importance.png
#     data/ml_charts/03_confusion_matrix.png
#     data/recommendation_scores.csv
#     data/similar_games.csv
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

# --- 2b. check the ML scripts exist -------------------------
for f in \
  scripts/ml_part1_regression.py \
  scripts/ml_part2_classification.py \
  scripts/ml_part3_recommender.py
do
  if [ ! -f "$f" ]; then
    echo "[ERROR] $f not found."
    exit 1
  fi
done

# --- 3. make sure the ML libraries are installed ------------
if ! "$PY_CMD" -c "import pandas, numpy, matplotlib, sklearn, scipy" >/dev/null 2>&1; then
  echo "ML libraries not found - installing for the first time..."
  if ! "$PY_CMD" -m pip install pandas numpy matplotlib scikit-learn scipy; then
    echo "[ERROR] Could not install ML libraries."
    echo "Try manually:  $PY_CMD -m pip install pandas numpy matplotlib scikit-learn scipy"
    exit 1
  fi
fi

# --- 4. run the three parts, one after the other ------------
echo "Using: $PY_CMD"
echo

echo "============================================================"
echo "PART 1/3 - Aoxue Li: regression (predict popularity)"
echo "============================================================"
if ! "$PY_CMD" scripts/ml_part1_regression.py; then
  echo "[ERROR] Part 1 failed - check the messages above."
  exit 1
fi
echo

echo "============================================================"
echo "PART 2/3 - Ezeme Onyenezi Innocent: classification (good-game classifier)"
echo "============================================================"
if ! "$PY_CMD" scripts/ml_part2_classification.py; then
  echo "[ERROR] Part 2 failed - check the messages above."
  exit 1
fi
echo

# --- Ezeme Onyenezi Innocent's text task (small, ~30 s) -----
# Uncomment the next lines to also run it:
# echo "============================================================"
# echo "Ezeme Onyenezi Innocent: discriminative words per category"
# echo "============================================================"
# "$PY_CMD" scripts/ml_part2_discriminative_words.py

echo "============================================================"
echo "PART 3/3 - Zhi Zhou: recommender + similar games"
echo "============================================================"
if ! "$PY_CMD" scripts/ml_part3_recommender.py; then
  echo "[ERROR] Part 3 failed - check the messages above."
  exit 1
fi
echo

echo "============================================================"
echo "All three parts finished!"
echo "  Charts:  data/ml_charts/"
echo "  Web app: data/recommendation_scores.csv + data/similar_games.csv"
echo "============================================================"