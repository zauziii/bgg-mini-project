"""
part1_find.py - Aoxue Li's part: data core + Home + "Find a game"
==================================================================
Task checklist:
  1. Run the app end-to-end; Home and Find must render correctly.
  2. Verify the fit functions and weights match
     scripts/ml_part3_recommender.py EXACTLY. Inconsistency found in complexity_fit
     and fixed.
  3. Check Home page metrics agree with the real data (2,077 games, etc).
  4. Harden edge cases: missing playtime / complexity must not break scoring.

This file is imported by webapp/app.py:
    from part1_find import render_home, render_find
"""

import numpy as np
import pandas as pd
import streamlit as st
import pathlib
from html import escape

_ASSETS = pathlib.Path(__file__).resolve().parent / "assets"


# ----------------------------------------------------------------------
# recommendation logic (EXACTLY the same formula as ml_part3_recommender.py)
# ----------------------------------------------------------------------
def players_fit(lo: float, hi: float, n: int) -> float:
    """1.0 = group size inside the range, 0.5 = one player off, else 0."""
    if lo <= n <= hi:
        return 1.0
    if n == lo - 1 or n == hi + 1:
        return 0.5
    return 0.0


def playtime_fit(game_minutes: float, pref_minutes: float) -> float:
    """1.0 at exact match, smoothly decays for longer/shorter games."""
    if pd.isna(game_minutes) or game_minutes <= 0:
        return 0.5
    diff = abs(np.log(game_minutes + 1) - np.log(pref_minutes + 1))
    return float(np.exp(-diff / 2.0))


def complexity_fit(game_weight: float, pref: float) -> float:
    """1.0 at exact complexity, decays with distance (1 = light, 5 = heavy)."""
    if pd.isna(game_weight):
        return 0.5
    return float(np.exp(-abs(game_weight - pref) / 2.0))


def recommend(games: pd.DataFrame, n_players: int, pref_minutes: int,
              pref_complexity: float, min_ratings: int = 100,
              top_n: int = 10, time_mode: str = "pref",
              complexity_max=None) -> pd.DataFrame:
    """Score every game, return the top_n that fit the player.

    time_mode:
      "pref" - playtime is a PREFERENCE: games close to the target rank higher.
      "max"  - playtime is a HARD LIMIT: games longer than the target are
               filtered out before scoring (missing playtime -> skipped).
    complexity_max (optional): a HARD complexity ceiling. When given, games
      heavier than this are excluded before scoring (used by the scene
      presets on the Home page). When None, complexity stays a preference.
    """
    # The UI promises that player count is required. Apply it before the
    # top-N slice so an incompatible game cannot displace a valid match.
    pool = games[(games["users_rated"] >= min_ratings)
                 & games["avg_rating"].notna()
                 & (games["min_players"] <= n_players)
                 & (games["max_players"] >= n_players)].copy()
    if time_mode == "max":
        pool = pool[pool["playing_time_min"].notna()
                    & (pool["playing_time_min"] <= pref_minutes)]
    if complexity_max is not None:
        pool = pool[pool["complexity_weight"].notna()
                    & (pool["complexity_weight"] <= complexity_max)]
    cols = ["game_id", "name", "top_category", "avg_rating",
            "complexity_weight", "playing_time_min", "min_players",
            "max_players", "users_rated", "score", "board_game_rank",
            "year_published"]
    if pool.empty:
        pool["score"] = pd.Series(dtype=float)
        return pool[cols]
    pool["players_fit"] = pool.apply(
        lambda r: players_fit(r["min_players"], r["max_players"], n_players),
        axis=1)
    pool["playtime_fit"] = pool["playing_time_min"].apply(
        playtime_fit, pref_minutes=pref_minutes)
    pool["complexity_fit"] = pool["complexity_weight"].apply(
        complexity_fit, pref=pref_complexity)
    # final score: how well it fits + its real quality (avg_rating)
    pool["score"] = (0.35 * pool["players_fit"]
                     + 0.20 * pool["playtime_fit"]
                     + 0.20 * pool["complexity_fit"]
                     + 0.25 * pool["avg_rating"] / 10.0)
    return pool.sort_values("score", ascending=False).head(top_n)[cols]


def reason_bits(g: pd.Series, n: int, pref_min: int,
                pref_comp: float, time_mode: str,
                comp_mode: str = "pref"):
    """Three short, data-backed matching reasons (round 2 format).

    Returns a list of (label, text) rows rendered as three lines:
        Players: Fits 4
        Playtime: 15 min longer   |  On target  |  5 min shorter
        Complexity: On target     |  0.1 above preference
    Only real differences are stated — never a fake "perfect match".
    When a rule is Maximum, the wording states the limit honestly.
    """
    rows = []

    # players: one short line about the group size
    if g["min_players"] <= n <= g["max_players"]:
        rows.append(("Players", f"Fits {n} player{'s' if n > 1 else ''}"))
    else:
        rows.append(("Players", "Outside this game's player range"))

    # playtime: honest difference vs the preference / limit
    if pd.notna(g["playing_time_min"]) and g["playing_time_min"] > 0:
        t = float(g["playing_time_min"])
        if time_mode == "max":
            rows.append(("Playtime", f"{t:.0f} min · within your {pref_min} min limit"))
        else:
            diff = t - pref_min
            if abs(diff) < 1:
                rows.append(("Playtime", "On target"))
            elif diff > 0:
                rows.append(("Playtime", f"{diff:.0f} min longer"))
            else:
                rows.append(("Playtime", f"{-diff:.0f} min shorter"))
    else:
        rows.append(("Playtime", "n/a"))

    # complexity: honest difference vs the preference / hard cap
    if pd.notna(g["complexity_weight"]):
        c = float(g["complexity_weight"])
        dc = c - pref_comp
        if comp_mode == "max":
            rows.append(("Complexity",
                         f"{c:.1f}/5 · within your {pref_comp:.1f}/5 limit"))
        elif abs(dc) < 0.05:
            rows.append(("Complexity", "On target"))
        elif dc > 0:
            rows.append(("Complexity", f"{dc:.1f} above preference"))
        else:
            rows.append(("Complexity", f"{-dc:.1f} below preference"))
    else:
        rows.append(("Complexity", "n/a"))
    return rows


