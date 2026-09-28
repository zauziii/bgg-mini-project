"""
eda.py - FULL Exploratory Data Analysis for the BGG board game dataset
=======================================================================
Week 2 of the mini-project: EDA & visualizations (complete version).

STYLE: publication-quality ("scientific paper") look.
  - serif fonts (Times New Roman where available)
  - no top/right spines, light dashed grid lines
  - matplotlib "tab10" scientific palette
  - 300 dpi output, tight bounding boxes

Reads  data/cleaned_games.csv
Prints a text summary for every section
Saves  14 PNG charts into data/charts/

Chart map
---------
 01 missing_values.png          how much data is missing per column
 02 rating_histogram.png        distribution of avg_rating
 03 rating_vs_complexity.png    scatter: rating x complexity (r = 0.50)
 04 rating_by_complexity_box.png  box: rating within each complexity group
 05 games_per_decade.png        how many games per decade
 06 rating_by_decade_box.png    box: rating within each decade
 07 rating_by_playtime_box.png  box: rating within each playtime group
 08 rating_by_solo_box.png      box: solo vs non-solo rating
 09 complexity_hist.png         distribution of complexity_weight
 10 playtime_hist.png           distribution of playing_time_min
 11 rating_vs_popularity.png    scatter: rating x users_rated (log x)
 12 top_categories.png          top 10 categories (horizontal bars)
 13 top_mechanics.png           top 10 mechanics (horizontal bars)
 14 players_bucket.png          how many games for each max-player range

Usage
-----
  Windows (easiest): double-click eda.bat in the repo root
  Windows (Anaconda Prompt):
      python scripts/eda.py
  Mac / Linux:
      python3 scripts/eda.py

Requires pandas + matplotlib (both come with Anaconda).
"""

import pathlib
from collections import Counter

import matplotlib.pyplot as plt
import pandas as pd

# ----------------------------------------------------------------------
# 0. WHERE ARE WE?
# ----------------------------------------------------------------------
HERE = pathlib.Path(__file__).resolve().parent   # .../scripts
ROOT = HERE.parent                                # repo root
DATA = ROOT / "data" / "cleaned_games.csv"
OUT = ROOT / "data" / "charts"
OUT.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# 0.5 PUBLICATION STYLE (applies to every chart below)
# ----------------------------------------------------------------------
# Scientific palette (matplotlib tab10, used by academic papers)
BLUE   = "#1f77b4"   # main series
ORANGE = "#ff7f0e"   # highlights (missing values, players)
GREEN  = "#2ca02c"   # second series (mechanics, popularity)
RED    = "#d62728"   # medians in box plots
PURPLE = "#9467bd"   # spare
GREY   = "#7f7f7f"   # unknown / secondary
DARK   = "#333333"   # axis text
GRID   = "#999999"   # grid lines

plt.rcParams.update({
    # fonts: serif = classic scientific paper look
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
    "font.size": 10,
    # axes
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 12,
    "axes.labelpad": 8,
    "axes.edgecolor": DARK,
    "axes.linewidth": 0.8,
    "axes.spines.top": False,     # scientific papers drop top & right frames
    "axes.spines.right": False,
    # ticks
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.color": "#555555",
    "ytick.color": "#555555",
    # misc
    "legend.fontsize": 10,
    "figure.dpi": 100,
    "savefig.dpi": 300,           # print quality for the report
    "savefig.bbox": "tight",
})


def style_ax(ax, grid_axis="y"):
    """Apply the common publication look to a freshly created axis."""
    # light dashed grid behind the data
    ax.grid(axis=grid_axis, linestyle="--", linewidth=0.5,
            color=GRID, alpha=0.4, zorder=0)
    # keep the data in front of the grid
    for coll in ax.collections:
        coll.set_zorder(3)
    for line in ax.lines:
        line.set_zorder(3)
    for patch in ax.patches:
        patch.set_zorder(2)


def box_style():
    """Return the shared props dict for publication-quality box plots."""
    return dict(
        patch_artist=True,
        medianprops={"color": RED, "linewidth": 1.6},
        boxprops={"facecolor": BLUE, "alpha": 0.45,
                  "edgecolor": "#175FA3", "linewidth": 1.0},
        whiskerprops={"color": "#555555", "linewidth": 1.0},
        capprops={"color": "#555555", "linewidth": 1.0},
        flierprops={"marker": "o", "markerfacecolor": BLUE,
                    "markersize": 3.5, "alpha": 0.45,
                    "markeredgecolor": "none"},
    )


