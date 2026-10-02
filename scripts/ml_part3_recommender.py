"""
ml_part3_recommender.py
=================================================================
Task 1: turn the ML analysis into something USEFUL for real players:
        a content-based recommender that suggests games based on
        group size, playtime preference and complexity preference.
Task 2 SIMILAR GAMES - "more like this" via Jaccard similarity
        on the categories + mechanics tags (same-series games excluded).

USAGE
-----

Output:
  - 3 demo recommendations in the terminal (family/veteran/solo)
  - data/recommendation_scores.csv  (2077 games x fit scores)
    -> this file powers the web app recommendation page
  - data/similar_games.csv  (2075 games x top-5 similar games)
    -> this file powers the web app "More like this" buttons

Log:
2026/09/29: project skeleton, data loading, first matching function.
2026/09/30: the two remaining matching functions (playtime, complexity).
2026/10/01: build the game pool, the recommend() function, and run three
            demo user profiles (family night / veteran duo / solo evening).
2026/10/01: log-distance playtime fit (the linear decay over-penalised long
            games), a rating-quality term in the score, and export of the per-game
            score table that powers the web app recommendation page.
2026/10/02: SIMILAR GAMES - "more like this" based on
            the categories + mechanics tags. Build the tag sets, the one-hot matrix
            and the pairwise distance matrix.
2026/10/02: for every game, pick the top-5 most similar games (excluding
            the game itself and same-series editions) and export similar_games.csv.
2026/10/02: finish.
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
REC_OUT = ROOT / "data" / "recommendation_scores.csv"

df = pd.read_csv(DATA, encoding="utf-8-sig")
print(f"Loaded {len(df)} games x {len(df.columns)} columns\n")


# ======================================================================
# 1. MATCHING FUNCTIONS
# ======================================================================

def players_fit(row, n_players):
    """1.0 = group size inside the game's range, 0.5 = one step away, 0 = far."""
    lo, hi = row["min_players"], row["max_players"]
    if lo <= n_players <= hi:
        return 1.0
    if n_players == lo - 1 or n_players == hi + 1:
        return 0.5
    return 0.0

def playtime_fit(g_minutes, pref_minutes):
    """Log-distance decay: 1.0 at exact match, ->0 far away (robust to long tails)."""
    if pd.isna(g_minutes) or g_minutes <= 0:
        return 0.5
    diff = abs(np.log(g_minutes + 1) - np.log(pref_minutes + 1))
    return float(np.exp(-diff / 2.0))

def complexity_fit(g_complexity, pref):
    """1.0 at exact complexity, decays with distance (pref in 1-5)."""
    if pd.isna(g_complexity):
        return 0.5
    return float(np.exp(-abs(g_complexity - pref) / 2.0))


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
rec["top_category"] = rec["categories"].fillna("").str.split(";").str[0].str.strip()
rec["users_rated"] = df["users_rated"].fillna(0)

def recommend(n_players, pref_minutes, pref_complexity, n=5, min_ratings=100):
    """Filter by data quality, score every game, return top-n with reasons."""
    pool = rec[rec["users_rated"] >= min_ratings]     # only games with real data
    pool = pool[pool["avg_rating"].notna()]
    pool = pool.copy()
    pool["players_fit"] = pool.apply(players_fit, axis=1, n_players=n_players)
    pool["playtime_fit"] = pool["playing_time_min"].apply(
        playtime_fit, pref_minutes=pref_minutes)
    pool["complexity_fit"] = pool["complexity_weight"].apply(
        complexity_fit, pref=pref_complexity)
    # overall score: fit dimensions + a quality term (avg_rating normalised)
    # so a perfect-fit but poorly-rated game never beats a great game.
    pool["score"] = (0.35 * pool["players_fit"] + 0.2 * pool["playtime_fit"]
                     + 0.2 * pool["complexity_fit"]
                     + 0.25 * pool["avg_rating"] / 10.0)
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


# ======================================================================
# 4. EXPORT THE SCORE TABLE FOR THE WEB APP
# ======================================================================
# one representative row per game (players=4, 45 min, medium complexity)
rec_out = rec.copy()
rec_out["players_fit"] = rec_out.apply(players_fit, axis=1, n_players=4)
rec_out["playtime_fit"] = rec_out["playing_time_min"].apply(
    playtime_fit, pref_minutes=45)
rec_out["complexity_fit"] = rec_out["complexity_weight"].apply(
    complexity_fit, pref=3)
rec_out["score"] = (0.35 * rec_out["players_fit"] + 0.2 * rec_out["playtime_fit"]
                    + 0.2 * rec_out["complexity_fit"]
                    + 0.25 * rec_out["avg_rating"] / 10.0)
