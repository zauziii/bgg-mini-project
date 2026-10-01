"""
ml_part3_recommender.py
=================================================================
Part 3 of the ML pipeline
turn the ML analysis into a content-based recommender that suggests
games based on group size, playtime preference and complexity.

2026/09/29: project skeleton, data loading, first matching function.
2026/09/30: the two remaining matching functions (playtime, complexity).
2026/10/01: build the game pool, the recommend() function, and run three
            demo user profiles (family night / veteran duo / solo evening).
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
    """1.0 = group size inside the range, 0.5 = one player away, 0 = far."""
    lo, hi = row["min_players"], row["max_players"]
    if lo <= n_players <= hi:
        return 1.0
    if n_players == lo - 1 or n_players == hi + 1:
        return 0.5
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


# # quick sanity check on the first game in the dataset
# row0 = df.iloc[0]
# print(f"Sanity check - players_fit for '{row0['name']}' "
#       f"({row0['min_players']}-{row0['max_players']} players):")
# for n in range(1, 8):
#     print(f"  {n} players -> {players_fit(row0, n)}")

# print("\nplaytime_fit (preference = 45 min):")
# for m in [15, 30, 45, 90, 180]:
#     print(f"  {m:>4d} min -> {playtime_fit(m, 45):.2f}")

# print("\ncomplexity_fit (preference = 3/5):")
# for c in [1, 2, 3, 4, 5]:
#     print(f"  {c}/5 -> {complexity_fit(c, 3):.2f}")
# print(f"  missing value -> {complexity_fit(np.nan, 3):.2f}")


# ======================================================================
# 2. BUILD THE GAME POOL
# ======================================================================
rec = df[["game_id", "name", "min_players", "max_players",
          "playing_time_min", "complexity_weight", "avg_rating",
          "categories", "mechanics", "board_game_rank"]].copy()
rec["top_category"] = rec["categories"].fillna("").str.split(";").str[0]
rec["users_rated"] = df["users_rated"].fillna(0)

def recommend(n_players, pref_minutes, pref_complexity, n=5, min_ratings=100):
    """Filter by data quality, score every game, return top-n."""
    pool = rec[rec["users_rated"] >= min_ratings]
    pool = pool[pool["avg_rating"].notna()]
    pool["players_fit"] = pool.apply(players_fit, axis=1, n_players=n_players)
    pool["playtime_fit"] = pool["playing_time_min"].apply(
        playtime_fit, pref_minutes=pref_minutes)
    pool["complexity_fit"] = pool["complexity_weight"].apply(
        complexity_fit, pref=pref_complexity)
    pool["score"] = (0.5 * pool["players_fit"]
                     + 0.25 * pool["playtime_fit"]
                     + 0.25 * pool["complexity_fit"])
    top = pool.sort_values("score", ascending=False).head(n)
    return top[["name", "avg_rating", "complexity_weight", "playing_time_min",
                "min_players", "max_players", "top_category", "score"]]


# ======================================================================
# 3. DEMO: three realistic user profiles
# ======================================================================
print("Demo 1 - family game night: 4 players, 30 min, light (2/5):")
print(recommend(n_players=4, pref_minutes=30, pref_complexity=2).round(2).to_string(index=False))

print("\nDemo 2 - veteran duo: 2 players, 180 min, heavy (4/5):")
print(recommend(n_players=2, pref_minutes=180, pref_complexity=4).round(2).to_string(index=False))

print("\nDemo 3 - solo evening: 1 player, 45 min, medium (3/5):")
print(recommend(n_players=1, pref_minutes=45, pref_complexity=3).round(2).to_string(index=False))