df = pd.read_csv(DATA, encoding="utf-8-sig")
print(f"Loaded {len(df)} games x {len(df.columns)} columns\n")

num_cols = [
    "year_published", "min_players", "max_players", "playing_time_min",
    "min_age", "users_rated", "avg_rating", "bayes_rating",
    "complexity_weight", "board_game_rank",
]

# ======================================================================
# 1. SUMMARY STATISTICS
# ======================================================================
print("=" * 50)
print("1. Summary statistics (numeric columns)")
print("=" * 50)
print(df[num_cols].describe().round(2).to_string())

# ======================================================================
# 2. MISSING VALUES
# ======================================================================
print("\n" + "=" * 50)
print("2. Missing values per column")
print("=" * 50)
miss = df[num_cols].isna().sum().sort_values(ascending=False)
miss_pct = (miss / len(df) * 100).round(1)
print((miss.astype(str) + "  (" + miss_pct.astype(str) + "%)").to_string())

fig, ax = plt.subplots(figsize=(7, 4))
miss.plot(kind="barh", color=ORANGE, edgecolor="white", ax=ax)
style_ax(ax)
ax.set_title("Missing values per column")
ax.set_xlabel("Number of missing rows")
ax.bar_label(ax.containers[0], fontsize=9, color="#555555", padding=3)
fig.savefig(OUT / "01_missing_values.png")
plt.close(fig)

# ======================================================================
# 3. RATING DISTRIBUTION (histogram)
# ======================================================================
print("\n" + "=" * 50)
print("3. Rating distribution (avg_rating)")
print("=" * 50)
bins = [1, 3, 4, 5, 6, 7, 8, 9, 10]
labels = ["1-3", "3-4", "4-5", "5-6", "6-7", "7-8", "8-9", "9-10"]
counts = pd.cut(df["avg_rating"].dropna(), bins=bins, labels=labels,
                right=False).value_counts().sort_index()
print(counts.to_string())

rat = df["avg_rating"].dropna()
# median line must sit on the categorical x-axis -> convert the value to a bin index
med_val = rat.median()
med_bin = None
for i in range(len(bins) - 1):
    if bins[i] <= med_val < bins[i + 1]:
        med_bin = i
        break
fig, ax = plt.subplots(figsize=(7, 4))
counts.plot(kind="bar", color=BLUE, edgecolor="white", ax=ax)
for c in ax.containers:
    c.set_label("_nolegend_")   # hide pandas' automatic "count" legend entry
style_ax(ax)
ax.set_title("Distribution of average ratings")
ax.set_xlabel("Average rating")
ax.set_ylabel("Number of games")
if med_bin is not None:
    ax.axvline(med_bin + 0.5, color=RED, linestyle="--", linewidth=1.2,
               label=f"median = {med_val:.2f}")
    ax.legend(frameon=False)
ax.bar_label(ax.containers[0], fontsize=9, color="#555555", padding=2)
fig.savefig(OUT / "02_rating_histogram.png")
plt.close(fig)

# ======================================================================
# 4. RATING vs COMPLEXITY (scatter, the strongest relationship)
# ======================================================================
print("\n" + "=" * 50)
print("4. Correlation with avg_rating")
print("=" * 50)
corr = df[num_cols + ["n_categories", "n_mechanics",
                      "description_length"]].corr()
print(corr["avg_rating"].round(3).sort_values(ascending=False).to_string())
print("Note: board_game_rank is negative (-0.84) because rank #1 = best.")

sub = df.dropna(subset=["avg_rating", "complexity_weight"])
fig, ax = plt.subplots(figsize=(7, 5))
ax.scatter(sub["complexity_weight"], sub["avg_rating"],
           s=14, alpha=0.4, color=BLUE, edgecolors="none", zorder=3)
style_ax(ax)
ax.set_title("Average rating vs complexity (r = 0.50)")
ax.set_xlabel("Complexity weight (1 = light, 5 = heavy)")
ax.set_ylabel("Average rating")
ax.text(0.03, 0.97, "r = 0.50", transform=ax.transAxes,
        fontsize=12, fontstyle="italic", va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                  edgecolor="#CCCCCC"))
