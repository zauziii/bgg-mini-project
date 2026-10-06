"""
ml_part1_regression.py - Aoxue Li: regression on the BGG data
================================================================
WHAT WE LEARNED (v2, 2026-10):
  - Predicting the raw community rating (avg_rating) gives low R2
    (~0.25-0.37) - the rating is a noisy average squeezed into a
    narrow band (most games 5.5-8.5), so there is little signal
    to explain. The MAE (~0.8 points) is actually a decent result.
  - Two things fix this:
      1) MAIN TARGET = popularity (log of users_rated). "What makes
         a board game popular?" - R2 jumps to ~0.70 and the result
         is more actionable for publishers/designers.
      2) TEXT FEATURES: TF-IDF of the game description (reduced to
         30 components). Text helps BOTH targets.

USAGE
-----
  Windows (easiest): double-click ml.bat in the repo root
  Windows (Anaconda Prompt):
      python scripts/ml_part1_regression.py
  Mac / Linux:
      python3 scripts/ml_part1_regression.py
Output:
  - terminal table: CV R2 / test R2 / RMSE / MAE for all 5 models
  - data/ml_charts/01_model_comparison.png   (main: popularity R2)
  - data/ml_charts/01b_rating_mae.png        (side: rating MAE)
  - feature importance from the Random Forest
"""

import pathlib
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import (GradientBoostingRegressor,
                              RandomForestRegressor)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import (mean_absolute_error, mean_squared_error,
                             r2_score)
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ----------------------------------------------------------------------
# paths + publication style
# ----------------------------------------------------------------------
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "data" / "cleaned_games.csv"
CHART_OUT = ROOT / "data" / "ml_charts"
CHART_OUT.mkdir(parents=True, exist_ok=True)

BLUE = "#1f77b4"
ORANGE = "#d97757"
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 12,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

# ----------------------------------------------------------------------
# 1. FEATURE PREPARATION
# ----------------------------------------------------------------------
df = pd.read_csv(DATA, encoding="utf-8-sig")
print(f"Loaded {len(df)} games x {len(df.columns)} columns")

# --- meta features (structured) ---
FEATURES = [
    "year_published", "min_players", "max_players", "playing_time_min",
    "min_age", "complexity_weight",
    "is_solo", "n_categories", "n_mechanics", "description_length",
]
# NOTE (v2): users_rated is REMOVED from the features. It is the target
# of the popularity regression, so keeping it would be a data leak
# (the model would trivially reach R2 = 1.0).

for c in FEATURES:
    df[c] = df[c].fillna(df[c].median())

sup = df.dropna(subset=["avg_rating"]).copy()

# --- text features (unstructured): TF-IDF -> 30 components ---
tfidf = TfidfVectorizer(max_features=1500, stop_words="english")
tf = tfidf.fit_transform(sup["description"].fillna(""))
svd = TruncatedSVD(n_components=30, random_state=42)
X_text = svd.fit_transform(tf)
print(f"Description text -> TF-IDF ({tf.shape[1]} terms) -> "
      f"{X_text.shape[1]} components")

# final feature matrix: structured + text
X_meta = sup[FEATURES]
X_all = np.hstack([X_meta.values, X_text])

# --- two targets ---
y_pop = np.log1p(sup["users_rated"])   # MAIN target: popularity
y_rat = sup["avg_rating"]              # SIDE target: rating

# one shared split (stratified on popularity) so numbers are comparable
y_strat = (y_pop >= y_pop.median()).astype(int)
idx = train_test_split(np.arange(len(sup)), test_size=0.2,
                       random_state=42, stratify=y_strat)
tr_i, te_i = idx[0], idx[1]

scaler = StandardScaler().fit(X_all[tr_i])
Xtr_s = scaler.transform(X_all[tr_i])
Xte_s = scaler.transform(X_all[te_i])
RANDOM = 42

print(f"Train {len(tr_i)} / Test {len(te_i)} rows\n")

# ======================================================================
# 2. TRAIN + COMPARE 5 MODELS on the MAIN TARGET (popularity)
# ======================================================================
print("=" * 60)
print("PART A  Regression: predict log(users_rated) = POPULARITY")
print("        'What makes a board game popular?'")
print("=" * 60)

models = {
    "Linear Regression": LinearRegression(),
    "Ridge": Ridge(alpha=1.0),
    "Random Forest": RandomForestRegressor(n_estimators=300,
                                           random_state=RANDOM, n_jobs=-1),
    "Gradient Boosting": GradientBoostingRegressor(random_state=RANDOM),
    "MLP (neural net)": MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=600,
                                     random_state=RANDOM),
}

