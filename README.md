#  BGG Borad Game Data Pipeline

Board game dataset downloaded from the **official BoardGameGeek XML API2**, cleaned in to a tiday CSV for a University of Helsinki *Data Science* mini project.

- **Games:** 2,077 board games × 18 raw fields (26 after cleaning)
- **Source:** [boardgamegeek.com/xmlapi2](https://boardgamegeek.com/xmlapi2) - `thing`, `search`, `hot` endpoints.
- **Terms of use:** https://boardgamegeek.com/wiki/page/XML_API_Terms_of_Use

## Repository structure
| Folder | Content |
|---|---|
| `data/` | raw & cleaned datasets |
| `scripts/` | fetch + clean pipelines |
| `notebooks/` | EDA & modeling notebooks (work in progress) |
| `webapp/` | interactive visualization web app (work in progress) |
| `blog/` | blog post materials (work in progress) |
| `presentation/` | spotlight presentation slides (work in progress) |
| `report/` | technical report PDF (work in progress) |

## Files

| File | What it is |
|---|---|
| `scripts/fetch_bgg.py` | hot list + 50 keyword searches → details for ~4,000 games (expansions filtered) |
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

***Windows (manual, Anoconda Prompt):**

**Mac / Linux:**

## Columns (data/cleaned_games.csv)

## Data cleaning highlights

## Security note

Your BGG API token is **never** stored in this repo. The scripts read it from the enviroment or ask for it interactively, and `.gitignore` excludes any token-like files and the `raw/`cache.

