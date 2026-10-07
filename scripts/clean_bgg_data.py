"""
clean_bgg_data.py
=================
Clean the raw BoardGameGeek data (games.csv) into a tidy dataset

It fixes the typical "dirty data" problems of the BGG export:
  1. duplicate rows
  2. empty strings vs. real missing values
  3. numbers stored as text
  4. BGG's special "fake zero" values (year 0, bayes 0, weight 0)
  5. messy free-text (names, description)
  6. add useful new features for later analysis

Run it from the folder that contains games.csv
    Windows (easiest): double-click clean.bat in the repo root
    Windows (Anaconda Prompt):
        cd data
        python .../scripts/clean_bgg_data.py

    Mac / Linux:
        cd data
        python3 ../scripts/clean_bgg_data.py

output: cleaned_games.csv (+ a summary printed in the terminal)
"""

import pathlib

import pandas as pd

# ======================================================================
# 0. LOCATE THE DATA FOLDER (works no matter where the script lives)
# ======================================================================
# The script may sit in the project root or in scripts/; the data
# folder is always <project root>/data. We walk up from the script
# location until we find a folder that contains data/games.csv.
HERE = pathlib.Path(__file__).resolve().parent
DATA_DIR = None
for candidate in (HERE, HERE.parent, HERE.parent.parent):
    if (candidate / "data" / "games.csv").is_file():
        DATA_DIR = candidate / "data"
        break
if DATA_DIR is None:
    raise FileNotFoundError(
        "Could not find data/games.csv. Run run.bat first to download "
        "the data, and keep clean_bgg_data.py inside the project folder."
    )

IN_CSV = DATA_DIR / "games.csv"
OUT_CSV = DATA_DIR / "cleaned_games.csv"

# ======================================================================
# 1. READ THE DATA
# ======================================================================
# dtype={"game_id": str} keeps game ids as text (ids can have leading zeros)
# utf-8-sig: game.csv is saved with a BOM (Excel-friendly) - read it back correctly
df = pd.read_csv(IN_CSV, dtype={"game_id": str}, encoding="utf-8-sig")

print("Raw rows:", len(df))

# ======================================================================
# 2. REMOVE DUPLICATES
# ======================================================================
before = len(df)
df = df.drop_duplicates(subset="game_id")
print("Duplicates removed", before - len(df))

# ======================================================================
# 3. UNIFY MISSING VALUE: "" -> NaN
# ======================================================================
# BGG writes empty celss as empty strings. pandas prefers NaN for "missing"
# so later numeric checks and plots treat them correctly
df = df.replace("", float("nan"))

# ======================================================================
# 4. CONVERT TEXT COLUMNS TO NUMBERS
# ======================================================================
# Many columns arrive as text ("7.0903"). Convert them to real numbers;
# anything that can't be converted (e.g. "Not Ranked") becomes NaN.
num_cols = [
    "year_published", "min_players", "max_players",
    "playing_time_min", "min_playtime", "max_playtime", "min_age",
    "users_rated", "avg_rating", "bayes_rating", "complexity_weight",
    "board_game_rank",
]
for col in num_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# ======================================================================
# 5. FIX BGG'S SPECIAL "FAKE ZERO" VALUES
# ======================================================================
# BGG uses 0 as a placeholder meaning "no data" in many fields
# We convert them to NaN so they are never mistaken for real values.
zero_to_nan = [
    "year_published", "min_players", "max_players",
    "playing_time_min", "min_playtime", "max_playtime",
    "users_rated", "avg_rating", "bayes_rating", "complexity_weight",
]
for col in zero_to_nan:
    df[col] = df[col].replace(0, float("nan"))

# negative years = ancient games (e.g. Go is stored as year -2200 BC)
# -> treat as unknown year
df.loc[df["year_published"] < 0, "year_published"] = float("nan")

# NOTE: min_age KEEPS its 0 values on purpose - BGG uses 0
# to mean "no age restricton given" (valid, not missing)

# ======================================================================
# 6. CLEAN TEXT FIELDS
# ======================================================================
df["name"] = df["name"].str.strip()                # remove extra spaces

# description: already cleaned during download; add its length as a feature
df["description_length"] = df["description"].fillna("").str.len()

# strip whitespace inside multi-value fields (categories, mechanics, designers)
for col in ["categories", "mechanics", "designers"]:
    df[col] = df[col].fillna("").str.replace("; ", ";", regex=False)

# ======================================================================
# CREATE NEW FEATURES (useful for EDA / ML later)
# ======================================================================
# 7.1 decade: which 10-year period was the game released in ? (0 = unknown)
df["decade"] = (df["year_published"].fillna(0) // 10 * 10).astype(int)

# 7.2 complexity group: ligt(<2) / medium (2-3) / heavy (>3)
def complexity_label(weight):
    if pd.isna(weight):
        return "unknown"
    if weight < 2:
        return "light"
    if weight < 3:
        return "medium"
    return "heavy"

df["complexity_group"] = df["complexity_weight"].apply(complexity_label)

# 7.3 playtime group: short (<=30) / medium (31-90) / long (>90)
def playtime_label(minutes):
    if pd.isna(minutes):
        return "unknown"
    if minutes <= 30:
        return "short"
    if minutes <= 90:
        return "medium"
    return "long"

df["playtime_group"] = df["playing_time_min"].apply(playtime_label)

# 7.4 can it be played solo? 1 = yes, 0 = no (missing -> 0)
df["is_solo"] = (df["min_players"] == 1).fillna(False).astype(int)

# 7.5 rank tier: how famous is the game on BGG?
rank = df["board_game_rank"]
df["rank_tier"] = "unranked"
df.loc[rank.notna() & (rank <= 1000), "rank_tier"] = "top1000"
df.loc[rank.notna() & (rank > 1000) & (rank <= 5000), "rank_tier"] = "top5000"
df.loc[rank.notna() & (rank > 5000), "rank_tier"] = "ranked"

# 7.6 how many categories / mechanics does each game have?
df["n_categories"] = df["categories"].fillna("").str.split(";").apply(len)
df["n_mechanics"] = df["mechanics"].fillna("").str.split(";").apply(len)

# ======================================================================
# 8. PRINT A SHORT CLEANING REPORT
# ======================================================================
print("\n--- cleaning report ---")
print("Final rows:", len(df))
print("\nMissing values per column:")
print(df[num_cols].isna().sum().to_string())
print("\nGames by decade (top 10):")
print(df["decade"].value_counts().sort_index(ascending=False).head(10).to_string())
print("\nComplexity groups:")
print(df["complexity_group"].value_counts().to_string())
print("\nPlaytime groups:")
print(df["playtime_group"].value_counts().to_string())
print("\nRank tiers:")
print(df["rank_tier"].value_counts().to_string())
print("\nRating stats (avg_rating):")
print(df["avg_rating"].describe().to_string())

# ======================================================================
# 9. SAVE
# ======================================================================
# utf-8-sig adds a BOM so Excel opens the file without mojibake
df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
print("\nSaved cleaned_games.csv with", len(df), "rows x", len(df.columns), "columns")
