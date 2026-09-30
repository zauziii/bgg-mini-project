"""
ml_part3_recommender.py
=================================================================
Part 3 of the ML pipeline
turn the ML analysis into a content-based recommender that suggests
games based on group size, playtime preference and complexity.

2026/09/29: project skeleton, data loading, first matching function.
2026/09/30: the two remaining matching functions (playtime, complexity).
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

def playtime_fit(g_minutes, pref_minutes):
    """1.0 at exact match, decays linearly with the gap in minutes."""
    if pd.isna(g_minutes) or g_minutes <= 0:
        return 0.5
    diff = abs(g_minutes - pref_minutes)
    return max(0.0, 1.0 - diff / pref_minutes)

def complexity_fit(g_complexity, pref):
    """1.0 at exact complexity, decays with distance (pref in 1-5)."""
    if pd.isna(g_complexity):
        return 0.0
    return float(np.exp(-abs(g_complexity - pref)))


# quick sanity check on the first game in the dataset
row0 = df.iloc[0]
print(f"Sanity check - players_fit for '{row0['name']}' "
      f"({row0['min_players']}-{row0['max_players']} players):")
for n in range(1, 8):
    print(f"  {n} players -> {players_fit(row0, n)}")

print("\nplaytime_fit (preference = 45 min):")
for m in [15, 30, 45, 90, 180]:
    print(f"  {m:>4d} min -> {playtime_fit(m, 45):.2f}")

print("\ncomplexity_fit (preference = 3/5):")
for c in [1, 2, 3, 4, 5]:
    print(f"  {c}/5 -> {complexity_fit(c, 3):.2f}")
print(f"  missing value -> {complexity_fit(np.nan, 3):.2f}")