fig.savefig(OUT / "03_rating_vs_complexity.png")
plt.close(fig)

# ======================================================================
# 5. BOXPLOT: rating by complexity group
# ======================================================================
print("\n" + "=" * 50)
print("5. Rating five-number summary by complexity group")
print("=" * 50)
groups = ["light", "medium", "heavy", "unknown"]
box_data = []
for g in groups:
    s = df.loc[df["complexity_group"] == g, "avg_rating"].dropna()
    box_data.append(s)
    print(f"{g:8s} n={len(s):4d}  min={s.min():.2f} "
          f"q1={s.quantile(.25):.2f} med={s.median():.2f} "
          f"q3={s.quantile(.75):.2f} max={s.max():.2f}")

fig, ax = plt.subplots(figsize=(7, 5))
bp = ax.boxplot(box_data, tick_labels=groups, **box_style())
style_ax(ax)
ax.set_title("Rating distribution by complexity group")
ax.set_ylabel("Average rating")
fig.savefig(OUT / "04_rating_by_complexity_box.png")
plt.close(fig)

# ======================================================================
# 6. GAMES PER DECADE
# ======================================================================
print("\n" + "=" * 50)
print("6. Games per decade (>= 1900)")
print("=" * 50)
dec = df.loc[df["decade"] >= 1900, "decade"].value_counts().sort_index()
print(dec.to_string())

fig, ax = plt.subplots(figsize=(8, 4))
dec.plot(kind="bar", color=BLUE, edgecolor="white", ax=ax)
style_ax(ax)
ax.set_title("Number of games by release decade")
ax.set_xlabel("Decade")
ax.set_ylabel("Number of games")
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
ax.bar_label(ax.containers[0], fontsize=8, color="#555555", padding=2)
fig.savefig(OUT / "05_games_per_decade.png")
plt.close(fig)

# ======================================================================
# 7. BOXPLOT: rating by decade
# ======================================================================
print("\n" + "=" * 50)
print("7. Rating five-number summary by decade")
print("=" * 50)
decades = [1990, 2000, 2010, 2020]
box_dec = []
for d in decades:
    s = df.loc[df["decade"] == d, "avg_rating"].dropna()
    box_dec.append(s)
    print(f"{d}s n={len(s):4d}  min={s.min():.2f} "
          f"q1={s.quantile(.25):.2f} med={s.median():.2f} "
          f"q3={s.quantile(.75):.2f} max={s.max():.2f}")

fig, ax = plt.subplots(figsize=(7, 5))
ax.boxplot(box_dec, tick_labels=[f"{d}s" for d in decades], **box_style())
style_ax(ax)
ax.set_title("Rating distribution by release decade")
ax.set_ylabel("Average rating")
fig.savefig(OUT / "06_rating_by_decade_box.png")
plt.close(fig)

# ======================================================================
# 8. BOXPLOT: rating by playtime group
# ======================================================================
print("\n" + "=" * 50)
print("8. Rating five-number summary by playtime group")
print("=" * 50)
pt_groups = ["short", "medium", "long", "unknown"]
box_pt = []
for g in pt_groups:
    s = df.loc[df["playtime_group"] == g, "avg_rating"].dropna()
    box_pt.append(s)
    print(f"{g:8s} n={len(s):4d}  med={s.median():.2f}")

fig, ax = plt.subplots(figsize=(7, 5))
ax.boxplot(box_pt, tick_labels=pt_groups, **box_style())
style_ax(ax)
ax.set_title("Rating distribution by playtime group")
ax.set_ylabel("Average rating")
fig.savefig(OUT / "07_rating_by_playtime_box.png")
plt.close(fig)

# ======================================================================
# 9. BOXPLOT: solo vs non-solo
# ======================================================================
print("\n" + "=" * 50)
print("9. Solo vs non-solo rating")
print("=" * 50)
solo_yes = df.loc[df["is_solo"] == 1, "avg_rating"].dropna()
solo_no = df.loc[df["is_solo"] == 0, "avg_rating"].dropna()
print(f"solo     n={len(solo_yes):4d}  mean={solo_yes.mean():.2f}  "
      f"med={solo_yes.median():.2f}")
print(f"non-solo n={len(solo_no):4d}  mean={solo_no.mean():.2f}  "
      f"med={solo_no.median():.2f}")

