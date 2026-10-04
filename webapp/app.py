"""
app.py - Board Game Finder: an interactive web app (modular build)
=================================================================
Public face of our mini-project: helps real board-game players pick a
game, plus an INTERACTIVE data explorer.

THIS FILE IS THE MAIN ENTRY POINT. The pages live in three files, one
per group member:

    1. part1_find.py    (Member 1) - Home + "Find me a game" + scoring
    2. part2_explore.py (Member 2) - "Explore the data" (interactive lab)
    3. part3_more.py    (Member 3) - "More like this" + Board Game Bestiary

app.py only: global styles, data loading, sidebar navigation, routing.
Each member edits ONLY their own part file.

Pages (left sidebar):
  1. Home              - what this is, where the data comes from
  2. Find me a game    - sliders -> top-10 games that fit YOUR game night
  3. Explore the data  - INTERACTIVE charts: filter, hover, zoom, search
  4. More like this    - pick a game -> 5 games like it
  5. Board Game Bestiary - 8-question parody quiz -> your creature + games

USAGE
-----
  Windows (easiest): double-click run_webapp.bat in the repo root
  Windows (Anaconda Prompt):
      streamlit run webapp/app.py
  Mac / Linux:
      streamlit run webapp/app.py

First time only:  pip install streamlit plotly
"""

import datetime
import pathlib
import os

import pandas as pd
import streamlit as st

from part1_find import render_home, render_find
from part2_explore import render_explore
from part3_more import render_more, render_bestiary

# ----------------------------------------------------------------------
# paths (app lives in webapp/, data lives in ../data)
# ----------------------------------------------------------------------
APP_DIR = pathlib.Path(__file__).resolve().parent   # .../webapp
ROOT = APP_DIR.parent                                # repo root
DATA = pathlib.Path(os.environ.get("BOARD_GAME_DATA_DIR", str(ROOT / "data")))

# Shared chart palette: terracotta, sage, purple and gold.
RESEARCH = ["#A94F35", "#675298", "#466449", "#8A6427", "#477F91",
            "#B77893", "#739260", "#CA9B45", "#7F6DAD", "#B56F51", "#909080"]

# ----------------------------------------------------------------------
# page setup
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Board Game Finder",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="auto",
)

