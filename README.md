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


## Quick start

### Windows - run.bat

1. Put `run.bat` in this folder (repo root)
2. Double-click it
3. When asked `Enter your BAG API token:`, paste your token
   (get one at https://boardgamegeek.com/applications)
4. Wait ~20 minutes → check `data/game.csv`

### Mac / Linux

```bash
export BGG_API_TOKEN="your-token"
python3 scripts/fetch_bgg.py --out data
```

## Columns (data/cleaned_games.csv)

## Data cleaning highlights

## Security note

Your BGG API token is **never** stored in this repo. The scripts read it from the enviroment or ask for it interactively, and 