fig, ax = plt.subplots(figsize=(6, 5))
ax.boxplot([solo_no, solo_yes], tick_labels=["non-solo", "solo"],
           **box_style())
style_ax(ax)
ax.set_title("Rating: solo vs non-solo games")
ax.set_ylabel("Average rating")
fig.savefig(OUT / "08_rating_by_solo_box.png")
plt.close(fig)

# ======================================================================
# 10. COMPLEXITY DISTRIBUTION (histogram)
# ======================================================================
print("\n" + "=" * 50)
print("10. Complexity distribution")
print("=" * 50)
cw = df["complexity_weight"].dropna()
print(f"n={len(cw)}  mean={cw.mean():.2f}  median={cw.median():.2f}")

fig, ax = plt.subplots(figsize=(7, 4))
ax.hist(cw, bins=[1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5],
        color=GREEN, edgecolor="white", linewidth=0.6, zorder=3)
style_ax(ax)
ax.set_title("Distribution of complexity weight")
ax.set_xlabel("Complexity (1 = light, 5 = heavy)")
ax.set_ylabel("Number of games")
ax.axvline(cw.median(), color=RED, linestyle="--", linewidth=1.2,
           label=f"median = {cw.median():.2f}")
ax.legend(frameon=False)
fig.savefig(OUT / "09_complexity_hist.png")
plt.close(fig)

# ======================================================================
# 11. PLAYTIME DISTRIBUTION (histogram, log y)
# ======================================================================
print("\n" + "=" * 50)
print("11. Playtime distribution")
print("=" * 50)
pt = df["playing_time_min"].dropna()
print(f"n={len(pt)}  mean={pt.mean():.1f}  median={pt.median():.0f}")

fig, ax = plt.subplots(figsize=(8, 4))
ax.hist(pt, bins=[0, 15, 30, 45, 60, 90, 120, 180, 240, 480, 1201],
        color=BLUE, edgecolor="white", linewidth=0.6, log=True, zorder=3)
style_ax(ax)
ax.set_title("Distribution of playing time (log scale)")
ax.set_xlabel("Minutes")
ax.set_ylabel("Number of games (log)")
fig.savefig(OUT / "10_playtime_hist.png")
plt.close(fig)

# ======================================================================
# 12. RATING vs POPULARITY (scatter, log x)
# ======================================================================
print("\n" + "=" * 50)
print("12. Rating vs popularity (users_rated)")
print("=" * 50)
bins = [0, 10, 50, 100, 500, 1000, 5000, 10000, 200000]
labs = ["<10", "10-50", "50-100", "100-500", "500-1k", "1k-5k",
        "5k-10k", "10k+"]
df["ur_b"] = pd.cut(df["users_rated"].fillna(0), bins=bins,
                    labels=labs, right=False)
g = df.groupby("ur_b", observed=True)["avg_rating"].agg(["mean", "count"]).round(2)
print(g.to_string())

sub2 = df.dropna(subset=["avg_rating", "users_rated"])
fig, ax = plt.subplots(figsize=(7, 5))
ax.scatter(sub2["users_rated"], sub2["avg_rating"],
           s=14, alpha=0.4, color=GREEN, edgecolors="none", zorder=3)
ax.set_xscale("log")
style_ax(ax)
ax.set_title("Rating vs popularity (users_rated, log x)")
ax.set_xlabel("Number of ratings (log)")
ax.set_ylabel("Average rating")
fig.savefig(OUT / "11_rating_vs_popularity.png")
plt.close(fig)

# ======================================================================
# 13. TOP CATEGORIES
# ======================================================================
print("\n" + "=" * 50)
print("13. Top 10 categories")
print("=" * 50)
cat_counts = Counter()
for v in df["categories"].dropna():
    for x in str(v).split(";"):
        x = x.strip()
        if x:
            cat_counts[x] += 1
top_cats = cat_counts.most_common(10)
print("\n".join(f"{n:5d}  {c}" for c, n in top_cats))

fig, ax = plt.subplots(figsize=(7, 5))
names = [c for c, _ in top_cats][::-1]
vals = [n for _, n in top_cats][::-1]
ax.barh(names, vals, color=BLUE, edgecolor="white", zorder=3)
style_ax(ax)
ax.set_title("Top 10 categories")
ax.set_xlabel("Number of games")
ax.bar_label(ax.containers[0], fontsize=9, color="#555555", padding=3)
fig.savefig(OUT / "12_top_categories.png")
plt.close(fig)