def _reason_html(g: pd.Series, n: int, pref_min: int,
                 pref_comp: float, time_mode: str,
                 comp_mode: str = "pref") -> str:
    """Render the three reason rows as HTML lines."""
    parts = []
    for label, text in reason_bits(g, n, pref_min, pref_comp, time_mode,
                                   comp_mode):
        parts.append(
            f'<div class="reason-line"><span class="reason-label">{label}:'
            f'</span> {text}</div>')
    return "".join(parts)


def _players(g: pd.Series) -> str:
    lo, hi = g["min_players"], g["max_players"]
    if pd.isna(lo) or pd.isna(hi):
        return "n/a"
    return f"{int(lo)}–{int(hi)}"


def _bgg_link(g: pd.Series) -> str:
    """Link to the game's page on BoardGameGeek."""
    gid = str(int(g["game_id"]))
    return f"https://boardgamegeek.com/boardgame/{gid}"


def switch_to(path: str) -> None:
    """Switch to another page.

    The app uses st.navigation with function-based st.Page objects, so
    st.switch_page must receive a *page object* (a url string would only
    work for file-based pages and raises StreamlitAPIException). app.py
    registers the page objects in st.session_state["PAGES"] keyed by
    url_path; we look it up there. If it is missing, we show a friendly
    error instead of crashing the page.
    """
    pages = st.session_state.get("PAGES")
    if pages and path in pages:
        st.switch_page(pages[path])
        return
    st.error("Navigation not ready (missing page '%s'). "
             "Please restart the app." % path)


# ----------------------------------------------------------------------
# scene presets ("Tonight's plan") - shared with the Find page
# ----------------------------------------------------------------------
PRESETS = {
    "quick": dict(label="Quick & easy", n=4, t=45, c=2.5,
                  blurb="4 players · up to 45 min"),
    "time":  dict(label="Take your time", n=4, t=120, c=2.5,
                  blurb="4 players · up to 120 min"),
    "five":  dict(label="Five at the table", n=5, t=90, c=2.5,
                  blurb="5 players · up to 90 min"),
}


def preset_match(n_players: int, pref_minutes: int,
                 pref_complexity: float, mode: str,
                 comp_mode: str = "pref") -> str:
    """Value-driven preset detection.

    Returns the preset key whose settings EXACTLY match the current form
    state, else None. Because it compares the live form values, changing
    any slider automatically clears the preset highlight (no stale state).
    A preset only matches when BOTH time and complexity rules are in
    Maximum mode and the values agree.
    """
    if mode != "max" or comp_mode != "max":
        return None
    for key, p in PRESETS.items():
        if (p["n"] == n_players and p["t"] == pref_minutes
                and abs(p["c"] - pref_complexity) < 1e-9):
            return key
    return None


def _active_preset_key() -> str:
    """Which scene (if any) matches the CURRENT recommendation state."""
    n = st.session_state.get("find_n", 4)
    t = st.session_state.get("find_time", 45)
    c = st.session_state.get("find_comp", 2.5)
    m = "max" if st.session_state.get("find_mode") == "Maximum time" else "pref"
    cm = "max" if (st.session_state.get("find_comp_mode")
                   == "Maximum complexity") else "pref"
    return preset_match(n, t, c, m, cm) or ""


def apply_preset(key: str) -> None:
    """Apply a scene preset to the Find form and go to the Find page.

    Every preset promises a MAXIMUM time and a MAXIMUM complexity, so
    both rules are switched to Maximum mode before navigating.
    """
    p = PRESETS[key]
    st.session_state["find_n"] = p["n"]
    st.session_state["find_time"] = p["t"]
    st.session_state["find_comp"] = p["c"]
    st.session_state["find_mode"] = "Maximum time"
    st.session_state["find_comp_mode"] = "Maximum complexity"
    # drop widget keys so the Find page widgets rebuild from the logical
    # state (Streamlit would otherwise serve stale cached widget values)
    for _wk in ("find_n_w", "find_time_w", "find_comp_w",
                "find_mode_w", "find_comp_mode_w"):
        st.session_state.pop(_wk, None)
    switch_to("find")


# ----------------------------------------------------------------------
# category art: small deterministic SVG motifs (no fake covers)
# ----------------------------------------------------------------------
_CAT_COLORS = {
    "Card Game": "#675298", "Dice": "#675298",
    "Abstract Strategy": "#8A6427", "Word Game": "#8A6427",
    "Economic": "#7A5C2E", "City Building": "#7A5C2E",
    "Animals": "#466449", "Children's Game": "#466449",
    "Action / Dexterity": "#A64D35", "Adventure": "#A64D35",
    "Negotiation": "#7A5C2E", "Medieval": "#7A5C2E",
    "Civilization": "#8A6427", "Fantasy": "#675298",
    "Deduction": "#466449", "Trains": "#A64D35",
    "Ancient": "#8A6427", "Movies / TV / Radio theme": "#675298",
    "Medical": "#A94F35", "Environmental": "#466449",
    "Party Game": "#675298", "Puzzle": "#8A6427",
    "Wargame": "#7A5C2E", "Fighting": "#A64D35",
    "Mythology": "#675298", "Pirates": "#A64D35",
    "Nautical": "#466449", "Space Exploration": "#675298",
    "Print & Play": "#7D7D75", "Miniatures": "#7A5C2E",
    "RPG": "#675298", "Horror": "#8C4A36",
    "Exploration": "#466449", "Travel": "#466449",
    "Territory Building": "#7A5C2E", "Educational": "#466449",
}
_DEFAULT_ART_COLOR = "#675298"


