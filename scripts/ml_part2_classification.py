"""
ml_part2_classification.py
=======================================================================
Task A: predict "is this a GOOD game?" (rating >= 7) with 4 classifiers:
        Logistic Regression, Random Forest, Gradient Boosting, MLP.
Task B: feature importance - which variables drive the rating?

USAGE
-----
  Windows (easiest): double-click ml.bat in the repo root
      (runs the full 3-part pipeline; your numbers will match)
  Windows (Anaconda Prompt):
      python scripts/ml_part2_classification.py
  Mac / Linux:
      python3 scripts/ml_part2_classification.py
Output:
  - terminal table: CV AUC / test AUC / F1 / accuracy for 4 classifiers
  - data/ml_charts/03_confusion_matrix.png
  - data/ml_charts/02_feature_importance.png
  - top features list in the terminal

See also:
  scripts/ml_part2_discriminative_words.py  (tf-idf word profiles per category)
"""

import pathlib
import warnings

import matplotlib.pyplot as plt
import pandas as pd

from sklearn.ensemble import (GradientBoostingClassifier,
                              RandomForestClassifier)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             roc_auc_score)
from sklearn.model_selection import (StratifiedKFold, cross_val_score,
                                     train_test_split)
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ----------------------------------------------------------------------
# paths + visualization style
# ----------------------------------------------------------------------
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "data" / "cleaned_games.csv"
CHART_OUT = ROOT / "data" / "ml_charts"
CHART_OUT.mkdir(parents=True, exist_ok=True)

BLUE, GREEN = "#1f77b4", "#2ca02c"
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

FEATURES = [
    "year_published", "min_players", "max_players", "playing_time_min",
    "min_age", "complexity_weight", "users_rated",
    "is_solo", "n_categories", "n_mechanics", "description_length",
]
for c in FEATURES:
    df[c] = df[c].fillna(df[c].median())

sup = df.dropna(subset=["avg_rating"]).copy()
X = sup[FEATURES]
# target: 1 = good game (rating >= 7). Watch out: only ~31% are positive.
y = (sup["avg_rating"] >= 7).astype(int)
print(f"Supervised rows: {len(sup)}  | good-game share: {y.mean():.1%}")
print("(imbalanced - we use class_weight='balanced' and report AUC)")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)
print(f"Train {len(X_train)} / Test {len(X_test)} rows\n")

scaler = StandardScaler().fit(X_train)      # needed by Logistic/MLP
Xtr_s, Xte_s = scaler.transform(X_train), scaler.transform(X_test)
RANDOM = 42

# ======================================================================
# 2. TASK A - CLASSIFY "IS IT A GOOD GAME?"
# ======================================================================
print("=" * 60)
print("PART B  Classification: is it a good game? (rating >= 7)")
print("=" * 60)

models = {
    "Logistic Regression": LogisticRegression(max_iter=1000,
                                              class_weight="balanced"),
    "Random Forest": RandomForestClassifier(n_estimators=300,
                                            class_weight="balanced",
                                            random_state=RANDOM, n_jobs=-1),
    "Gradient Boosting": GradientBoostingClassifier(random_state=RANDOM),
    "MLP (neural net)": MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=600,
                                      random_state=RANDOM),
}

rows = []
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM)
for name, model in models.items():
    use_s = name in ("Logistic Regression", "MLP (neural net)")
    Xtr, Xte = (Xtr_s, Xte_s) if use_s else (X_train, X_test)

    cv_auc = cross_val_score(model, Xtr, y_train, cv=cv,
                             scoring="roc_auc", n_jobs=-1).mean()
    model.fit(Xtr, y_train)
    proba = model.predict_proba(Xte)[:, 1]
    pred = model.predict(Xte)
    auc = roc_auc_score(y_test, proba)
    f1 = f1_score(y_test, pred)
    acc = accuracy_score(y_test, pred)
    rows.append([name, round(cv_auc, 3), round(auc, 3), round(f1, 3),
                 round(acc, 3)])
    print(f"  {name:<20s} CV AUC={cv_auc:.3f}  test AUC={auc:.3f}  "
          f"F1={f1:.3f}  acc={acc:.3f}")

tab = pd.DataFrame(rows, columns=["model", "CV AUC", "test AUC", "F1", "accuracy"])
print("\nClassification comparison (save this table for your report):")
print(tab.to_string(index=False))

# ======================================================================
# 3. CONFUSION MATRIX of the best model (Random Forest)
# ======================================================================
best = RandomForestClassifier(n_estimators=300, class_weight="balanced",
                              random_state=RANDOM, n_jobs=-1)
best.fit(X_train, y_train)
cm = confusion_matrix(y_test, best.predict(X_test))
print(f"\nConfusion matrix (Random Forest):\n{cm}")

fig, ax = plt.subplots(figsize=(5.2, 4.2))
im = ax.imshow(cm, cmap="Blues")
ax.set_xticks([0, 1]); ax.set_xticklabels(["not good", "good"])
ax.set_yticks([0, 1]); ax.set_yticklabels(["not good", "good"])
ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
ax.set_title("Good-game classifier - confusion matrix (Random Forest)")
for i in range(2):
    for j in range(2):
        ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center",
                fontsize=14, color="white" if cm[i, j] > cm.max() / 2
                else "#333333")
fig.savefig(CHART_OUT / "03_confusion_matrix.png")
plt.close(fig)
print(f"Chart saved: {CHART_OUT / '03_confusion_matrix.png'}")

# ======================================================================
# 4. TASK B - FEATURE IMPORTANCE (what drives the rating?)
# ======================================================================
print("\n" + "=" * 60)
print("PART B2  Feature importance (Random Forest, cold-start model)")
print("=" * 60)
feat_no_pop = [f for f in FEATURES if f != "users_rated"]
rf = RandomForestClassifier(n_estimators=300, class_weight="balanced",
                            random_state=RANDOM, n_jobs=-1)
rf.fit(X_train[feat_no_pop], y_train)
imp = pd.Series(rf.feature_importances_, index=feat_no_pop).sort_values()
print(imp.round(3).to_string())
print("\nTop 3 for your report:")
print(imp.tail(3).round(3).to_string())

fig, ax = plt.subplots(figsize=(7, 4.6))
imp.tail(10).plot(kind="barh", color=GREEN, edgecolor="white", ax=ax, zorder=3)
ax.grid(axis="x", linestyle="--", linewidth=0.5, color="#999999",
        alpha=0.4, zorder=0)
ax.set_title("Top features driving the rating (cold-start model)")
ax.set_xlabel("Importance (Gini)")
ax.bar_label(ax.containers[0], fontsize=9, color="#555555", padding=3)
fig.savefig(CHART_OUT / "02_feature_importance.png")
plt.close(fig)
print(f"Chart saved: {CHART_OUT / '02_feature_importance.png'}")
print("\nDONE - your part is complete.")