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

```bash
# 1. download (needs a BBG API token from https://boardgamegeek.com/applications). Our application was submitted on 11 September 2026 and approved on 12 September 2026.
export BGG_API_TOKEN="your-token"
python3 scripts/fetch_bgg.py --out data

# 2. clean (run inside data/ so games.csv is found)
cd data
python3 ../scripts/clean_bgg_data.py        # reads games.csv -> writes cleaned_games.csv

## Columns (data/cleaned_games.csv)

## Data cleaning highlights

