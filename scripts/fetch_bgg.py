"""
fetch_bgg.py - Download a BoardGameGeek dataset via the offical XML API2.

Why this script exists
----------------------
Since fall 2025 BGG requires a Bearer token (register your app at
https://boardgamegeek.com/applications, then generate a token).

This script:
  1. GET /xmlapi2/hot?type=boardgame        -> current hot games (ids)
  2. GET /xmlapi2/search?query=...          -> ids from a list of search terms
  3. GET /xmlapi2/thing?id=..&stats=1       -> full details, 20 ids per batch
and finally saves all games into a single games.csv file.

Rate limiting: BGG limits the XML API to ~100 requests/min. This script stays
well below that (3.5s between requests) and backs off on HTTP 429 / 5xx.
Raw responses are cached in <out>/raw/ so re-runs do not re-download.

Usage
-----
    Windows (run.bat)

    Windows (Anacond Prompt):
        set BGG_API_TOKEN="your token"
        python scripts\fetch_bgg.py --out data

    Mac / Linux:
        export BGG_API_TOKEN="your token"
        python3 fetch_bgg.py --out data

Requires only the Python standard library (urlib + xml.etree)
"""

import argparse
import csv
import html
import os
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BASE = "https://boardgamegeek.com/xmlapi2"
UA = "DS-DataScienceProject/1.0 (student mini-project)"

DEFAULT_SEARCH_TERMS = [
    # strategy / euro
    "Catan", "Carcassonne", "Ticket to Ride", "Pandemic", "Gloomhaven",
    "Terraforming Mars", "Wingspan", "Azul", "Splendor", "7 Wonders",
    "Dominion", "Agricola", "Puerto Rico", "Power Grid", "Scythe", "Root",
    "Everdell", "Spirit Island", "Brass", "Great Western Trail",
    "Castles of Burgundy", "Viticulture", "Ark Nova", "Dune Imperium",
    "Twilight Imperium", "War of the Ring", "Gaia Project",
    "A Feast for Odin", "El Grande", "Food Chain Magnate",
    # abstract / family / party
    "Chess", "Go", "Hive", "Patchwork", "Santorini", "Qwirkle",
    "Just One", "Wavelength", "Codenames", "Dixit", "Hanabi",
    "Monopoly", "Uno", "Exploding Kittens", "Scrabble", "Risk", "Jenga",
    # thematic / cooperative
    "Mysterium", "Marvel Champions", "Arkham Horror", "Descent",
    "Mansions of Madness", "Nemesis", "Dead of Winter",
]

def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def http_get(path: str, params: dict, token: str, raw_dir: pathlib.Path) -> bytes:
    """Get an XML API2 endpoint with Bearer auth, catching raw response."""
    params["_"] = str(int(time.time()))  # unique cache key per cell
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    # cache key without the timestamp param
    key_params = {k: v for k, v in params.items() if k != "_"}
    cache = raw_dir / f"{path.strip('/').replace('/', '_')}_{urllib.parse.urlencode(sorted(key_params.items()))[:200]}.xml"
    
    if cache.exists() and cache.stat().st_size > 0:
        log(f"  cache hit: {cache.name}")
        return cache.read_bytes()

    req =urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "User-Agent": UA,
        "Accept": "application/xml, text/xml, */*",
    })
    for attempt in range(8):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            if b"<items" in data or b"<item" in data or path == "/hot":
                cache.write_bytes(data)
                return data
            log(f"  unexpected payload ({len(data)} bytes), retrying ({attempt+1})")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 60
                log(f"  429 rate limited -> sleeping {wait}s")
                time.sleep(wait)
            elif e.code in (500, 502, 503, 504):
                wait = 30
                log(f"  {e.code} server error -> sleeping {wait}s")
                time.sleep(wait)
            elif e.code in (401, 403):
                log(f"  {e.code} auth error - token invalid/not approved? aborting")
                raise
            else:
                log(f"  HTTP {e.code} -> sleeping 10s")
                time.sleep(10)
        except Exception as e:  # connection error
            log(f"  network error {e!r} -> sleeping 15s")
            time.sleep(15)
    raise RuntimeError(f"giving up on {url}")


def fetch_hot(token: str, raw_dir: pathlib.Path) -> list[int]:
    log("Step 1/4: hot games")
    data = http_get("/hot", {"type": "boardgame"}, token, raw_dir)
    root = ET.fromstring(data)
    ids = [int(it.get("id")) for it in root.findall("item")]
    log(f"  {len(ids)} hot game ids")
    return ids


def fetch_search_ids(token: str, raw_dir: pathlib.Path, terms=None) -> list[int]:
    log("Step 2/4: search by keywords")
    terms = terms or DEFAULT_SEARCH_TERMS
    ids: list[int] = []
    for t in terms:
        data = http_get("/search", {"query": t, "type": "boardgame"}, token, raw_dir)
        try:
            root = ET.fromstring(data)
        except ET.ParseError:
            log(f"  parse error for '{t}', skipping")
            continue
        found = [int(it.get("id")) for it in root.findall("item")]
        log(f"  '{t}': {len(found)} hits")
        ids.extend(found)
        time.sleep(3.5)
    uniq = list(dict.fromkeys(ids))
    log(f"  total unique ids from search: {len(uniq)}")
    return uniq


