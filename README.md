#  BGG Borad Game Data Pipeline

Board game dataset downloaded from the **official BoardGameGeek XML API2**, cleaned in to a tiday CSV for a University of Helsinki *Data Science* mini project.

- **Games:** 2,077 board games × 18 raw fields (26 after cleaning)
- **Source:** [boardgamegeek.com/xmlapi2](https://boardgamegeek.com/xmlapi2) - `thing`, `search`, `hot` endpoints.
- **Terms of use:** https://boardgamegeek.com/wiki/page/XML_API_Terms_of_Use

## Repository structure
| Folder | Content |
|---|---|
| `data/` | raw & cleaned datasets (work in progress) |
| `scripts/` | data pipelines and regression analysis |
| `canvas/` | mini-project [canvas](https://docs.google.com/document/d/1OYbvQNJgDx0BgSNYbPcRcZpna5havE-W1R5lEIug1BU/edit?usp=sharing) (proposal)
| `notebooks/` | EDA & modeling notebooks (work in progress) |
| `webapp/` | interactive visualization web app modules and assets |
| `blog/` | blog post materials (work in progress) |
| `presentation/` | spotlight presentation slides (work in progress) |
| `final_report.pdf` / `final_report.qmd` | technical report and Quarto source |

## Files

| File | What it is |
|---|---|
| `scripts/fetch_bgg.py` | hot list + 50 keyword searches → ~4,000 candidate IDs → 2,077 core board games after filtering out expansions & non-game entries |
| `scripts/ml_part1_regression.py` | Popularity regression with TF-IDF/SVD description features and rating MAE side analysis |
| `webapp/part1_find.py` | Home and game-finder functionality for the web app |
| `data/games.csv` | Raw export straight from the downloader (uncleaned) |
| `run.bat` | Windows one-click downloader (double-click, paste token) |
| `README.md` | This file |


## Quick start

The pipeline has two steps: **download** then **clean**. Pick your platform below.

### Step 1 - Download the data

**Windows (easiest):** double-click `run.bat` in the repo root, paste your token when asked (get one at https://boardgamegeek.com/applications), wait ~20 minutes → `data/games.csv`.

**Windows (manual, Anoconda Prompt):**

```bat
set BGG_API_TOKEN="your token"
python scripts\fetch_bgg.py --out data
```

**Mac / Linux:**

```bash
export BGG_API_TOKEN="your token"
python3 scripts/fetch_bgg.py --out data
```

### Step 2 - Clean the data

**Windows (easiest):**

**Windows (manual, Anoconda Prompt):**

**Mac / Linux:**

## Columns (data/cleaned_games.csv)

| Column | Description |
|---|---|
| `game_id` | BGG game id |
| `name` | primary name |
| `year_published` | release year (NaN = unknown) |
| `min_players` / `max_players` | player count range |
| `playing_time_min` | typical play time in minutes |
| `min_playtime` / `max_playtime` | play time range |
| `min_age` | recommended minimum age (0 = no restriction) |
| `users_rated` | number of ratings |
| `avg_rating` | average user rating (1-10) |
| `bayes_rating` | Bayesian average (NaN = not enough ratings) |
| `complexity_weight` | complexity 1 (easy) .. 5 (heavy) |
| `board_game_rank` | overall BGG rank (NaN = unranked) |
| `categories` | semicolon-separated categories |
| `mechanics` | semicolon-separated mechanics |
| `designers` | semicolon-separated designers |
| `description` | free-text description (unstructured, great for NLP) |
| `description_length` | number of characters in description |
| `decade` | release decade, e.g. 2010 (0 = unknown) |
| `complexity_group` | light / medium / heavy / unknown |
| `playtime_group` | short (≤30 min) / medium (31-90) / long (>90) / unknown |
| `is_solo` | 1 = playable solo |
| `rank_tier` | top1000 / top5000 / ranked / unranked |
| `n_categories` / `n_mechanics` | number of categories / mechanics |

## Data cleaning highlights

The raw export contains classic "dirty data" problems that the cleaning
pipeline fixes:

- **Fake zeros** — BGG uses `0` as "no data" for year, playtime, ratings,
  complexity and users_rated (e.g. 402 games have `playing_time=0`, 197 have
  `avg_rating=0.0`). These are converted to `NaN`.
- **Ancient games** — e.g. Go is stored with year **-2200** (2200 BC); treated
  as unknown year.
- **`"Not Ranked"`** — literal string for unranked games; normalized to `NaN`.
- **`min_age=0`** is *kept* — BGG uses it to mean "no age restriction".

## Security note

The BGG API token is **never** stored in this repo. The scripts read it from the enviroment or ask for it interactively, and `.gitignore` excludes any token-like files and the `raw/`cache.