def _svg_motif(category: str, color: str) -> str:
    """Central motif paths for a 64x64 viewBox, all drawn in `color`."""
    if category == "Card Game":
        return ('<rect x="15" y="14" width="22" height="30" rx="3" '
                'fill="#ffffff" stroke="{c}" stroke-width="2"/>'
                '<rect x="28" y="20" width="22" height="30" rx="3" '
                'fill="#ffffff" stroke="{c}" stroke-width="2"/>'
                '<path d="M20 24 L24 20 L28 24 L24 28 Z" fill="{c}"/>').format(c=color)
    if category == "Abstract Strategy":
        return ('<circle cx="27" cy="25" r="7" fill="none" stroke="{c}" '
                'stroke-width="2.5"/>'
                '<path d="M32 42 L41 29 L44 38 Z" fill="{c}"/>'
                '<rect x="22" y="34" width="7" height="7" rx="1" fill="{c}"/>'
                ).format(c=color)
    if category in ("Economic", "City Building"):
        return ('<circle cx="24" cy="28" r="9" fill="#ffffff" stroke="{c}" '
                'stroke-width="2.5"/>'
                '<circle cx="40" cy="34" r="9" fill="#ffffff" stroke="{c}" '
                'stroke-width="2.5"/>'
                '<path d="M22 33 h4 M23 37 h4 M38 31 h4" stroke="{c}" '
                'stroke-width="2"/>').format(c=color)
    if category == "Animals":
        return ('<ellipse cx="26" cy="34" rx="9" ry="7" fill="#ffffff" '
                'stroke="{c}" stroke-width="2.5"/>'
                '<ellipse cx="36" cy="25" rx="4" ry="5.5" fill="{c}"/>'
                '<ellipse cx="44" cy="30" rx="4" ry="5.5" fill="{c}"/>'
                '<ellipse cx="34" cy="40" rx="4" ry="5.5" fill="{c}"/>'
                ).format(c=color)
    if category == "Children's Game":
        return ('<rect x="18" y="26" width="12" height="12" rx="2" fill="{c}"/>'
                '<rect x="30" y="26" width="12" height="12" rx="2" '
                'fill="#ffffff" stroke="{c}" stroke-width="2"/>'
                '<rect x="24" y="14" width="12" height="12" rx="2" '
                'fill="#ffffff" stroke="{c}" stroke-width="2"/>'
                ).format(c=color)
    if category == "Action / Dexterity":
        return ('<circle cx="32" cy="30" r="13" fill="none" stroke="{c}" '
                'stroke-width="2.5"/>'
                '<circle cx="32" cy="30" r="8" fill="none" stroke="{c}" '
                'stroke-width="2"/>'
                '<circle cx="32" cy="30" r="3.5" fill="{c}"/>'
                ).format(c=color)
    if category == "Dice":
        return ('<rect x="18" y="16" width="28" height="28" rx="5" '
                'fill="#ffffff" stroke="{c}" stroke-width="2.5"/>'
                '<circle cx="26" cy="24" r="2.2" fill="{c}"/>'
                '<circle cx="38" cy="24" r="2.2" fill="{c}"/>'
                '<circle cx="32" cy="30" r="2.2" fill="{c}"/>'
                '<circle cx="26" cy="36" r="2.2" fill="{c}"/>'
                '<circle cx="38" cy="36" r="2.2" fill="{c}"/>'
                ).format(c=color)
    if category == "Adventure":
        return ('<path d="M20 16 L20 46" stroke="{c}" stroke-width="3"/>'
                '<path d="M20 18 L42 24 L20 32 Z" fill="{c}"/>'
                '<path d="M36 40 L48 46 M40 44 L50 38" stroke="{c}" '
                'stroke-width="3"/>').format(c=color)
    if category == "Word Game":
        return ('<rect x="16" y="18" width="16" height="20" rx="3" '
                'fill="{c}"/>'
                '<rect x="34" y="26" width="14" height="12" rx="3" '
                'fill="#ffffff" stroke="{c}" stroke-width="2.5"/>'
                ).format(c=color)
    if category in ("Negotiation", "Economic"):
        # trade / resources: two hands + a coin, or resource cubes
        return ('<path d="M20 38 Q26 30 34 34 Q40 30 46 36" fill="none" '
                'stroke="{c}" stroke-width="3" stroke-linecap="round"/>'
                '<circle cx="32" cy="20" r="5.5" fill="#ffffff" stroke="{c}" '
                'stroke-width="2.5"/>'
                '<path d="M32 17.5 v5 M29.7 20 h4.6" stroke="{c}" '
                'stroke-width="1.8"/>'
                '<rect x="26" y="44" width="7" height="6" rx="1.5" fill="{c}"/>'
                '<rect x="35" y="44" width="7" height="6" rx="1.5" '
                'fill="#ffffff" stroke="{c}" stroke-width="1.8"/>'
                ).format(c=color)
    if category in ("Medieval", "City Building", "Territory Building"):
        # castle: two towers + keep + gate
        return ('<rect x="18" y="30" width="12" height="14" fill="{c}"/>'
                '<path d="M18 32 L24 24 L30 32 Z" fill="{c}"/>'
                '<rect x="34" y="26" width="14" height="18" fill="{c}"/>'
                '<path d="M34 28 L41 18 L48 28 Z" fill="{c}"/>'
                '<rect x="38" y="38" width="6" height="6" rx="1" '
                'fill="#ffffff"/>'
                '<rect x="22" y="38" width="4" height="6" fill="#ffffff"/>'
                ).format(c=color)
    if category == "Civilization":
        # temple column + lintel
        return ('<rect x="26" y="20" width="6" height="24" fill="{c}"/>'
                '<rect x="36" y="24" width="6" height="20" fill="{c}"/>'
                '<rect x="22" y="16" width="24" height="6" rx="1.5" fill="{c}"/>'
                '<circle cx="47" cy="30" r="6" fill="#ffffff" stroke="{c}" '
                'stroke-width="2.5"/>'
                ).format(c=color)
    if category == "Fantasy":
        # sword + shield
        return ('<path d="M18 18 L40 40 M22 16 L46 40 M18 18 L16 22 Z" '
                'fill="none" stroke="{c}" stroke-width="2.5" '
                'stroke-linejoin="round"/>'
                '<path d="M42 24 a11 11 0 0 1 -6 11 l-2 -4 Z" fill="{c}"/>'
                ).format(c=color)
    if category == "Deduction":
        # magnifying glass over a clue
        return ('<circle cx="30" cy="30" r="11" fill="none" stroke="{c}" '
                'stroke-width="3"/>'
                '<path d="M38 38 L48 48" stroke="{c}" stroke-width="3" '
                'stroke-linecap="round"/>'
                '<circle cx="30" cy="30" r="3" fill="{c}"/>'
                ).format(c=color)
    if category == "Trains":
        return ('<path d="M18 30 h28 M22 22 h12 l6 8" fill="none" stroke="{c}" '
                'stroke-width="2.5" stroke-linecap="round"/>'
                '<rect x="20" y="34" width="24" height="10" rx="2" fill="{c}"/>'
                '<circle cx="25" cy="46" r="3" fill="{c}"/>'
                '<circle cx="39" cy="46" r="3" fill="{c}"/>'
                ).format(c=color)
    if category == "Medical":
        # cross in a rounded square (medical kit)
        return ('<rect x="18" y="18" width="28" height="28" rx="6" '
                'fill="#ffffff" stroke="{c}" stroke-width="2.5"/>'
                '<rect x="27" y="23" width="10" height="18" rx="2" fill="{c}"/>'
                '<rect x="23" y="27" width="18" height="10" rx="2" fill="{c}"/>'
                ).format(c=color)
    if category == "Environmental":
        # leaf + stem
        return ('<path d="M32 16 C20 24 18 40 32 48 C46 40 44 24 32 16 Z" '
                'fill="#ffffff" stroke="{c}" stroke-width="2.5"/>'
                '<path d="M32 30 L32 48 M26 44 L32 48 L38 44" fill="none" '
                'stroke="{c}" stroke-width="2.2" stroke-linecap="round"/>'
                '<path d="M32 22 L32 34 M28 27 L36 27" stroke="{c}" '
                'stroke-width="1.6"/>'
                ).format(c=color)
    if category in ("Ancient", "Mythology"):
        # broken column / pediment
        return ('<rect x="20" y="20" width="6" height="24" fill="{c}"/>'
                '<rect x="32" y="24" width="6" height="20" fill="{c}"/>'
                '<path d="M18 16 L32 10 L46 16 Z" fill="{c}"/>'
                '<circle cx="47" cy="34" r="6" fill="#ffffff" stroke="{c}" '
                'stroke-width="2.5"/>'
                ).format(c=color)
    if category in ("Party Game", "Word Game"):
        # speech bubble + confetti
        return ('<rect x="16" y="18" width="22" height="18" rx="5" '
                'fill="#ffffff" stroke="{c}" stroke-width="2.5"/>'
                '<path d="M22 36 L20 44 L28 38 Z" fill="{c}"/>'
                '<path d="M44 18 l2 4 4 1 -4 1 -2 4 -2 -4 -4 -1 4 -1 Z" '
                'fill="{c}"/>'
                '<path d="M48 32 l1.5 3 3 1 -3 1 -1.5 3 -1.5 -3 -3 -1 3 -1 Z" '
                'fill="{c}" opacity="0.7"/>'
                ).format(c=color)
    if category == "Puzzle":
        # two puzzle pieces
        return ('<path d="M18 18 h12 a5 5 0 0 1 0 8 a5 5 0 0 1 0 8 h-12 Z" '
                'fill="#ffffff" stroke="{c}" stroke-width="2.5"/>'
                '<path d="M34 22 h12 a5 5 0 0 1 0 8 a5 5 0 0 1 0 8 h-12 Z" '
                'fill="{c}"/>'
                ).format(c=color)
    if category in ("Wargame", "Fighting"):
        # crossed swords + banner
        return ('<path d="M24 20 L38 34 M22 22 L20 24 Z" fill="none" '
                'stroke="{c}" stroke-width="2.6" stroke-linecap="round"/>'
                '<path d="M40 20 L26 34 M42 22 L44 24 Z" fill="none" '
                'stroke="{c}" stroke-width="2.6" stroke-linecap="round"/>'
                '<path d="M31 14 L33 22 L31 28 L29 22 Z" fill="{c}"/>'
                ).format(c=color)
    if category == "Miniatures":
        # tiny figure on a base
        return ('<circle cx="32" cy="20" r="5" fill="{c}"/>'
                '<path d="M25 30 q0 -12 7 -12 q7 0 7 12 Z" fill="{c}"/>'
                '<rect x="22" y="42" width="20" height="5" rx="2" fill="{c}"/>'
                ).format(c=color)
    if category in ("Nautical", "Pirates", "Travel", "Exploration"):
        # compass rose
        return ('<circle cx="32" cy="30" r="14" fill="none" stroke="{c}" '
                'stroke-width="2.5"/>'
                '<path d="M32 18 L35 29 L46 32 L35 35 L32 46 L29 35 L18 32 '
                'L29 29 Z" fill="{c}"/>'
                ).format(c=color)
    if category == "Space Exploration":
        # rocket
        return ('<path d="M32 12 L38 30 L32 42 L26 30 Z" fill="{c}"/>'
                '<circle cx="32" cy="26" r="4" fill="#ffffff"/>'
                '<rect x="26" y="36" width="12" height="4" rx="2" fill="{c}"/>'
                '<path d="M28 44 L26 50 M36 44 L38 50 M32 44 L32 50" '
                'stroke="{c}" stroke-width="2" stroke-linecap="round"/>'
                ).format(c=color)
    if category in ("Horror", "RPG"):
        # die + book
        return ('<rect x="16" y="20" width="14" height="20" rx="2" '
                'fill="#ffffff" stroke="{c}" stroke-width="2.5"/>'
                '<path d="M34 20 l12 3 v18 l-12 -3 Z" fill="{c}"/>'
                '<circle cx="23" cy="30" r="2.5" fill="{c}"/>'
                '<path d="M40 28 l4 1 M40 34 l4 1" stroke="#ffffff" '
                'stroke-width="1.6"/>'
                ).format(c=color)
    if category == "Educational":
        # open book + lightbulb
        return ('<path d="M18 24 h12 v16 h-12 Z M30 24 h12 v16 h-12 Z" '
                'fill="#ffffff" stroke="{c}" stroke-width="2.5"/>'
                '<circle cx="48" cy="18" r="5" fill="{c}"/>'
                '<path d="M48 23 v5 M48 30 v2" stroke="{c}" '
                'stroke-width="2" stroke-linecap="round"/>'
                ).format(c=color)
    # default motif: a friendly star
    return ('<path d="M32 14 L36.2 25.8 L48 26.6 L39 34.2 L41.8 45.8 '
            'L32 39.6 L22.2 45.8 L25 34.2 L16 26.6 L27.8 25.8 Z" '
            'fill="{c}"/>').format(c=color)