def fetch_things(ids: list[int], token: str, raw_dir: pathlib.Path,
                 sleep: float = 3.5) -> list[ET.Element]:
    log(f"Step 3/4: fetch details for {len(ids)} games (20/batch)")
    items: list[ET.Element] = []
    for i in range(0, len(ids), 20):
        batch = ids[i:i + 20]
        data = http_get("/thing", {"id": ",".join(map(str, batch)), "stats": "1"},
                        token, raw_dir)
        try:
            root = ET.fromstring(data)
        except ET.ParseError as e:
            log(f"  parse error at batch {i // 20}: {e}")
            continue
        batch_items = root.findall("item")
        items.extend(batch_items)
        log(f"  batch {i // 20 + 1}/{(len(ids) + 19) // 20}: +{len(batch_items)} items "
            f"(total {len(items)})")
        time.sleep(sleep)
    return items


TAG_RE = re.compile(r"<[^>]+>")


def clean_desc(raw: str | None) -> str:
    if not raw:
        return ""
    txt = TAG_RE.sub(" ", raw)
    return re.sub(r"\s+", " ", html.unescape(txt)).strip()


def parse_thing(item: ET.Element) -> dict:
    def val(el, attr="value", default=""):
        return el.get(attr, default) if el is not None else default

    name = ""
    for n in item.findall("name"):
        if n.get("type")  == "primary":
            name = n.get("value", "")
            break
    cats = [l.get("value", "") for l in item.findall("link")
            if l.get("type") == "boardgamecategory"]
    mechs = [l.get("value", "") for l in item.findall("link")
            if l.get("type") == "boardgamemechanic"]
    des = [l.get("value", "") for l in item.findall("link")
            if l.get("type") == "boardgamedesigner"]

    rank = ""
    stats = item.find("statistics")
    if stats is not None:
        ratings = stats.find("ratings")
        if ratings is not None:
            for r in ratings.findall("ranks/rank"):
                if r.get("type") == "subtype" and r.get("name") == "boardgame":
                    rank = r.get("value", "")
                    if rank == "Not Ranked":  # BGG literal for unranked games
                        rank = ""
                    break

    return {
        "game_id": item.get("id", ""),
        "name":name,
        "year_published": val(item.find("yearpublished")),
        "min_players": val(item.find("minplayers")),
        "max_players": val(item.find("maxplayers")),
        "playing_time_min": val(item.find("playingtime")),
        "min_playtime": val(item.find("minplaytime")),
        "max_playtime": val(item.find("maxplaytime")),
        "min_age": val(item.find("minage")),
        "users_rated": val(stats.find("ratings/usersrated")) if stats is not None else "", 
        "avg_rating": val(stats.find("ratings/average")) if stats is not None else "", 
        "bayes_rating": val(stats.find("ratings/bayesaverage")) if stats is not None else "", 
        "complexity_weight": val(stats.find("ratings/averageweight")) if stats is not None else "", 
        "board_game_rank": rank,
        "categories": ";".join(cats),
        "mechanics": ";".join(mechs),
        "designers": ";".join(des),
        "description": clean_desc(item.findtext("description")),
    }


COLUMNS = ["game_id", "name", "year_published", "min_players", "max_players",
           "playing_time_min", "min_playtime", "max_playtime", "min_age",
           "users_rated", "avg_rating", "bayes_rating", "complexity_weight",
           "board_game_rank", "categories", "mechanics", "designers", "description"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Download BGG board game data")
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent),
                    help="output directory (default: script folder)")
    ap.add_argument("--token", default=os.environ.get("BGG_API_TOKEN", ""),
                    help="BGG API token (or set env BGG_API_TOKEN)")
    ap.add_argument("--sleep", type=float, default=3.5,
                    help="seconds between requests (default 3.5)")
    args = ap.parse_args()

    if not args.token:
        print("ERROR: no token. Set BGG_API_TOKEN env var or pass --token")
        return 1

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    raw_dir = out / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    hot_ids = fetch_hot(args.token, raw_dir)
    search_ids = fetch_search_ids(args.token, raw_dir, DEFAULT_SEARCH_TERMS)
    all_ids = list(dict.fromkeys(hot_ids + search_ids))
    log(f"  combined unique ids: {len(all_ids)}")

    items = fetch_things(all_ids, args.token, raw_dir, sleep=args.sleep)

    rows = [parse_thing(it) for it in items if it.get("type") == "boardgame"]
    log(f"Step 4/4: writing {len(rows)} games to games.csv")

    csv_path = out / "games.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    log("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())