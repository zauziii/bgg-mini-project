# 🎲 BGG Board Game Data Pipeline

A University of Helsinki Data Science mini project that collects board game data from **BoardGameGeek (BGG)**, prepares an analysis dataset, compares machine learning methods, and serves recommendations through a Streamlit app.

[![BGG API](https://img.shields.io/badge/source-BoardGameGeek%20XML%20API2-orange)](https://boardgamegeek.com/xmlapi2) [![Streamlit](https://img.shields.io/badge/web%20app-Streamlit-FF4B4B)](https://bgg-mini-project.streamlit.app) [![API terms](https://img.shields.io/badge/data%20use-BGG%20API%20Terms-blue)](https://boardgamegeek.com/wiki/page/XML_API_Terms_of_Use)

**[Open the app](https://bgg-mini-project.streamlit.app)** · [Quick start](#quick-start) · [Analysis results](#analysis-and-machine-learning) · [Team contributions](#team-and-contributions)

## At a glance

| Item | Summary |
|---|---|
| Dataset | 2,077 board games and 26 cleaned columns |
| Source | BGG XML API2: `thing`, `search`, and `hot` endpoints |
| Collection | Hot list and 50 keyword searches, followed by filtering to core board games |
| Workflow | Download → Clean → Explore → Model → Web app |
| Analysis | Exploratory analysis, regression, classification, text analysis, and content-based recommendations |
| Web app | Five pages: Home, Find me a game, Explore the data, More like this, and Board Game Bestiary |

## Quick start

Run the commands below **from the repository root**. In Anaconda, open Anaconda Prompt and activate your project environment first. On macOS/Linux, use `python3` in place of `python` if required by your environment.

### 1. Install dependencies

```bash
python -m pip install -r requirements.txt
```

The EDA and machine learning scripts also require the following packages:

```bash
python -m pip install pandas numpy matplotlib scikit-learn scipy
```

### 2. Run the app

The cleaned dataset is included in the repository. If the recommendation outputs are also present, start the app directly:

```bash
python -m streamlit run webapp/app.py
```

Open [http://localhost:8501](http://localhost:8501) if the browser does not open automatically.

The app uses `data/cleaned_games.csv` and the recommendation outputs, including `data/recommendation_scores.csv` and `data/similar_games.csv`. If these outputs are missing, generate them first:

```bash
python scripts/ml_part3_recommender.py
```

On Windows, `run_webapp.bat` provides a launcher. On macOS/Linux, use `bash run_webapp.sh`.

### 3. Rebuild the pipeline

Downloading the data again is optional when using the committed snapshot. A new download may change the dataset and the resulting scores.

<details>
<summary><strong>Download data from BGG</strong></summary>

Register an application and obtain an API token at [boardgamegeek.com/applications](https://boardgamegeek.com/applications).

**Windows — Anaconda Prompt / Command Prompt:**

```bat
set "BGG_API_TOKEN=your_token"
python scripts\fetch_bgg.py --out data
```

**macOS / Linux:**

```bash
export BGG_API_TOKEN="your_token"
python3 scripts/fetch_bgg.py --out data
```

Windows users can also double-click `run.bat` and enter the token when prompted. The original download took approximately 20 minutes; timing depends on the API and cache state.

Output: `data/games.csv`. Raw XML responses are cached in `data/raw/` so interrupted runs can reuse downloaded responses.

</details>

<details>
<summary><strong>Clean the data</strong></summary>

```bash
python scripts/clean_bgg_data.py
```

Launchers: `clean.bat` on Windows or `bash clean.sh` on macOS/Linux.

Output: `data/cleaned_games.csv`.

</details>

<details>
<summary><strong>Run exploratory analysis</strong></summary>

```bash
python scripts/eda.py
```

Launchers: `eda.bat` on Windows or `bash eda.sh` on macOS/Linux.

Output: 14 PNG charts in `data/charts/`.

</details>

<details>
<summary><strong>Run machine learning and generate recommendations</strong></summary>

```bash
python scripts/ml_part1_regression.py
python scripts/ml_part2_classification.py
python scripts/ml_part3_recommender.py
```

Optional category-level text analysis:

```bash
python scripts/ml_part2_discriminative_words.py
```

Launchers: `ml_parts.bat` on Windows or `bash ml_parts.sh` on macOS/Linux.

Outputs: model charts in `data/ml_charts/`, `data/recommendation_scores.csv`, and `data/similar_games.csv`.

</details>

## Analysis and machine learning

The following approximate results describe the project snapshot. Consult the scripts and [technical report](report/technical_report.pdf) for the analysis details; these values are not guarantees for a fresh download or a different evaluation split.

| Part | Question | Approach | Snapshot result or output |
|---|---|---|---|
| EDA | What patterns appear in the collected games? | Distributions, release-year trends, categories, mechanics, and correlations | 14 charts; rating–complexity correlation approximately 0.50 |
| Part 1 — Regression | How well can game attributes predict popularity? | Linear regression, Ridge, random forest, gradient boosting, and MLP | Test R² approximately 0.70 for `log(users_rated)` |
| Part 1 — Rating analysis | How well can game attributes predict average rating? | Rating prediction as a secondary analysis | Test R² approximately 0.25–0.37; MAE approximately 0.8 rating points |
| Part 2 — Classification | Can a game be classified as having an average rating of at least 7? | Logistic regression, random forest, gradient boosting, and MLP; class weighting where applied | Test ROC-AUC approximately 0.85. Majority-class baseline **accuracy** approximately 0.69; this is a separate metric |
| Part 2 — Text | Which words characterise each major game category? | Category-level TF-IDF profiles | Examples for economic games: *market*, *auction*, and *trade* |
| Part 3 — Game finder | Which games fit the selected group and preferences? | A transparent fit score using player count, play time, complexity, quality, and popularity | Top-10 recommendation lists |
| Part 3 — Similar games | Which games share categories and mechanics? | Jaccard similarity on categories and mechanics, with same-series matches excluded | Top-5 neighbours per game |

### Features and evaluation

The predictive analyses use structured game attributes and 30 components derived from game descriptions through TF-IDF and SVD. The classifier excludes `users_rated` as a predictor.

These are retrospective predictions for games in the collected dataset. BGG's [complexity/weight score](https://boardgamegeek.com/wiki/page/weight) is a community rating. A model using `complexity_weight` or its derived groups therefore does not have a strictly prerelease feature set. The recommendation system also uses existing rating and popularity information.

To reproduce and assess the predictive results:

- Record the data snapshot, eligible sample size, train/test split, random seed, target definition, and model associated with each score.
- Check that the classifier's predictors exclude its target `avg_rating` and rating-derived fields such as `bayes_rating`, `board_game_rank`, and `rank_tier`.
- Fit TF-IDF, SVD, imputation, scaling, and other learned preprocessing on training data only. During cross-validation, fit them within each training fold, for example through a scikit-learn `Pipeline`.
- Compare the same metrics on the same evaluation sample. ROC-AUC and accuracy should be reported separately.

The fit score and Jaccard neighbours are recommendation rules; the predictive model scores above do not establish their recommendation quality.

## Repository structure

```text
.
├── data/           # Raw cache, cleaned data, charts, and recommendation CSVs
├── scripts/        # Collection, cleaning, EDA, ML, and recommendation scripts
├── webapp/         # Streamlit modules and Bestiary artwork
├── report/         # Technical report and Quarto source
├── presentation/   # Final presentation slides
├── canvas/         # Project proposal canvas: DOCX and HTML
├── .streamlit/     # Streamlit theme configuration
└── requirements.txt
```

<details>
<summary><strong>Key files</strong></summary>

| File | Purpose |
|---|---|
| `scripts/fetch_bgg.py` | Collect the hot list and keyword-search candidates, fetch details, and cache XML responses; approximately 4,000 candidates yielded 2,077 core games in the project snapshot |
| `scripts/clean_bgg_data.py` | Remove duplicate IDs, normalise missing values, convert types, and engineer analysis variables |
| `scripts/eda.py` | Generate 14 exploratory charts in `data/charts/` |
| `scripts/ml_part1_regression.py` | Popularity regression, description features, and the secondary rating analysis |
| `scripts/ml_part2_classification.py` | Rating-threshold classification, ROC/PR curves, confusion matrices, and feature importance |
| `scripts/ml_part2_discriminative_words.py` | Generate TF-IDF word profiles for major game categories |
| `scripts/ml_part3_recommender.py` | Generate game-finder scores and similar-game neighbours |
| `webapp/app.py` | Configure the app, styling, and sidebar routing |
| `webapp/part1_find.py` | Home and game-finder pages |
| `webapp/part2_explore.py` | Interactive Plotly data explorer |
| `webapp/part3_more.py` | Similar-game page and Bestiary quiz |
| `data/games.csv` | Raw tabular export from the downloader |
| `data/cleaned_games.csv` | Cleaned analysis dataset: 2,077 rows and 26 columns |
| `data/recommendation_scores.csv` | Scores used by the game finder |
| `data/similar_games.csv` | Top-5 similar games for each game |
| `report/final_report.pdf` | Technical report |
| `report/final_report.qmd` | Quarto source for the report |

</details>

## Data and cleaning

The collection starts with BGG's hot list and 50 keyword searches. After fetching game details and applying the project's filters, the documented dataset contains 2,077 core board games.

The cleaning script handles duplicate IDs, text-formatted numbers, missing-value codes, and derived variables. Examples recorded for the raw snapshot include 402 games with `playing_time=0` and 197 with `avg_rating=0.0`.

| Field or issue | Project handling and interpretation |
|---|---|
| Duplicate `game_id` | Drop duplicate rows |
| Numeric values stored as text | Convert to numeric types |
| Zero year, play time, average rating, or complexity | Treat as missing under the project's cleaning rules |
| `users_rated=0` | The documented cleaning rule also maps these values to missing. This needs field-specific interpretation: zero may be a valid count of games with no ratings, rather than missing data |
| Negative publication year | Treat as missing for modern release-year analysis. A negative year can represent an ancient game; it is not inherently an invalid value. The raw export retains the source value |
| Literal `"Not Ranked"` | Normalise to missing rank |
| `min_age=0` | Retain the source code; without further evidence, do not interpret it as a confirmed absence of age restrictions |

<details>
<summary><strong>Data dictionary — data/cleaned_games.csv</strong></summary>

Combined rows below describe more than one column; the full dataset has 26 columns.

| Column | Description |
|---|---|
| `game_id` | BGG game identifier |
| `name` | Primary game name |
| `year_published` | Publication year after cleaning; missing when unavailable or excluded by the year-cleaning rule |
| `min_players` / `max_players` | Supported player-count range |
| `playing_time_min` | Typical play time in minutes |
| `min_playtime` / `max_playtime` | Minimum and maximum play time in minutes |
| `min_age` | Recommended minimum age; source code `0` is retained |
| `users_rated` | Number of user ratings, subject to the zero-handling rule above |
| `avg_rating` | Average user rating on the 1–10 scale |
| `bayes_rating` | BGG Bayesian rating; missing where unavailable under the cleaning rules |
| `complexity_weight` | Community complexity/weight rating on the 1–5 scale |
| `board_game_rank` | Overall BGG rank; missing for unranked games |
| `categories` | Semicolon-separated game categories |
| `mechanics` | Semicolon-separated game mechanics |
| `designers` | Semicolon-separated designer names |
| `description` | Free-text game description |
| `description_length` | Description length in characters |
| `decade` | Release decade, such as 2010; `0` denotes unknown |
| `complexity_group` | `light`, `medium`, `heavy`, or `unknown` |
| `playtime_group` | `short` (≤30 minutes), `medium` (31–90), `long` (>90), or `unknown` |
| `is_solo` | `1` when the recorded player range supports solo play |
| `rank_tier` | `top1000`, `top5000`, `ranked`, or `unranked` |
| `n_categories` / `n_mechanics` | Counts of categories and mechanics |

</details>

## Web app

**Live app:** [bgg-mini-project.streamlit.app](https://bgg-mini-project.streamlit.app)

| Page | What it provides |
|---|---|
| Home | Project overview and data-source information |
| Find me a game | Player-count, time, and complexity controls that return ten fitting games |
| Explore the data | Interactive Plotly charts with year, category, and complexity filters, plus hover and zoom |
| More like this | Five similar games for a selected title |
| Board Game Bestiary | An eight-question parody quiz that links one of four player creatures to game suggestions |

<details>
<summary><strong>Bestiary characters</strong></summary>

- 🏗️ **Tung Tung Tung Tung Sahur — The City Builder:** economic, city-building, and civilization games.
- 🏖️ **Tralalero Tralala — The Beach Party Animal:** party, dexterity, and word games.
- 📜 **Luguanluguan — The Rule Sheriff:** abstract strategy and deduction games.
- 💣 **Bombardino Crocodillo — The Bombardier:** dice, wargames, and fighting games.

</details>

## Limitations

- **Sample coverage:** the hot list and keyword searches give a selected sample of BGG games, so the findings may not apply to the full database.
- **Data snapshot:** ratings and rating counts change over time. Here, popularity means the number of user ratings at collection time.
- **Model performance:** reported scores apply to this dataset and evaluation split. Results for newly collected games or a different sample may differ.

## Team and contributions

| Member | Programme | Main responsibilities |
|---|---|---|
| **Aoxue Li** | Life Science Informatics | Cleaning and feature engineering; Part 1 regression; Home and game-finder pages; macOS/Linux launchers; presentation slides; README and documentation |
| **Ezeme Onyenezi Innocent** | Computer Science | EDA; Part 2 classification and text analysis; data-explorer page; similar-game page and Bestiary quiz |
| **Zhi Zhou** | Life Science Informatics | BGG downloader and cache; recommendation and similarity engine; app shell and integration; Windows launchers; deployment and environment configuration; README and documentation |

The report and proposal were prepared and reviewed jointly by all three members.

<details>
<summary><strong>Detailed task division</strong></summary>

**●** lead / module owner · **◐** joint work, testing, or review · **—** not involved

| Work package | Aoxue | Ezeme | Zhi |
|---|:---:|:---:|:---:|
| Data collection: BGG downloader and caching | ◐ | — | ● |
| Cleaning and feature engineering | ● | — | ◐ |
| Exploratory analysis: 14 charts | — | ● | ◐ |
| Part 1: popularity / rating regression | ● | ◐ | ◐ |
| Part 2: rating-threshold classification | ◐ | ● | ◐ |
| Part 2: discriminative-words text analysis | ◐ | ● | ◐ |
| Part 3: recommender and similar games | ◐ | ◐ | ● |
| Web app: Home and Find me a game | ● | ◐ | ◐ |
| Web app: Explore the data | ◐ | ● | ◐ |
| Web app: More like this and Bestiary | ◐ | ● | ◐ |
| App shell, theme, and integration | ◐ | ◐ | ● |
| macOS/Linux `.sh` launchers | ● | ◐ | ◐ |
| Windows `.bat` launchers | ◐ | ◐ | ● |
| Deployment and environment configuration | ◐ | ◐ | ● |
| Report, Quarto source, and proposal | ◐ | ◐ | ◐ |
| Presentation slides | ● | ◐ | ◐ |
| Oral presentation | ◐ | ◐ | ◐ |
| README and project documentation | ● | — | ● |

</details>

### Contribution estimate

These percentages are a **team self-assessment**, based on the role weights below. They are not measured working hours or commit shares.

| Work-package pattern | Points assigned |
|---|---|
| Three joint contributors: ◐ / ◐ / ◐ | 100/3 points each |
| One lead and two reviewers: ● / ◐ / ◐ | Lead: 60; each reviewer: 20 |
| Two leads: ● / — / ● | Each lead: 50; non-participant: 0 |
| One lead and one reviewer, with one non-participant | Lead: 60; reviewer: 20; non-participant: 0 |

There are 18 work packages. **Three packages**—data collection, cleaning, and EDA—receive 80 points each under this convention. The other 15 receive 100 points each, giving a total of **1,740 points**. The 80-point packages consequently carry less total weight than the 100-point packages.

| Member | Share of allocated points |
|---|---:|
| Aoxue Li | 34.29% |
| Ezeme Onyenezi Innocent | 30.27% |
| Zhi Zhou | 35.44% |
| **Total** | **100.00%** |

``` mermaid
%%{init: {'theme': 'base', 'themeVariables': {'pie1': '#4E79A7', 'pie2': '#F28E2B', 'pie3': '#59A14F'}}}%%
pie showData
    title Overall contribution (team self-assessment)
    "Aoxue Li" : 34
    "Ezeme Onyenezi Innocent" : 31
    "Zhi Zhou" : 35
```

Commit counts are not used to measure effort because members had different levels of Git/GitHub experience. The README and documentation package is split equally between its two named leads.

### AI assistance log

The percentages below are the team's estimates of AI involvement within each work package. They are not measured percentages of final code or authorship, and they are separate from the human contribution estimates above.

The team reports reviewing, running, and validating AI-generated code, and checking AI-assisted text and layout before inclusion. Team members remain responsible for their deliverables.

| Work package | Estimated AI involvement | Assistance reported by the team |
|---|---:|---|
| Data collection: downloader and caching | 55% | Writing downloader code and cache logic |
| Cleaning and feature engineering | 10% | Edge-case handling and debugging |
| Exploratory data analysis | 10% | Plotting-code assistance |
| Part 1: regression | 10% | Debugging model-fitting code |
| Part 2: rating-threshold classification | 10% | Debugging evaluation code |
| Part 2: discriminative-words NLP | 15% | Writing and debugging the text-analysis pipeline |
| Part 3: recommender and similar games | 15% | Similarity-matching logic |
| Web app: Home and Find me a game | 55% | Page logic, layout, and debugging |
| Web app: Explore the data | 50% | Page logic and charts |
| Web app: More like this and Bestiary | 60% | Page logic, quiz flow, and matching rules |
| App shell, theme, and integration | 55% | App shell, theme, and page integration |
| Report and Quarto source | 10% | YAML configuration, syntax corrections, and layout fixes |
| macOS/Linux `.sh` launchers | 50% | Generating and debugging shell launchers |
| Windows `.bat` launchers | 50% | Generating and debugging batch launchers |
| Deployment and environment configuration | 10% | Environment-setup assistance |
| Presentation slides | 10% | Layout adjustments |
| Oral presentation | 0% | No AI assistance reported |
| README and project documentation | 30% | Contribution-diagram suggestion, Markdown formatting, command corrections, and wording review |

## API token and data use

The downloader reads the BGG API token from `BGG_API_TOKEN` or an interactive prompt. Keep token values out of source files and commits. The repository's ignore rules cover local token files and the raw-response cache.

BGG data use is governed by the [BGG XML API Terms of Use](https://boardgamegeek.com/wiki/page/XML_API_Terms_of_Use). The terms badge above refers to the data source; it does not specify a software licence for this repository.
