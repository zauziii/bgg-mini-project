"""
ml_part3_recommender.py
=================================================================
Part 3 of the ML pipeline
turn the ML analysis into a content-based recommender that suggests
games based on group size, playtime preference and complexity.

2026/09/29: project skeleton, data loading, first matching function.
"""

import pathlib
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ----------------------------------------------------------------------
# paths
# ----------------------------------------------------------------------
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "data" / "cleaned_games.csv"

df = pd.read_csv(DATA, encoding="utf-8-sig")
print(f"Loaded {len(df)} games x {len(df.columns)} columns\n")

# ======================================================================
# 1. MATCHING FUNCTIONS
# ======================================================================

def players_fit(row, n_players):
    """1.0 = group size inside the game's range, 0 = outside it."""
    lo, hi = row["min_players"], row["max_players"]
    if lo <= n_players <= hi:
        return 1.0
    return 0.0


# quick sanity check on the first game in the dataset
row0 = df.iloc[0]
print(f"Sanity check - players_fit for '{row0['name']}' "
      f"({row0['min_players']}-{row0['max_players']} players):")
for n in range(1, 8):
    print(f"  {n} players -> {players_fit(row0, n)}")