def _cat_art(category: str, size: int = 56) -> str:
    """Small deterministic category motif inside a soft neutral tile.

    Used instead of real covers (our dataset has no cover URLs). The motif
    is abstract on purpose, so it can never be mistaken for a real box
    cover; the real game name is always shown next to it.
    """
    color = _CAT_COLORS.get(category, _DEFAULT_ART_COLOR)
    motif = _svg_motif(category, color)
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 64 64" '
        f'xmlns="http://www.w3.org/2000/svg" class="cat-art">'
        f'<rect x="1" y="1" width="62" height="62" rx="14" '
        f'fill="{color}" opacity="0.10"/>'
        f'<rect x="1" y="1" width="62" height="62" rx="14" '
        f'fill="none" stroke="{color}" stroke-opacity="0.35" '
        f'stroke-width="1.5"/>{motif}</svg>')


# ----------------------------------------------------------------------
# PAGE 1 - HOME
# ----------------------------------------------------------------------
_HERO_ART = """<svg viewBox="40 45 250 200" xmlns="http://www.w3.org/2000/svg" class="hero-art-svg">
  <defs>
    <filter id="soft" x="-40%" y="-40%" width="180%" height="180%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#293027" flood-opacity="0.18"/>
    </filter>
  </defs>
  <!-- back card, tilted left -->
  <g transform="rotate(-10 150 150)" filter="url(#soft)">
    <rect x="108" y="88" width="84" height="118" rx="9" fill="#FFFCF6" stroke="#DEDBCC" stroke-width="2"/>
    <rect x="118" y="98" width="64" height="98" rx="5" fill="none" stroke="#675298" stroke-opacity="0.35" stroke-width="2"/>
    <path d="M150 118 l14 14 -14 14 -14 -14 Z" fill="#675298" opacity="0.55"/>
  </g>
  <!-- purple die, rolling -->
  <g transform="rotate(12 210 150)" filter="url(#soft)">
    <rect x="182" y="112" width="58" height="58" rx="10" fill="#675298"/>
    <circle cx="204" cy="134" r="4.2" fill="#ffffff"/>
    <circle cx="218" cy="134" r="4.2" fill="#ffffff"/>
    <circle cx="211" cy="141" r="4.2" fill="#ffffff"/>
    <circle cx="204" cy="148" r="4.2" fill="#ffffff"/>
    <circle cx="218" cy="148" r="4.2" fill="#ffffff"/>
    <rect x="186" y="116" width="50" height="50" rx="8" fill="none" stroke="#ffffff" stroke-opacity="0.25" stroke-width="2"/>
  </g>
  <!-- warm pawn / meeple -->
  <g filter="url(#soft)">
    <path d="M252 168 c-8 0 -12 -14 0 -24 c12 10 8 24 0 24 Z" fill="#A64D35"/>
    <rect x="243" y="168" width="18" height="12" rx="5" fill="#A64D35"/>
    <circle cx="252" cy="152" r="5" fill="#A64D35"/>
  </g>
  <!-- front card, tilted right, overlapping -->
  <g transform="rotate(7 150 175)" filter="url(#soft)">
    <rect x="104" y="118" width="84" height="118" rx="9" fill="#FFFCF6" stroke="#DEDBCC" stroke-width="2"/>
    <rect x="114" y="128" width="64" height="98" rx="5" fill="none" stroke="#8A6427" stroke-opacity="0.4" stroke-width="2"/>
    <circle cx="146" cy="166" r="13" fill="none" stroke="#8A6427" stroke-width="2"/>
    <path d="M146 158 l6 9 -6 9 -6 -9 Z" fill="#8A6427" opacity="0.6"/>
  </g>
  <!-- tiny star accents -->
  <path d="M58 70 l4 8 9 1 -7 6 2 9 -8 -5 -8 5 2 -9 -7 -6 9 -1 Z" fill="#8A6427" opacity="0.35"/>
  <path d="M272 66 l3 6 7 1 -5 4 1 6 -6 -3 -6 3 1 -6 -5 -4 7 -1 Z" fill="#675298" opacity="0.4"/>
</svg>"""