rec_out.to_csv(REC_OUT, index=False, encoding="utf-8-sig")
print(f"\nSaved per-game score table -> {REC_OUT} ({len(rec_out)} rows)")

# print("\nNEXT STEP: in the web app, the recommendation page will")
# print("re-compute these three fit scores live (players / time /")
# print("complexity chosen by the user) and sort the same way.")


# ======================================================================
# 5. SIMILAR GAMES ("more like this")
# ======================================================================
# Different question from Part 1-4:
#   recommender   : "what fits my needs?"   (game vs user requirement)
#   similar games : "what is like this one?" (game vs game, by shared tags)
# Similarity = Jaccard of the label sets (categories + mechanics).

from scipy.spatial.distance import pdist, squareform

print("\n" + "=" * 60)
print("PART 5  Similar games: 'more like this' (Jaccard on tags)")
print("=" * 60)

# build one label set per game: categories + mechanics
sim = rec[["game_id", "name", "top_category"]].copy()
sim["labels"] = (rec["categories"].fillna("")
                 + ";" + rec["mechanics"].fillna(""))
sim["labels"] = sim["labels"].str.split(";").apply(
    lambda lst: sorted({s.strip() for s in lst if s.strip()}))
# "family" = the game series (e.g. "Catan: Big Box" -> "catan").
# We never recommend the same series (editions/reprints are too easy).
sim["family"] = sim["name"].str.split(":").str[0].str.strip().str.lower()

# games with no tags at all cannot be compared - drop them
mask = sim["labels"].apply(len) > 0
sim = sim[mask].reset_index(drop=True)
print(f"Games with tags for comparison: {len(sim)} (dropped {int((~mask).sum())})")

# one-hot matrix: rows = games, cols = unique tags
all_tags = sorted({t for lst in sim["labels"] for t in lst})
mat = np.zeros((len(sim), len(all_tags)), dtype=bool)
for i, lst in enumerate(sim["labels"]):
    idx = [all_tags.index(t) for t in lst]
    mat[i, idx] = True

# pairwise Jaccard distance (1 - similarity). Similarity = 1 - distance.
dist = squareform(pdist(mat, metric="jaccard"))
np.fill_diagonal(dist, 1.0)               # ignore the game itself
print(f"Pairwise matrix: {len(sim)} x {len(sim)}")

# # quick debug: nearest rows to the first game
# i = 0
# nearest = np.argsort(dist[i])[:6]
# print(f"\nDebug - nearest rows to '{sim.loc[i, 'name']}':")
# for j in nearest:
#     print(f"  {sim.loc[j, 'name']:<45s} distance {dist[i, j]:.3f}")

SIM_N = 5
sim_rows = []
families = sim["family"].values
for i in range(len(sim)):
    # exclude the game itself AND all games from the same series.
    # "same series" = family keys that are equal or contain each other,
    # e.g. "catan" vs "baden-württemberg catan" or "catan: family edition".
    order_all = np.argsort(dist[i])
    fam_i = families[i]
    cand = [j for j in order_all
            if not (families[j] == fam_i
                    or families[j] in fam_i or fam_i in families[j])][:SIM_N]
    scores = 1.0 - dist[i, cand]
    row = {"game_id": sim.loc[i, "game_id"], "name": sim.loc[i, "name"],
           "top_category": sim.loc[i, "top_category"]}
    for k, (j, sc) in enumerate(zip(cand, scores), start=1):
        row[f"sim{k}_name"] = sim.loc[j, "name"]
        row[f"sim{k}_score"] = round(float(sc), 3)
    sim_rows.append(row)

sim_df = pd.DataFrame(sim_rows)
SIM_OUT = ROOT / "data" / "similar_games.csv"
sim_df.to_csv(SIM_OUT, index=False, encoding="utf-8-sig")
print(f"Saved -> {SIM_OUT} ({len(sim_df)} games x top-{SIM_N} similar)")

# demo: what is like Catan? (pick the classic game, not an edition)
catan = sim_df[sim_df["name"].str.lower() == "catan"]
if catan.empty:                                  # fall back to any Catan game
    catan = sim_df[sim_df["name"].str.contains("Catan", case=False, na=False)]
catan = catan.iloc[0]
print(f"\nDemo - games like '{catan['name']}' (category: {catan['top_category']}):")
for k in range(1, SIM_N + 1):
    print(f"  {catan[f'sim{k}_name']:<45s} similarity {catan[f'sim{k}_score']:.3f}")
print("\nDONE - your part is complete (recommender + similar games).")