# ======================================================================
# 14. TOP MECHANICS
# ======================================================================
print("\n" + "=" * 50)
print("14. Top 10 mechanics")
print("=" * 50)
mech_counts = Counter()
for v in df["mechanics"].dropna():
    for x in str(v).split(";"):
        x = x.strip()
        if x:
            mech_counts[x] += 1
top_mechs = mech_counts.most_common(10)
print("\n".join(f"{n:5d}  {c}" for c, n in top_mechs))

fig, ax = plt.subplots(figsize=(7, 5))
names = [c for c, _ in top_mechs][::-1]
vals = [n for _, n in top_mechs][::-1]
ax.barh(names, vals, color=GREEN, edgecolor="white", zorder=3)
style_ax(ax)
ax.set_title("Top 10 mechanics")
ax.set_xlabel("Number of games")
ax.bar_label(ax.containers[0], fontsize=9, color="#555555", padding=3)
fig.savefig(OUT / "13_top_mechanics.png")
plt.close(fig)

# ======================================================================
# 15. PLAYER RANGE BUCKETS
# ======================================================================
print("\n" + "=" * 50)
print("15. Max players buckets")
print("=" * 50)
pbins = [1, 2, 3, 4, 6, 8, 10, 20, 101]
plabs = ["1", "2", "3-4", "5-6", "7-8", "9-10", "11-20", "20+"]
p_bucket = pd.cut(df["max_players"].fillna(0), bins=pbins,
                  labels=plabs, right=False)
pc = p_bucket.value_counts().sort_index()
print(pc.to_string())

fig, ax = plt.subplots(figsize=(7, 4))
pc.plot(kind="bar", color=ORANGE, edgecolor="white", ax=ax)
style_ax(ax)
ax.set_title("Number of games by max players")
ax.set_xlabel("Max players")
ax.set_ylabel("Number of games")
ax.bar_label(ax.containers[0], fontsize=9, color="#555555", padding=2)
fig.savefig(OUT / "14_players_bucket.png")
plt.close(fig)

# ======================================================================
# 16. KEY TABLES (T1-T6): printed evidence for the report
# ======================================================================
print("\n" + "=" * 50)
print("T1. Descriptive statistics")
print("=" * 50)
print(df[num_cols].describe().round(2).to_string())

print("\n" + "=" * 50)
print("T2. Missing values")
print("=" * 50)
miss = df[num_cols].isna().sum().sort_values(ascending=False)
miss_pct = (miss / len(df) * 100).round(1)
print((miss.astype(str) + "  (" + miss_pct.astype(str) + "%)").to_string())

print("\n" + "=" * 50)
print("T3. Correlation with avg_rating (sorted)")
print("=" * 50)
corr = df[num_cols + ["n_categories", "n_mechanics",
                      "description_length"]].corr()
print(corr["avg_rating"].round(3).sort_values(ascending=False).to_string())

print("\n" + "=" * 50)
print("T4. Top 10 games by rating (users_rated >= 1000)")
print("=" * 50)
t4 = (df.loc[df["users_rated"] >= 1000]
        .sort_values("avg_rating", ascending=False)
        .head(10)[["name", "year_published", "avg_rating",
                   "users_rated", "complexity_weight", "playing_time_min"]])
print(t4.round(2).to_string(index=False))

print("\n" + "=" * 50)
print("T5. Top 10 games by popularity (users_rated)")
print("=" * 50)
t5 = (df.sort_values("users_rated", ascending=False)
        .head(10)[["name", "year_published", "avg_rating",
                   "users_rated", "complexity_weight"]])
print(t5.round(2).to_string(index=False))

print("\n" + "=" * 50)
print("T6. Top 5 most complex games (complexity, users_rated >= 50)")
print("=" * 50)
t6 = (df.loc[df["users_rated"] >= 50]
        .sort_values("complexity_weight", ascending=False)
        .head(5)[["name", "complexity_weight", "avg_rating",
                  "playing_time_min", "users_rated"]])
print(t6.round(2).to_string(index=False))

# ======================================================================
# DONE
# ======================================================================
n_png = len(list(OUT.glob("*.png")))
print(f"\nDone. {n_png} charts saved to: {OUT}")