def _hero_art_html() -> str:
    return f'<div class="hero-art">{_HERO_ART}</div>'


def _b64(path: pathlib.Path) -> str:
    """Small local image -> base64 data URI (no network requests)."""
    import base64
    try:
        return base64.b64encode(path.read_bytes()).decode("ascii")
    except OSError:
        return ""


def _preset_card(key: str, selected: bool = False) -> str:
    p = PRESETS[key]
    sel = " preset-selected" if selected else ""
    icons = {
        "quick": '<circle cx="12" cy="13" r="8"/><path d="M12 8v5l3 2M9 2h6M12 2v3"/>',
        "time": '<path d="M4 8h13v9a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4zM17 9h2a3 3 0 0 1 0 6h-2M7 3v2M11 2v3M15 3v2"/>',
        "five": '<circle cx="9" cy="8" r="3"/><circle cx="18" cy="9" r="2.5"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 15a5 5 0 0 1 6 5v1"/>',
    }
    icon = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" '
            f'aria-hidden="true">{icons[key]}</svg>')
    return (f'<div class="preset-card{sel}" data-preset="{key}">'
            f'<span class="preset-icon">{icon}</span>'
            f'<div class="preset-label">{p["label"]}</div>'
            f'<div class="preset-sub">{p["blurb"]}<br>Complexity up to {p["c"]:.1f}/5'
            f'</div></div>')


