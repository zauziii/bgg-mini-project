"""
ml_part1_regression.py
===================================================================
Task: predict a game's average rating (0-10) using 5 models:
      Linear Regression, Ridge, Random Forest, Gradient Boosting, MLP.

USAGE
-----
  From the repository root:
      python ml_part1_regression.py
Output:
  - terminal table: CV R2 / test R2 / RMSE / MAE for all 5 models
  - data/ml_charts/01_model_comparison.png
  - cold-start R2 number in the terminal
"""

import pathlib
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.ensemble import (GradientBoostingRegressor,
                              RandomForestRegressor)
from sklearn.base import clone
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import (mean_absolute_error, mean_squared_error,
                             r2_score)
from sklearn.model_selection import KFold, train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from tqdm.auto import tqdm

warnings.filterwarnings("ignore")

# ----------------------------------------------------------------------
# paths + visualization style
# ----------------------------------------------------------------------
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE
DATA = ROOT / "data" / "cleaned_games.csv"
CHART_OUT = ROOT / "data" / "ml_charts"
CHART_OUT.mkdir(parents=True, exist_ok=True)

BLUE = "#1f77b4"
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
# 1. FEATURE PREPARATION (the same for everyone)
# ----------------------------------------------------------------------
df = pd.read_csv(DATA, encoding="utf-8-sig")
print(f"Loaded {len(df)} games x {len(df.columns)} columns")

FEATURES = [
    "year_published", "min_players", "max_players", "playing_time_min",
    "min_age", "complexity_weight", "users_rated",
    "is_solo", "n_categories", "n_mechanics", "description_length",
]
for c in FEATURES:
    df[c] = df[c].fillna(df[c].median())

sup = df.dropna(subset=["avg_rating"]).copy()
X = sup[FEATURES]
y = sup["avg_rating"]
print(f"Supervised rows: {len(sup)}")

# same split as the full ml.py (stratify on the good-game flag)
# so everyone's numbers match the merged pipeline
y_strat = (sup["avg_rating"] >= 7).astype(int)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y_strat)
print(f"Train {len(X_train)} / Test {len(X_test)} rows\n")

scaler = StandardScaler().fit(X_train)      # needed by Linear/Ridge/MLP
Xtr_s, Xte_s = scaler.transform(X_train), scaler.transform(X_test)
RANDOM = 42

# ======================================================================
# 2. TRAIN + COMPARE 5 MODELS
# ======================================================================
print("=" * 60)
print("PART A  Regression: predict avg_rating  (5 models)")
print("=" * 60)

models = {
    "Linear Regression": LinearRegression(),
    "Ridge": Ridge(alpha=1.0),
    "Random Forest": RandomForestRegressor(n_estimators=300,
                                           random_state=RANDOM, n_jobs=1),
    "Gradient Boosting": GradientBoostingRegressor(random_state=RANDOM),
    "MLP (neural net)": MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=600,
                                     random_state=RANDOM),
}

rows = []
cv = KFold(n_splits=5, shuffle=True, random_state=RANDOM)
for name, model in tqdm(models.items(), total=len(models), desc="Models",
                        unit="model"):
    use_s = name in ("Linear Regression", "Ridge", "MLP (neural net)")
    Xtr, Xte = (Xtr_s, Xte_s) if use_s else (X_train, X_test)
    Xtr = np.asarray(Xtr)
    ytr = y_train.to_numpy()

    # 5-fold cross-validation score on the training part
    fold_scores = []
    for train_idx, val_idx in tqdm(cv.split(Xtr, ytr), total=cv.get_n_splits(),
                                   desc=f"{name} CV", unit="fold",
                                   leave=False):
        fold_model = clone(model)
        fold_model.fit(Xtr[train_idx], ytr[train_idx])
        fold_scores.append(r2_score(ytr[val_idx],
                                    fold_model.predict(Xtr[val_idx])))
    cv_r2 = float(np.mean(fold_scores))
    # refit on all training data -> evaluate on the held-out test part
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)
    r2 = r2_score(y_test, pred)
    rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
    mae = mean_absolute_error(y_test, pred)
    rows.append([name, round(cv_r2, 3), round(r2, 3), round(rmse, 3),
                 round(mae, 3)])
    print(f"  {name:<20s} CV R2={cv_r2:.3f}  test R2={r2:.3f}  "
          f"RMSE={rmse:.3f}  MAE={mae:.3f}")

tab = pd.DataFrame(rows, columns=["model", "CV R2", "test R2", "RMSE", "MAE"])
print("\nRegression comparison (save this table for your report):")
print(tab.to_string(index=False))

# ======================================================================
# 3. COLD-START CHECK (models how we can rate NEW games)
# ======================================================================
rf = RandomForestRegressor(n_estimators=300, random_state=RANDOM, n_jobs=1)
feat_no_pop = [f for f in FEATURES if f != "users_rated"]
rf.fit(X_train[feat_no_pop], y_train)
cold_r2 = r2_score(y_test, rf.predict(X_test[feat_no_pop]))
print(f"\nCold-start check (drop users_rated): R2 {tab.loc[2, 'test R2']:.3f} "
      f"-> {cold_r2:.3f}")
print("Interpretation: even for a brand-new game with zero ratings,")
print("we can still predict its quality from year/complexity/text features.")

# ======================================================================
# 4. CHART: model comparison
# ======================================================================
fig, ax = plt.subplots(figsize=(7, 4.2))
ax.bar(tab["model"], tab["test R2"], color=BLUE, edgecolor="white", zorder=3)
ax.grid(axis="y", linestyle="--", linewidth=0.5, color="#999999",
        alpha=0.4, zorder=0)
ax.set_title("Regression models - test R2 (higher is better)")
ax.set_ylabel("R2 on held-out test set")
ax.set_xticklabels(tab["model"], rotation=20, ha="right", fontsize=9)
ax.axhline(0, color="#333333", linewidth=0.8)
ax.bar_label(ax.containers[0], fontsize=9, color="#555555", padding=2)
fig.savefig(CHART_OUT / "01_model_comparison.png")
plt.close(fig)
print(f"\nChart saved: {CHART_OUT / '01_model_comparison.png'}")
print("\nDONE - your part is complete. Best model should be Random Forest.")