# Component-scoped styles: native layout containers stay transparent.
st.markdown("""
<style>
/* Styles are scoped to named components; layout wrappers stay transparent. */
:root {
  --bg-page: #F7F3EA; --bg-sidebar: #F3EFE3;
  --surface: #FFFCF6; --surface-quiet: #F0EBE0;
  --text: #293027; --text-secondary: #626859;
  --border: #DEDBCC; --border-strong: #C9C4AF;
  --primary: #A94F35; --primary-hover: #93422D;
  --primary-soft: #F3E1D6; --purple: #675298;
  --purple-hover: #584585; --purple-soft: #E9E2F5;
  --green: #466449; --green-soft: #E4EDDA;
  --gold: #8A6427; --gold-soft: #F2E5C9;
  --shadow-soft: 0 6px 20px rgba(55,45,30,.05);
}
.stApp { background: var(--bg-page); color: var(--text); }
html, body, [data-testid="stAppViewContainer"] {
  font-family: 'Space Grotesk', 'Segoe UI', system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
}
[data-testid="stMain"] { min-width: 0; }
.block-container {
  max-width: 1120px; padding: 2.5rem 32px 4rem;
  margin-inline: auto; box-sizing: border-box;
  container-type: inline-size; container-name: page;
}
h1 { font-size: 2.5rem; font-weight: 750; letter-spacing: -.025em;
  line-height: 1.18; color: var(--text); overflow-wrap: anywhere; }
h2 { font-size: 1.6rem; font-weight: 700; line-height: 1.3;
  letter-spacing: -.015em; color: var(--text); margin-top: 1.25rem; }
h3 { color: var(--text); font-size: 1.2rem; line-height: 1.4; }
p, li { color: var(--text); font-size: 16px; line-height: 1.6; }
[data-testid="stCaptionContainer"] { opacity: 1 !important; }
[data-testid="stCaptionContainer"] p, [data-testid="stCaption"] p, .stCaption p {
  color: var(--text-secondary) !important; font-size: 13px; line-height: 1.55;
}
a { color: var(--primary); text-underline-offset: 3px; }
a:hover { color: var(--primary-hover); }
svg, img { max-width: 100%; }
[data-testid="stColumn"], [data-testid="stVerticalBlock"] { min-width: 0; }

/* Every real button can wrap on a narrow screen, including its label. */
.stButton > button {
  min-height: 44px; border-radius: 10px; font-weight: 650;
  white-space: normal; padding: 9px 16px; box-shadow: none;
  transition: background .15s ease, border-color .15s ease;
}
.stButton > button p, .stButton > button span {
  color: inherit; font-size: 14px; line-height: 1.4;
  white-space: normal; overflow-wrap: anywhere;
}
.stButton > button[data-testid="stBaseButton-primary"] {
  color: white; background: var(--primary); border: 1px solid var(--primary);
}
.stButton > button[data-testid="stBaseButton-primary"]:hover {
  color: white; background: var(--primary-hover); border-color: var(--primary-hover);
}
.stButton > button[data-testid="stBaseButton-secondary"] {
  color: var(--text); background: var(--surface); border: 1px solid var(--border-strong);
}
.stButton > button[data-testid="stBaseButton-secondary"]:hover {
  color: var(--primary-hover); border-color: var(--primary); background: #FAF2EA;
}
.stButton > button:disabled {
  background: var(--surface-quiet) !important; border-color: var(--border) !important;
  color: var(--text-secondary) !important; opacity: 1; cursor: default;
}
.stButton > button:focus-visible, a:focus-visible,
:is(label[data-baseweb="radio"], label[data-testid="stRadioOption"]):focus-within {
  outline: 3px solid var(--purple); outline-offset: 3px;
}
[data-baseweb="input"], [data-baseweb="select"] > div {
  border-color: var(--border); background: white; border-radius: 10px;
}
[data-baseweb="slider"] [role="slider"] {
  background: var(--primary); border-color: var(--primary);
}
[data-testid="stSegmentedControl"] [aria-checked="true"] {
  background: var(--primary) !important; color: white !important;
}
[data-testid="stSegmentedControl"] [aria-checked="true"] p { color: inherit; }
[data-testid="stSegmentedControl"] button { white-space: normal; }

/* Deliberate surfaces only. Never style all Streamlit containers as cards. */
.st-key-find_filters, .st-key-explore_filters,
.st-key-category_filters, .st-key-similar_seed {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 16px; padding: 22px 24px; box-sizing: border-box;
}
.panel-title { font-size: 19px; font-weight: 700; color: var(--text); line-height: 1.4; }
.st-key-find_filters [data-testid="stCaptionContainer"] p { font-size: 13px; }
.st-key-find_controls > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"],
.st-key-explore_controls > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] {
  display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 24px;
}
.st-key-find_controls > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
.st-key-explore_controls > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
  width: 100% !important; flex: none !important; min-width: 0 !important;
}
.control-endpoints { display: flex; justify-content: space-between;
  color: var(--text-secondary); font-size: 12px; margin-top: -6px; }
.summary-bar { font-size: 14px; line-height: 1.6; color: var(--text-secondary);
  padding: 0; margin: 0 0 8px; overflow-wrap: anywhere; }
.summary-bar b { color: var(--text); }
.preset-chip { color: var(--primary-hover); background: var(--primary-soft);
  padding: 5px 10px; border-radius: 6px; font-size: 13px;
  display: inline-block; margin: 0 0 6px; }


/* Filter header actions keep their content width rather than a narrow fraction. */
.st-key-explore_filter_header > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"],
.st-key-category_filter_header > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] {
  display: flex; flex-wrap: wrap; gap: 12px; align-items: center;
}
.st-key-explore_filter_header [data-testid="stColumn"]:first-child { flex: 1 1 100px !important; min-width: 0 !important; }
.st-key-category_filter_header [data-testid="stColumn"]:first-child { flex: 1 1 220px !important; min-width: 0 !important; }
.st-key-explore_filter_header [data-testid="stColumn"]:last-child,
.st-key-category_filter_header [data-testid="stColumn"]:last-child { width: auto !important; flex: 0 0 auto !important; min-width: 0 !important; }

/* Hero includes the native buttons in the same single gradient surface. */
.st-key-home_hero {
  background: linear-gradient(125deg,#F2E5C9 0%,#F8F1E2 65%,#F3EAF2 100%);
  border: 1px solid var(--border); border-radius: 20px;
  padding: 32px 36px; box-sizing: border-box; box-shadow: var(--shadow-soft);
}
.hero-badge { display: inline-block; font-size: 11px; font-weight: 700;
  letter-spacing: .07em; text-transform: uppercase; color: var(--primary-hover);
  background: var(--primary-soft); border-radius: 99px; padding: 5px 10px; margin-bottom: 14px; }
.hero-title { max-width: 470px; padding: 0 !important; color: var(--text); font-size: 42px; line-height: 1.14;
  font-weight: 750; letter-spacing: -.03em; margin: 0 0 14px; }
.hero-desc { color: var(--text); font-size: 16px; line-height: 1.6; max-width: 470px; }
.hero-note { color: var(--gold); font-size: 13px; margin-top: 10px; }
.hero-art { display: flex; align-items: center; justify-content: center; }
.hero-art-svg { width: 100%; max-width: 280px; height: auto; }
.st-key-hero_actions > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"],
.st-key-compact_actions > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] {
  display: flex; flex-wrap: wrap; gap: 12px; align-items: center;
}
.st-key-hero_actions > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
.st-key-compact_actions > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
  width: auto !important; flex: 0 1 auto !important; min-width: 0 !important;
}
.st-key-home_presets > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] {
  display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 18px;
  align-items: stretch;
}
.st-key-home_presets > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
  width: 100% !important; flex: none !important; min-width: 0 !important;
}
.st-key-preset_quick, .st-key-preset_time, .st-key-preset_five {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 18px; box-sizing: border-box; height: 100%;
}
.st-key-preset_quick:has(.preset-selected),
.st-key-preset_time:has(.preset-selected), .st-key-preset_five:has(.preset-selected) {
  background: var(--primary-soft); border-color: var(--primary);
}
.preset-icon { display: block; color: var(--primary); margin: 0 0 10px; height: 26px; }
.preset-icon svg { width: 26px; height: 26px; }
.preset-label { font-size: 17px; line-height: 1.35; font-weight: 700; color: var(--text); }
.preset-sub { font-size: 13px; line-height: 1.6; color: var(--text-secondary); margin-top: 8px; }
.st-key-home_presets button:disabled { background: transparent !important;
  color: var(--primary-hover) !important; border-color: rgba(169,79,53,.35) !important; }

/* Purple module owns both the roll action and its result. */
.st-key-home_dice { background: var(--purple-soft); border: 1px solid #CFC3E5;
  padding: 24px; border-radius: 18px; box-sizing: border-box; }
.dice-head { display: flex; align-items: center; gap: 10px; font-size: 20px; font-weight: 700; color: var(--text); line-height: 1.4; }
.dice-sub { font-size: 14px; color: var(--text-secondary); line-height: 1.6; margin-top: 5px; }
.dice-summary { font-size: 14px; color: var(--purple); line-height: 1.6; margin: 12px 0 2px; }
.st-key-home_dice button[data-testid="stBaseButton-primary"] {
  background: var(--purple); border-color: var(--purple); color: white;
}
.st-key-home_dice button[data-testid="stBaseButton-primary"]:hover {
  background: var(--purple-hover); border-color: var(--purple-hover);
}
.dice-result { display: flex; gap: 22px; align-items: center; background: var(--surface);
  border-radius: 12px; padding: 20px; box-sizing: border-box; }
.dice-result-art { flex: 0 0 96px; }
.dice-result-body { flex: 1; min-width: 0; }
.dice-result .game-card__title { font-size: 23px; }

/* Pure HTML card grids adapt to the actual content width, including sidebar. */
.game-grid { display: grid; grid-template-columns: repeat(3,minmax(0,1fr));
  gap: 20px; align-items: stretch; }
.similar-grid { grid-template-columns: repeat(2,minmax(0,1fr)); }
.game-card, .sim-card, .bestiary-result-game {
  min-width: 0; display: flex; flex-direction: column; background: var(--surface);
  border: 1px solid var(--border); border-radius: 14px; padding: 20px;
  box-sizing: border-box; gap: 10px;
}
.game-card:hover, .sim-card:hover, .bestiary-result-game:hover {
  border-color: var(--border-strong); box-shadow: var(--shadow-soft);
}
.game-card__art { display: flex; justify-content: center; align-items: center; min-height: 70px; }
.featured-art { background: #F5EFDF; border-radius: 10px; padding: 12px; }
.game-card__title { font-size: 20px; line-height: 1.35; font-weight: 700;
  color: var(--text); margin: 0; overflow-wrap: anywhere; }
.game-card__meta { font-size: 14px; line-height: 1.6; color: var(--text-secondary); }
.score-strong { font-weight: 700; color: var(--text); }
.game-card__action { margin-top: auto; padding-top: 12px; font-size: 14px; }
.game-card__action a { font-weight: 600; color: var(--primary) !important; }
.card-rank-row { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.rank-badge { color: var(--primary-hover); background: var(--primary-soft);
  border-radius: 6px; padding: 2px 8px; font-size: 12px; font-weight: 700; }
.top-fit-tag { color: white; background: var(--primary); border-radius: 6px;
  padding: 2px 8px; font-size: 12px; font-weight: 650; }
.tag-row { display: flex; flex-wrap: wrap; gap: 6px; }
.neutral-tag { color: var(--text-secondary); background: var(--surface-quiet);
  border-radius: 6px; font-size: 12px; line-height: 1.5; padding: 3px 8px;
  overflow-wrap: anywhere; max-width: 100%; box-sizing: border-box; }
.fit-note, .featured-why, .bestiary-reason { color: var(--text-secondary);
  font-size: 13px; line-height: 1.6; }
.sim-label-row { display: flex; align-items: baseline; justify-content: space-between;
  gap: 12px; margin-top: 4px; font-size: 13px; color: var(--text-secondary); }
.sim-score { font-weight: 700; color: var(--purple); }
.sim-track { height: 7px; border-radius: 99px; background: var(--surface-quiet); overflow: hidden; }
.sim-fill { height: 100%; border-radius: 99px; background: var(--purple); }
.cat-art { display: block; margin: 0; flex-shrink: 0; }

/* One green invitation, with its real CTA inside it. */
.st-key-home_invite { background: var(--green-soft); border: 1px solid #C8D8BF;
  border-radius: 16px; padding: 24px; box-sizing: border-box; margin-top: 8px; }
.invite-art { display: flex; justify-content: center; align-items: center; }
.invite-art img { width: 104px; height: 104px; object-fit: contain; border-radius: 12px; }
.bi-title { color: var(--text); font-size: 20px; line-height: 1.4; font-weight: 700; }
.bi-sub { color: var(--text-secondary); font-size: 14px; line-height: 1.6; margin-top: 6px; }
.data-strip { font-size: 13px; color: var(--text-secondary); border-top: 1px solid var(--border);
  padding-top: 16px; margin-top: 20px; line-height: 1.6; }

/* Quiz is centred by max-width, never by empty side columns. */
.st-key-bestiary_quiz { max-width: 680px !important; width: 100%; margin-inline: auto;
  background: var(--surface); border: 1px solid var(--border); border-radius: 20px;
  padding: 28px 32px; box-shadow: var(--shadow-soft); box-sizing: border-box; }
.quiz-head { display: flex; align-items: center; gap: 16px; }
.quiz-mascot { width: 52px; height: 52px; object-fit: contain; border-radius: 12px; flex-shrink: 0; }
.quiz-meta { flex: 1; min-width: 0; }
.quiz-step { color: var(--text-secondary); font-size: 13px; margin-bottom: 10px; }
.quiz-grid { display: grid; grid-template-columns: repeat(8,minmax(0,1fr)); gap: 6px; }
.quiz-cell { height: 8px; background: var(--surface-quiet); border-radius: 99px; box-sizing: border-box; }
.quiz-cell.done { background: var(--purple); }
.quiz-cell.current { background: var(--purple-soft); border: 1.5px solid var(--purple); }
.quiz-question { font-size: 23px; line-height: 1.4; font-weight: 700; color: var(--text);
  margin: 10px 0 2px; overflow-wrap: anywhere; }
.st-key-bestiary_quiz [data-testid="stElementContainer"]:has([data-testid="stRadio"]),
.st-key-bestiary_quiz [data-testid="stRadio"], .st-key-bestiary_quiz [role="radiogroup"] {
  width: 100% !important; max-width: 100%; align-self: stretch;
}
.st-key-bestiary_quiz [role="radiogroup"] { gap: 10px; }
.st-key-bestiary_quiz [role="radiogroup"] > div { width: 100%; }
.st-key-bestiary_quiz :is(label[data-baseweb="radio"], label[data-testid="stRadioOption"]) {
  display: flex; width: 100%; min-height: 64px; margin: 0; align-items: center;
  padding: 14px 16px; box-sizing: border-box; background: var(--surface);
  border: 1px solid var(--border); border-radius: 11px; cursor: pointer;
}
.st-key-bestiary_quiz :is(label[data-baseweb="radio"], label[data-testid="stRadioOption"]):hover {
  background: #F7F3FB; border-color: var(--purple);
}
.st-key-bestiary_quiz :is(label[data-baseweb="radio"], label[data-testid="stRadioOption"]):has(input:checked) {
  background: var(--purple-soft); border: 2px solid var(--purple); padding: 13px 15px;
}
.st-key-bestiary_quiz :is(label[data-baseweb="radio"], label[data-testid="stRadioOption"]) p {
  color: var(--text); font-size: 15px; line-height: 1.6; white-space: normal;
  overflow-wrap: anywhere;
}
.st-key-bestiary_quiz label[data-testid="stRadioOption"]:has(input:checked) > div > div:first-child {
  background: var(--purple) !important; border-color: var(--purple) !important;
}
.st-key-quiz_actions > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] {
  display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 12px;
}
.st-key-quiz_actions > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
  width: 100% !important; flex: none !important; min-width: 0 !important;
}
.st-key-quiz_actions button { min-width: 100px; max-width: 100%; }
.st-key-quiz_actions [data-testid="stColumn"]:last-child > [data-testid="stVerticalBlock"] {
  align-items: flex-end;
}
.quiz-note { font-size: 13px; color: var(--text-secondary); line-height: 1.6; margin-top: 4px; }
.bestiary-hero { display: flex; align-items: center; gap: 28px; background: var(--purple-soft);
  border: 1px solid #CFC3E5; border-radius: 18px; padding: 26px; box-sizing: border-box; }
.bestiary-creature-img { width: 144px; height: 144px; border-radius: 16px; object-fit: contain; flex-shrink: 0; }
.bestiary-hero-text { flex: 1; min-width: 0; }
.bestiary-step { font-size: 13px; color: var(--purple); margin-bottom: 6px; }
.bestiary-creature-title { font-size: 30px; line-height: 1.3; color: var(--text); font-weight: 750; }
.bestiary-creature-name { font-size: 15px; color: var(--text-secondary); margin-top: 4px; }
.bestiary-creature-desc { font-size: 15px; line-height: 1.6; color: var(--text); margin: 12px 0; }
.bestiary-tag { color: var(--purple); background: #F8F5FC; padding: 4px 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; }
.bestiary-why { color: var(--text-secondary); font-size: 14px; line-height: 1.6; }

[data-testid="stSidebar"] { background: var(--bg-sidebar); border-right: 1px solid var(--border);
  min-width: 248px; max-width: 248px; }
[data-testid="stSidebarHeader"] { display: flex; width: 100% !important; box-sizing: border-box; padding: 18px 0 10px !important; min-height: 56px; gap: 8px !important; }
[data-testid="stSidebarHeader"]::before { content: "Board Game Finder"; display: block;
  color: var(--text); font-size: 15px; line-height: 1.4; font-weight: 700; white-space: nowrap; flex: 0 0 auto; }
[data-testid="stSidebarHeader"] [data-testid="stLogoSpacer"] { display: none !important; }
[data-testid="stSidebarCollapseButton"] { flex: 0 0 24px !important; min-width: 24px; max-width: 24px; }
[data-testid="stSidebarNav"] { padding-top: 4px; }
[data-testid="stSidebarNav"] a { border-radius: 9px; padding: 9px 12px; margin: 3px 6px; min-height: 42px; }
[data-testid="stSidebarNav"] a:hover { background: rgba(169,79,53,.07); }
[data-testid="stSidebarNav"] a[aria-current="page"] { background: var(--primary-soft); }
.footer-note { color: var(--text-secondary); font-size: 12px; line-height: 1.7;
  text-align: center; margin-top: 2.5rem; overflow-wrap: anywhere; }
[data-testid="stPlotlyChart"] { border: 1px solid var(--border); border-radius: 12px;
  overflow: hidden; background: white; }
hr { border-color: var(--border); }

/* Container queries use available page width, so an open sidebar is included. */
@container page (max-width: 880px) {
  .game-grid:not(.similar-grid) { grid-template-columns: repeat(2,minmax(0,1fr)); }
  .st-key-explore_controls > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] {
    grid-template-columns: repeat(2,minmax(0,1fr));
  }
}
@container page (max-width: 740px) {
  .st-key-home_hero > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] { flex-direction: column; }
  .st-key-home_hero > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    width: 100% !important; flex: none !important; min-width: 0 !important;
  }
  .hero-title { font-size: 34px; }
  .hero-art-svg { max-width: 180px; }
  .bestiary-creature-title { font-size: 26px; }
}
@container page (max-width: 620px) {
  .game-grid:not(.similar-grid), .game-grid.similar-grid { grid-template-columns: minmax(0,1fr); }
  .st-key-home_presets > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"],
  .st-key-find_controls > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"],
  .st-key-explore_controls > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] {
    grid-template-columns: minmax(0,1fr);
  }
  .st-key-home_hero { padding: 24px; }
  .dice-result { align-items: flex-start; gap: 16px; }
  .dice-result-art { flex-basis: 64px; }
  .dice-result-art svg { width: 64px; height: 64px; }
  .dice-result .game-card__title { font-size: 20px; }
  .bestiary-hero { flex-direction: column; align-items: flex-start; gap: 18px; }
  .bestiary-creature-img { width: 112px; height: 112px; }
}
@media (max-width: 768px) {
  .block-container { padding: 1.6rem 18px 3rem; }
  h1 { font-size: 2rem; } h2 { font-size: 1.4rem; }
  .st-key-bestiary_quiz { padding: 22px 20px; }
  .st-key-home_dice, .st-key-find_filters, .st-key-explore_filters,
  .st-key-category_filters, .st-key-similar_seed, .st-key-home_invite { padding: 20px; }
  .quiz-question { font-size: 21px; }
}
@media (max-width: 420px) {
  .block-container { padding-inline: 14px; }
  .st-key-home_hero { padding: 20px; }
  .hero-title { font-size: 30px; }
  .st-key-bestiary_quiz { padding: 20px 16px; }
  .st-key-bestiary_quiz :is(label[data-baseweb="radio"], label[data-testid="stRadioOption"]) { padding: 12px; }
  .st-key-bestiary_quiz :is(label[data-baseweb="radio"], label[data-testid="stRadioOption"]):has(input:checked) { padding: 11px; }
  .dice-result { flex-direction: column; padding: 16px; }
  .dice-result-art { flex-basis: auto; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { transition: none !important; animation: none !important; }
}

</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------
# load data once and share it across pages (Streamlit caches it)
# ----------------------------------------------------------------------
@st.cache_data
def load_games() -> pd.DataFrame:
    df = pd.read_csv(DATA / "cleaned_games.csv", encoding="utf-8-sig")
    df["users_rated"] = df["users_rated"].fillna(0)
    df["top_category"] = (df["categories"].fillna("")
                          .str.split(";").str[0].str.strip()
                          .replace("", "Other"))
    return df


@st.cache_data
def load_similar() -> pd.DataFrame:
    return pd.read_csv(DATA / "similar_games.csv", encoding="utf-8-sig")


missing_data = [name for name in ("cleaned_games.csv", "similar_games.csv")
                if not (DATA / name).is_file()]
if missing_data:
    st.error("Game data is missing. Keep the original data folder beside webapp.")
    st.code("\n".join(str(DATA / name) for name in missing_data), language=None)
    st.stop()

games = load_games()
similar = load_similar()


# ----------------------------------------------------------------------
# sidebar navigation - native Streamlit multipage style (like the
# reference demo: icon + label, current page highlighted)
# ----------------------------------------------------------------------
MBTI_ICONS = pathlib.Path(__file__).resolve().parent / "assets" / "mbti"
# Sidebar brand is rendered above the navigation items by CSS
# ([data-testid="stSidebar"]::before), so no markdown brand block is
# needed here. The Bestiary mascot now lives on the Home page and the
# Bestiary page itself (see part1_find / part3_more).


def _page_home():
    render_home(games)


def _page_find():
    render_find(games)


def _page_explore():
    render_explore(games, RESEARCH)


def _page_more():
    render_more(similar, games)


def _page_bestiary():
    render_bestiary(games, MBTI_ICONS)


pages = [
    st.Page(_page_home, title="Home", icon=":material/home:",
            url_path="home", default=True),
    st.Page(_page_find, title="Find a game", icon=":material/target:",
            url_path="find"),
    st.Page(_page_explore, title="Explore the data", icon=":material/insights:",
            url_path="explore"),
    st.Page(_page_more, title="Similar games", icon=":material/cards:",
            url_path="more"),
    st.Page(_page_bestiary, title="Board Game Bestiary", icon=":material/pets:",
            url_path="bestiary"),
]

# expose the st.Page objects to the part modules so st.switch_page can
# receive an object (passing a url string only works for file-based pages)
st.session_state["PAGES"] = {p.url_path: p for p in pages}

pg = st.navigation(pages, position="sidebar")
st.sidebar.caption("Data-science mini-project · data: BoardGameGeek")
pg.run()

# build stamp: generated at runtime so it can never be a future date
_build = datetime.date.today().isoformat()
st.markdown(
    f'<div class="footer-note">Board Game Finder · Introduction to Data '
    f'Science mini-project · Data: BoardGameGeek XML API2 · '
    f'build {_build}</div>',
    unsafe_allow_html=True,
)