def _featured_reason(g: pd.Series) -> str:
    """One short, true sentence about why this game is on the front page."""
    rated = int(g["users_rated"])
    if rated >= 50000:
        return f"Rated {rated/1000:.0f}k+ times by the BGG community."
    if rated >= 10000:
        return (f"Rated {rated/1000:.1f}k times — one of the "
                "most-voted games on BGG.")
    return f"Rated {rated:,} times by BGG voters."


def _do_dice_roll(games: pd.DataFrame, n_players: int, pref_minutes: int,
                  pref_complexity: float, time_mode: str,
                  comp_mode: str = "pref") -> None:
    """Run one dice pick from the current top matches.

    Shared by "Roll for a pick" and "Roll again": sample one game from
    the top 10 matches (never the same game twice in a row), and store
    the result + pool size in session state. Updates dice_empty when
    nothing fits. When the complexity rule is Maximum, the hard cap is
    applied BEFORE the top-10 slice.
    """
    st.session_state["dice_settings"] = (n_players, pref_minutes,
                                         pref_complexity, time_mode, comp_mode)
    comp_max = pref_complexity if comp_mode == "max" else None
    top = recommend(games, n_players, pref_minutes, pref_complexity,
                    time_mode=time_mode, complexity_max=comp_max, top_n=10)
    if len(top) == 0:
        st.session_state.pop("dice_pick", None)
        st.session_state["dice_empty"] = True
        return
    st.session_state.pop("dice_empty", None)
    last = st.session_state.get("dice_last_id")
    cand = top
    if len(cand) > 1 and last is not None:
        cand = cand[cand["game_id"] != last]
        if len(cand) == 0:          # only the previous pick fits -> reuse it
            cand = top
    pick = cand.sample(1).iloc[0]
    st.session_state["dice_pick"] = pick.to_dict()
    st.session_state["dice_last_id"] = pick["game_id"]
    st.session_state["dice_pool_size"] = int(len(top))


def _number(value, digits=0, fallback="unavailable") -> str:
    """Display missing values honestly instead of rendering 'nan'."""
    if pd.isna(value):
        return fallback
    return f"{float(value):.{digits}f}"


def _game_meta_html(g: pd.Series, year: bool = False) -> str:
    parts = [f'<span class="score-strong">{_number(g["avg_rating"], 2)}</span> BGG']
    if year and pd.notna(g["year_published"]):
        parts.append(_number(g["year_published"]))
    parts.append(f"{_players(g)} players")
    if pd.notna(g["playing_time_min"]) and g["playing_time_min"] > 0:
        parts.append(f'{_number(g["playing_time_min"])} min')
    else:
        parts.append("playtime unavailable")
    return " · ".join(parts)


def _fit_note(g, n, minutes, complexity, time_mode, comp_mode):
    notes = []
    for label, text in reason_bits(g, n, minutes, complexity, time_mode, comp_mode):
        if label == "Players":
            continue  # the actual player range is already visible in the metadata
        if label == "Playtime" and time_mode == "max":
            notes.append("Within your time limit")
        elif label == "Complexity" and comp_mode == "max":
            notes.append("Within your complexity limit")
        else:
            notes.append(f'{label}: {text.lower()}')
    return " · ".join(notes)


def _game_card_html(g, rank=None, note="", featured=False) -> str:
    rank_html = ""
    if rank is not None:
        badge = '<span class="top-fit-tag">Top fit</span>' if rank == 1 else ""
        rank_html = f'<div class="card-rank-row"><span class="rank-badge">#{rank}</span>{badge}</div>'
    art_cls = "game-card__art featured-art" if featured else "game-card__art"
    comp = (f'Complexity {_number(g["complexity_weight"], 1)}/5'
            if pd.notna(g["complexity_weight"]) else "Complexity unavailable")
    return (
        '<article class="game-card">'
        f'<div class="{art_cls}">{_cat_art(g["top_category"], 88 if featured else 64)}</div>'
        f'{rank_html}<div class="game-card__title">{escape(str(g["name"]))}</div>'
        f'<div class="game-card__meta">{_game_meta_html(g, year=featured)}</div>'
        f'<div class="tag-row"><span class="neutral-tag">{comp}</span>'
        f'<span class="neutral-tag">{escape(str(g["top_category"]))}</span></div>'
        f'<div class="fit-note">{escape(note)}</div>'
        f'<div class="game-card__action"><a href="{_bgg_link(g)}" target="_blank" '
        'rel="noopener noreferrer">View on BGG ↗</a></div></article>'
    )


def _dice_result_html(g, note):
    return (
        '<div class="dice-result">'
        f'<div class="dice-result-art">{_cat_art(g["top_category"], 96)}</div>'
        '<div class="dice-result-body">'
        f'<div class="game-card__title">{escape(str(g["name"]))}</div>'
        f'<div class="game-card__meta">{_game_meta_html(g)}</div>'
        f'<div class="fit-note">{escape(note)}</div>'
        f'<div class="game-card__action"><a href="{_bgg_link(g)}" target="_blank" '
        'rel="noopener noreferrer">View on BGG ↗</a></div></div></div>'
    )


