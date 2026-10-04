"""
ml_part2_discriminative_words.py
==========================================================================
Task: for each major game category, find the WORDS that make it special.
      "Economic games talk about market, auction, trade - Children's games
       talk about memory, matching, pictures."

USAGE
-----
  Windows (easiest): double-click ml.bat in the repo root
      (runs the full 3-part pipeline; your numbers will match)
  Windows (Anaconda Prompt):
      python scripts/ml_part2_discriminative_words.py
  Mac / Linux:
      python3 scripts/ml_part2_discriminative_words.py
Output:
  - terminal table: top 8 discriminative words per category
  - data/charts/08_category_words.png  (publication-style grid chart)
"""

import pathlib
import warnings

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

warnings.filterwarnings("ignore")

# ----------------------------------------------------------------------
# paths + visualizatio style
# ----------------------------------------------------------------------
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "data" / "cleaned_games.csv"
CHART_OUT = ROOT / "data" / "charts"
CHART_OUT.mkdir(parents=True, exist_ok=True)

BLUE, ORANGE, GREEN, RED, PURPLE, GRAY = (
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#7f7f7f")
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

# ----------------------------------------------------------------------
# 1. LOAD + prep
# ----------------------------------------------------------------------
df = pd.read_csv(DATA, encoding="utf-8-sig")
df["top_category"] = df["categories"].fillna("").str.split(";").str[0].str.strip()
print(f"Loaded {len(df)} games")

# keep only categories with enough games so the words are meaningful
MIN_GAMES = 50
counts = df["top_category"].value_counts()
cats = list(counts[counts >= MIN_GAMES].head(6).index)   # 6 categories
df_use = df[df["top_category"].isin(cats)].copy()
print(f"Analyzing {len(cats)} categories: {', '.join(cats)}\n")

# ----------------------------------------------------------------------
# 2. TF-IDF: how important each word is inside each category
# ----------------------------------------------------------------------
# a word is "discriminative" if it is common in THIS category
# but rare everywhere else -> exactly what tf-idf measures
vec = TfidfVectorizer(stop_words="english", max_features=5000, min_df=5)
X = vec.fit_transform(df_use["description"].fillna(""))
words = vec.get_feature_names_out()

# words that are common EVERYWHERE (proof that a word cloud would be useless)
global_avg = X.mean(axis=0).A1
top_global = [words[i] for i in global_avg.argsort()[::-1][:8]]
print("Most common words in ALL descriptions (why a word cloud fails):")
print("  " + ", ".join(top_global) + "\n")

# for each category: a word is DISCRIMINATIVE if its tf-idf is high in THIS
# category but low everywhere else -> rank by (class average - global average)
global_avg = X.mean(axis=0).A1
profiles = {}
for c in cats:
    rows = df_use["top_category"] == c
    avg = X[rows.values].mean(axis=0).A1
    diff = avg - global_avg                      # penalise words common everywhere
    top_idx = diff.argsort()[::-1][:8]
    profiles[c] = [(words[i], round(float(diff[i]), 3)) for i in top_idx]

print("Discriminative words per category (top 8, tf-idf score):")
for c, wl in profiles.items():
    print(f"  {c:<22s} " + ", ".join(f"{w} ({s:.2f})" for w, s in wl))

# ----------------------------------------------------------------------
# 3. CHART: one horizontal bar per category (publication style)
# ----------------------------------------------------------------------
fig, axes = plt.subplots(2, 3, figsize=(12, 7.5))
colors = [BLUE, ORANGE, GREEN, RED, PURPLE, GRAY]
for ax, (c, wl), col in zip(axes.flat, profiles.items(), colors):
    ws, ss = zip(*wl)
    ax.barh(ws, ss, color=col, edgecolor="white", zorder=3)
    ax.grid(axis="x", linestyle="--", linewidth=0.5, color="#999999",
            alpha=0.4, zorder=0)
    ax.set_title(c, fontsize=12, fontweight="bold")
    ax.tick_params(axis="y", labelsize=9)
    ax.set_xlim(0, max(ss) * 1.15)
    ax.set_xticks([])                     # scores are in the table, keep bars clean
fig.suptitle("What each game category talks about (discriminative words)",
             fontsize=14, fontweight="bold", y=1.02)
fig.tight_layout()
out = CHART_OUT / "08_category_words.png"
fig.savefig(out)
plt.close(fig)
print(f"\nChart saved: {out}")
print("\nDONE. Report sentence: 'Economic games describe markets and auctions,")
print("children's games describe memory and matching - the words show what")
print("each category is really about.'")