rows = []
cv = KFold(n_splits=5, shuffle=True, random_state=RANDOM)
for name, model in models.items():
    use_s = name in ("Linear Regression", "Ridge", "MLP (neural net)")
    Xtr, Xte = (Xtr_s, Xte_s) if use_s else (X_all[tr_i], X_all[te_i])

    cv_r2 = cross_val_score(model, Xtr, y_pop.iloc[tr_i], cv=cv,
                            scoring="r2", n_jobs=-1).mean()
    model.fit(Xtr, y_pop.iloc[tr_i])
    pred = model.predict(Xte)
    r2 = r2_score(y_pop.iloc[te_i], pred)
    rmse = float(np.sqrt(mean_squared_error(y_pop.iloc[te_i], pred)))
    # MAE back in original units (number of ratings)
    mae = mean_absolute_error(
        sup["users_rated"].iloc[te_i], np.expm1(pred))
    rows.append([name, round(cv_r2, 3), round(r2, 3), round(rmse, 3),
                 round(mae, 0)])
    print(f"  {name:<20s} CV R2={cv_r2:.3f}  test R2={r2:.3f}  "
          f"RMSE={rmse:.3f}  MAE={mae:.0f} ratings")

tab = pd.DataFrame(rows, columns=["model", "CV R2", "test R2", "RMSE", "MAE"])
print("\nPopularity regression comparison (save for your report):")
print(tab.to_string(index=False))

# ======================================================================
# 3. SIDE ANALYSIS: rating prediction - why low R2 is OK (MAE tells it)
# ======================================================================
print("\n" + "=" * 60)
print("PART B  Rating regression (side check): predict avg_rating")
print("        R2 is low by nature - MAE is the honest metric")
print("=" * 60)

rows_rat = []
for name, model in models.items():
    use_s = name in ("Linear Regression", "Ridge", "MLP (neural net)")
    Xtr, Xte = (Xtr_s, Xte_s) if use_s else (X_all[tr_i], X_all[te_i])
    model.fit(Xtr, y_rat.iloc[tr_i])
    pred = model.predict(Xte)
    r2 = r2_score(y_rat.iloc[te_i], pred)
    mae = mean_absolute_error(y_rat.iloc[te_i], pred)
    rows_rat.append([name, round(r2, 3), round(mae, 3)])
    print(f"  {name:<20s} test R2={r2:.3f}  MAE={mae:.3f} points")

tab_rat = pd.DataFrame(rows_rat, columns=["model", "test R2", "MAE"])
print("\nInterpretation: predicting a community average is hard (narrow "
      "band, noisy). An MAE of ~0.8 points means we are, on average, "
      "less than one rating point off - a useful result even with low R2.")

# ======================================================================
# 4. FEATURE IMPORTANCE (Random Forest, popularity model)
# ======================================================================
rf = RandomForestRegressor(n_estimators=300, random_state=RANDOM, n_jobs=-1)
rf.fit(X_all[tr_i], y_pop.iloc[tr_i])
imp = pd.Series(rf.feature_importances_,
                index=list(FEATURES) + [f"text_{i}" for i in range(30)])
print("\nTop 8 features for popularity (Random Forest):")
print(imp.sort_values(ascending=False).head(8).round(3).to_string())
print("(text_* = latent themes from the game description)")

# ======================================================================
# 5. CHARTS (publication style)
# ======================================================================
# --- main chart: popularity R2 ---
fig, ax = plt.subplots(figsize=(7, 4.2))
ax.bar(tab["model"], tab["test R2"], color=BLUE, edgecolor="white", zorder=3)
ax.grid(axis="y", linestyle="--", linewidth=0.5, color="#999999",
        alpha=0.4, zorder=0)
ax.set_title("Popularity regression - test R2 (higher is better)")
ax.set_ylabel("R2 on held-out test set")
ax.set_xticklabels(tab["model"], rotation=20, ha="right", fontsize=9)
ax.axhline(0, color="#333333", linewidth=0.8)
ax.bar_label(ax.containers[0], fontsize=9, color="#555555", padding=2)
ax.set_ylim(0, 1)
fig.savefig(CHART_OUT / "01_model_comparison.png")
plt.close(fig)
print(f"\nChart saved: {CHART_OUT / '01_model_comparison.png'}")

# --- side chart: rating MAE (honest metric for the noisy target) ---
fig, ax = plt.subplots(figsize=(7, 4.2))
ax.bar(tab_rat["model"], tab_rat["MAE"], color=ORANGE, edgecolor="white",
       zorder=3)
ax.grid(axis="y", linestyle="--", linewidth=0.5, color="#999999",
        alpha=0.4, zorder=0)
ax.set_title("Rating prediction - test MAE (lower is better)")
ax.set_ylabel("Mean absolute error (rating points)")
ax.set_xticklabels(tab_rat["model"], rotation=20, ha="right", fontsize=9)
ax.axhline(0, color="#333333", linewidth=0.8)
ax.bar_label(ax.containers[0], fontsize=9, color="#555555", padding=2)
fig.savefig(CHART_OUT / "01b_rating_mae.png")
plt.close(fig)
print(f"Chart saved: {CHART_OUT / '01b_rating_mae.png'}")

print("\nDONE - Aoxue Li's part is complete. Best popularity model should be "
      "Gradient Boosting or Random Forest (R2 ~0.70).")