def render_home(games: pd.DataFrame) -> None:
    games = games.copy()
    if "top_category" not in games.columns:
        games["top_category"] = games["categories"].fillna("").str.split(";").str[0].replace("", "Other")

    with st.container(key="home_hero"):
        text, art = st.columns([3, 2])
        with text:
            st.markdown(
                '<span class="hero-badge">A cozy data-powered finder</span>'
                '<h1 class="hero-title">What are we playing tonight?</h1>'
                '<div class="hero-desc">Your friends bring the snacks. '
                "We'll help you pick the game.</div>"
                '<div class="hero-note">A little luck. A great night.</div>',
                unsafe_allow_html=True)
            with st.container(key="hero_actions"):
                a, b = st.columns(2)
                with a:
                    if st.button("Find our next game", key="hero_find_btn", type="primary"):
                        switch_to("find")
                with b:
                    if st.button("Start with a game I love", key="hero_more_btn"):
                        switch_to("more")
        with art:
            st.markdown(_hero_art_html(), unsafe_allow_html=True)

    st.subheader("Tonight's plan")
    st.caption("Pick a scene, then fine-tune your settings.")
    active = _active_preset_key()
    with st.container(key="home_presets"):
        for key, col in zip(PRESETS, st.columns(3)):
            with col, st.container(key=f"preset_{key}"):
                selected = active == key
                st.markdown(_preset_card(key, selected), unsafe_allow_html=True)
                if selected:
                    st.button("Selected ✓", key=f"preset_btn_{key}",
                              width="stretch", disabled=True)
                elif st.button("Use this preset", key=f"preset_btn_{key}",
                               width="stretch"):
                    apply_preset(key)

    dn = st.session_state.get("find_n", 4)
    dt = st.session_state.get("find_time", 45)
    dc = st.session_state.get("find_comp", 2.5)
    dm = "max" if st.session_state.get("find_mode") == "Maximum time" else "pref"
    dcm = "max" if st.session_state.get("find_comp_mode") == "Maximum complexity" else "pref"
    settings = (dn, dt, dc, dm, dcm)
    # A previous roll must not claim to match newly changed settings.
    if st.session_state.get("dice_settings") != settings:
        st.session_state.pop("dice_pick", None)
        st.session_state.pop("dice_empty", None)
    t_desc = f"up to {dt} min" if dm == "max" else f"around {dt} min"
    c_desc = f"complexity up to {dc:.1f}/5" if dcm == "max" else f"complexity around {dc:.1f}/5"

    with st.container(key="home_dice"):
        st.markdown(
            f'<div class="dice-head">{_cat_art("Dice", 26)} Tonight’s dice pick</div>'
            '<div class="dice-sub">A little luck can settle the debate.</div>'
            f'<div class="dice-summary">{dn} players · {t_desc} · {c_desc}</div>',
            unsafe_allow_html=True)
        label = "Roll again" if st.session_state.get("dice_pick") is not None else "Roll for a pick"
        if st.button(label, key="dice_roll_btn", type="primary"):
            _do_dice_roll(games, dn, dt, dc, dm, dcm)
            st.rerun()
        if st.session_state.get("dice_empty"):
            st.info("No game fits yet. Try more time or a higher complexity limit.")
            a, b = st.columns(2)
            with a:
                if st.button("Add 30 minutes", key="dice_more_time", width="stretch"):
                    st.session_state["find_time"] = min(300, dt + 30)
                    st.session_state.pop("find_time_w", None)
                    st.rerun()
            with b:
                if st.button("Reset settings", key="dice_reset", width="stretch"):
                    _reset_find_state()
                    st.rerun()
        elif st.session_state.get("dice_pick") is not None:
            g = pd.Series(st.session_state["dice_pick"])
            st.markdown(_dice_result_html(g, _fit_note(g, dn, dt, dc, dm, dcm)), unsafe_allow_html=True)
            pool_n = st.session_state.get("dice_pool_size", 0)
            if pool_n == 1:
                st.caption("This is the only game that fits your current settings.")
            else:
                st.caption(f"Picked from your top {pool_n} matches.")

    st.subheader("Featured games")
    st.caption("A few of the most-voted games in the collection.")
    examples = games.sort_values("users_rated", ascending=False).drop_duplicates("name").head(3)
    cards = [_game_card_html(g, note=_featured_reason(g), featured=True) for _, g in examples.iterrows()]
    st.markdown(f'<div class="game-grid featured-grid">{"".join(cards)}</div>', unsafe_allow_html=True)

    with st.container(key="home_invite"):
        art, text = st.columns([1, 5])
        with art:
            icon = _ASSETS / "mbti" / "main.png"
            image_html = (f'<img src="data:image/png;base64,{_b64(icon)}" '
                          'alt="Board Game Bestiary mascot"/>' if icon.exists()
                          else _cat_art("Fantasy", 96))
            st.markdown(f'<div class="invite-art">{image_html}</div>', unsafe_allow_html=True)
        with text:
            st.markdown('<div class="bi-title">Meet your tabletop creature.</div>'
                        '<div class="bi-sub">Answer 8 questions and discover your '
                        'creature — plus 3 games to try.</div>', unsafe_allow_html=True)
            if st.button("Take the quiz", key="home_bestiary", type="primary"):
                switch_to("bestiary")

    with st.container(key="compact_actions"):
        a, b = st.columns(2)
        with a:
            if st.button("Similar games", key="home_more"):
                switch_to("more")
        with b:
            if st.button("Explore the data", key="home_explore"):
                switch_to("explore")

    med_rating = float(games["avg_rating"].median())
    med_time = float(games["playing_time_min"].median())
    st.markdown(f'<div class="data-strip">{len(games):,} games · median {med_time:.0f} min · '
                f'{games["top_category"].nunique()} categories · median BGG rating {med_rating:.2f}/10</div>',
                unsafe_allow_html=True)
    with st.expander("About the data — sources, cleaning & limitations"):
        st.markdown(
            "Game details and community statistics come from the **BoardGameGeek XML API**. "
            "The original cleaning pipeline removed expansions, re-implementations and non-games.\n\n"
            "BGG stores some missing values as `0`; these are converted to missing values in the cleaned dataset. "
            "Ancient and outlier release years are treated as unknown.\n\n"
            "Community ratings help compare games, but individual taste varies. "
            "Recommendations require at least **100 ratings**."
        )


def _reset_find_state():
    for key, value in (("find_n", 4), ("find_time", 45), ("find_comp", 2.5),
                       ("find_mode", "Preferred time"), ("find_comp_mode", "Preferred complexity")):
        st.session_state[key] = value
        st.session_state.pop(f"{key}_w", None)
    for key in ("dice_pick", "dice_empty", "dice_settings"):
        st.session_state.pop(key, None)


def render_find(games: pd.DataFrame) -> None:
    st.title("Your table, your rules.")
    st.write("Set your night's conditions — find the best fits from real BoardGameGeek data.")
    for key, value in (("find_n", 4), ("find_time", 45), ("find_comp", 2.5),
                       ("find_mode", "Preferred time"), ("find_comp_mode", "Preferred complexity")):
        st.session_state.setdefault(key, value)

    with st.container(key="find_filters"):
        st.markdown('<div class="panel-title">Your game night</div>', unsafe_allow_html=True)
        with st.container(key="find_controls"):
            players, duration, complexity = st.columns(3)
            with players:
                n_players = st.slider("Players", 1, 10, value=int(st.session_state["find_n"]), key="find_n_w")
                st.caption("Every result supports your group size.")
            with duration:
                pref_minutes = st.slider("Playtime (min)", 10, 300, step=5,
                                         value=int(st.session_state["find_time"]), key="find_time_w")
                time_options = ["Preferred time", "Maximum time"]
                mode_label = st.radio("Time rule", time_options,
                                      index=time_options.index(st.session_state["find_mode"]),
                                      format_func=lambda v: v.split()[0], horizontal=True, key="find_mode_w")
                st.caption("Only games within your limit." if mode_label == "Maximum time"
                           else "Nearby durations may appear.")
            with complexity:
                pref_complexity = st.slider("Complexity (/5)", 1.0, 5.0, step=0.5,
                                            value=float(st.session_state["find_comp"]), key="find_comp_w")
                comp_options = ["Preferred complexity", "Maximum complexity"]
                comp_label = st.radio("Complexity rule", comp_options,
                                      index=comp_options.index(st.session_state["find_comp_mode"]),
                                      format_func=lambda v: v.split()[0], horizontal=True, key="find_comp_mode_w")
                st.caption("Heavier games are excluded." if comp_label == "Maximum complexity"
                           else "Nearby complexity levels may appear.")

    st.session_state.update(find_n=int(n_players), find_time=int(pref_minutes),
                            find_comp=float(pref_complexity), find_mode=mode_label, find_comp_mode=comp_label)
    mode = "max" if mode_label == "Maximum time" else "pref"
    comp_mode = "max" if comp_label == "Maximum complexity" else "pref"
    matched = preset_match(n_players, pref_minutes, pref_complexity, mode, comp_mode)
    if matched:
        st.markdown(f'<div class="preset-chip">Scene · {PRESETS[matched]["label"]}</div>', unsafe_allow_html=True)

    top = recommend(games, n_players, pref_minutes, pref_complexity,
                    time_mode=mode, complexity_max=pref_complexity if comp_mode == "max" else None)
    if top.empty:
        st.info("No game fits yet. Try more time or a higher complexity limit.")
        a, b = st.columns(2)
        with a:
            if st.button("Add 30 minutes", key="find_more_time", width="stretch"):
                st.session_state["find_time"] = min(300, pref_minutes + 30)
                st.session_state.pop("find_time_w", None)
                st.rerun()
        with b:
            if st.button("Reset filters", key="find_reset", width="stretch"):
                _reset_find_state()
                st.rerun()
        return

    st.subheader(f"Games for your group of {n_players}")
    time_desc = f"up to {pref_minutes} min" if mode == "max" else f"around {pref_minutes} min"
    comp_desc = (f"complexity up to {pref_complexity:.1f}/5" if comp_mode == "max"
                 else f"complexity around {pref_complexity:.1f}/5")
    st.markdown(f'<div class="summary-bar"><b>{len(top)} matches</b> · {time_desc} · {comp_desc}</div>',
                unsafe_allow_html=True)
    cards = [_game_card_html(g, rank=rank,
                            note=_fit_note(g, n_players, pref_minutes, pref_complexity, mode, comp_mode))
             for rank, (_, g) in enumerate(top.iterrows(), 1)]
    st.markdown(f'<div class="game-grid find-grid">{"".join(cards)}</div>', unsafe_allow_html=True)

    with st.expander("How matching works"):
        st.markdown(
            "**Player count is required.** Maximum time and complexity are hard limits. "
            "Preferred rules allow nearby values and rank closer games higher.\n\n"
            "**Fit score** = 35% players fit + 20% playtime fit + 20% complexity fit + 25% BGG rating. "
            "It measures the match to your settings; BGG rating is the community average."
        )
    with st.expander("Full stats for these games"):
        full = top.copy()
        full["Players"] = full.apply(_players, axis=1)
        full["Rating"] = full["avg_rating"].round(2)
        full["Ratings given"] = full["users_rated"].astype(int)
        full["Fit score"] = full["score"].round(3)
        st.dataframe(full[["name", "Players", "Rating", "Ratings given", "Fit score"]]
                     .rename(columns={"name": "Game"}), hide_index=True, width="stretch")
    st.caption("Only games with at least 100 BGG ratings are included.")