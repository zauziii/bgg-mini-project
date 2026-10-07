"""
part3_more.py - Ezeme Onyenezi Innocent's part: "Similar games" + Board Game Bestiary
=======================================================================
Task checklist:
  1. Pick several games in "Similar games"; the progress bars and
     similarity scores must render correctly for each.
  2. Walk the full quiz flow; each of the four creatures must be reachable.
  3. Sanity-check the recommended games on the results page:
     they must belong to the creature's categories, and only games with
     a decent number of user ratings (users_rated >= 100) should appear —
     matching the policy stated on the Home page.

This file is imported by webapp/app.py:
    from part3_more import render_more, render_bestiary
"""

import re
from html import escape

import pandas as pd
import streamlit as st

from part1_find import _cat_art, _players, _game_meta_html, _number


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
# PAGE 4 - SIMILAR GAMES
# ----------------------------------------------------------------------
def _series_key(name: str) -> str:
    """Crude series key: 'Brass: Lancashire' and 'Brass: Birmingham'
    both become 'brass', so we can show one per series by default."""
    return re.split(r"[:,(]", name)[0].strip().lower()


def _similar_card_html(c, rank):
    g = c["g"]
    shared_html = ""
    if c["shared"]:
        tags = "".join(f'<span class="neutral-tag">{escape(x)}</span>' for x in c["shared"][:4])
        shared_html = '<div class="fit-note">Shared features</div>' + f'<div class="tag-row">{tags}</div>'
    score = max(0.0, min(1.0, float(c["score"])))
    complexity = (f'Complexity {_number(g["complexity_weight"], 1)}/5'
                  if pd.notna(g["complexity_weight"]) else "Complexity unavailable")
    return (
        '<article class="sim-card">'
        f'<div class="game-card__art">{_cat_art(g["top_category"], 64)}</div>'
        f'<div class="card-rank-row"><span class="rank-badge">#{rank}</span></div>'
        f'<div class="game-card__title">{escape(str(c["name"]))}</div>'
        f'<div class="game-card__meta">{_game_meta_html(g)}</div>'
        f'<div class="tag-row"><span class="neutral-tag">{complexity}</span></div>'
        f'{shared_html}<div class="sim-label-row"><span>Feature similarity</span>'
        f'<span class="sim-score">{score:.0%}</span></div>'
        f'<div class="sim-track"><div class="sim-fill" style="width:{score * 100:.1f}%"></div></div>'
        f'<div class="game-card__action"><a href="https://boardgamegeek.com/boardgame/{int(g["game_id"])}" '
        'target="_blank" rel="noopener noreferrer">View on BGG ↗</a></div></article>'
    )


def render_more(similar: pd.DataFrame, games: pd.DataFrame) -> None:
    st.title("Similar games")
    st.write("Start with a game you enjoy. Explore shared mechanics and themes.")
    names = sorted(similar["name"].dropna().unique().tolist())
    if not names:
        st.info("No similarity records are available yet.")
        return
    with st.container(key="similar_seed"):
        select, summary = st.columns([1.6, 1])
        with select:
            choice = st.selectbox("Choose a game", names,
                                  index=names.index("Catan") if "Catan" in names else 0, key="sim_seed")
        choice_g = games[games["name"] == choice]
        with summary:
            if not choice_g.empty:
                g0 = choice_g.iloc[0]
                st.markdown('<div class="fit-note">Selected game</div>'
                            f'<div class="game-card__title">{escape(choice)}</div>'
                            f'<div class="game-card__meta">{_game_meta_html(g0)}</div>', unsafe_allow_html=True)

    row = similar[similar["name"] == choice].iloc[0]
    st.subheader(f"Games like {choice}")
    cg_cats, cg_mech = set(), set()
    if not choice_g.empty:
        cg = choice_g.iloc[0]
        cg_cats = {s.strip() for s in str(cg["categories"]).split(";") if s.strip() and s != "nan"}
        cg_mech = {s.strip() for s in str(cg["mechanics"]).split(";") if s.strip() and s != "nan"}

    candidates = []
    seen = set()
    for k in range(1, 6):
        name, score = row.get(f"sim{k}_name"), row.get(f"sim{k}_score")
        if pd.isna(name) or pd.isna(score) or name in seen:
            continue
        seen.add(name)
        hit = games[games["name"] == name]
        if hit.empty:
            continue
        g = hit.iloc[0]
        # Stable ordering prevents badges from shuffling on every rerun.
        cats = sorted({s.strip() for s in str(g["categories"]).split(";")} & cg_cats)[:2]
        mechanics = sorted({s.strip() for s in str(g["mechanics"]).split(";")} & cg_mech)[:2]
        candidates.append({"name": name, "score": score, "g": g, "shared": cats + mechanics})
    groups = {}
    for candidate in candidates:
        groups.setdefault(_series_key(candidate["name"]), []).append(candidate)
    main = [group[0] for group in groups.values()]
    extra = [candidate for group in groups.values() for candidate in group[1:]]
    if not main:
        st.info("No related games from this record are present in the current dataset.")
        return
    st.caption(f'{len(main)} similar games' + (f' · {len(extra)} more from the same series' if extra else ''))
    # One real CSS grid establishes common rows, equal heights and row gaps.
    cards = [_similar_card_html(candidate, rank) for rank, candidate in enumerate(main, 1)]
    st.markdown(f'<div class="game-grid similar-grid">{"".join(cards)}</div>', unsafe_allow_html=True)
    if extra:
        with st.expander(f"More from the same series ({len(extra)} games)"):
            for candidate in extra:
                st.write(f'{candidate["name"]} — similarity {candidate["score"]:.0%}')
    st.caption("Similarity reflects shared game features, not how much you will enjoy a game.")
    with st.expander("How similarity is calculated"):
        st.markdown("Scores compare board-game **categories and mechanics**. "
                    "One game per series is shown by default; expand the list above to see the rest.")


# ----------------------------------------------------------------------
# PAGE 5 - BOARD GAME BESTIARY (parody personality quiz)
# ----------------------------------------------------------------------
QUESTIONS = [
    {"q": "It's Friday night. Your ideal evening is…",
     "options": [
         {"code": "WOOD", "text": "Planning the whole campaign: map, turn order, backup plans"},
         {"code": "SHARK", "text": "Friends, snacks, loud laughter, zero planning"},
         {"code": "DEER", "text": "Same table, same time, same rituals as every Friday"},
         {"code": "CROC", "text": "Whatever happens, happens. Chaos is the plan"},
     ]},
    {"q": "A new game catches your eye. What hooks you first?",
     "options": [
         {"code": "WOOD", "text": "The mechanics — how deep is the strategy?"},
         {"code": "SHARK", "text": "The vibe — will it make people laugh?"},
         {"code": "DEER", "text": "The rulebook — is it airtight and fair?"},
         {"code": "CROC", "text": "The weirdest thing about it. Break it immediately."},
     ]},
    {"q": "During a game night you are usually the one who…",
     "options": [
         {"code": "WOOD", "text": "Builds the best engine and plans three turns ahead"},
         {"code": "SHARK", "text": "Keeps the energy up and the snacks coming"},
         {"code": "DEER", "text": "Remembers the exact rules and calls them out"},
         {"code": "CROC", "text": "Finds the loophole and exploits it for the lulz"},
     ]},
    {"q": "Your friend is about to lose badly. You…",
     "options": [
         {"code": "WOOD", "text": "Quietly calculate if you can still turn the whole game"},
         {"code": "SHARK", "text": "Distract everyone with a joke to soften the blow"},
         {"code": "DEER", "text": "Remind them of the rules that led them there"},
         {"code": "CROC", "text": "Pile on. Victory is victory."},
     ]},
    {"q": "Pick your ideal game night length:",
     "options": [
         {"code": "WOOD", "text": "Three hours of epic, layered strategy"},
         {"code": "SHARK", "text": "Twenty minutes. Then on to the NEXT one"},
         {"code": "DEER", "text": "Starts at 18:00 sharp. Ends at 21:00 sharp."},
         {"code": "CROC", "text": "Until someone falls asleep at the table"},
     ]},
    {"q": "Your game shelf at home looks like…",
     "options": [
         {"code": "WOOD", "text": "Colour-coded and organised by complexity"},
         {"code": "SHARK", "text": "Whatever boxes are within reach"},
         {"code": "DEER", "text": "Alphabetical. Every insert back in place."},
         {"code": "CROC", "text": "A beautiful, chaotic pile of half-opened boxes"},
     ]},
    {"q": "Someone suggests a house rule. You…",
     "options": [
         {"code": "WOOD", "text": "Analyse how it changes the balance, then vote"},
         {"code": "SHARK", "text": "Try it immediately if it sounds fun"},
         {"code": "DEER", "text": "Decline. The rulebook is the rulebook."},
         {"code": "CROC", "text": "Invent three more house rules on the spot"},
     ]},
    {"q": "The game ends. You…",
     "options": [
         {"code": "WOOD", "text": "Review the scoresheet and plan your rematch"},
         {"code": "SHARK", "text": "Start the next round before the box is closed"},
         {"code": "DEER", "text": "Pack everything up correctly. Perfectly."},
         {"code": "CROC", "text": "Ask the score. Remember it wrong. Laugh anyway."},
     ]},
]

# 4 creatures (Italian Brainrot / "foreign Shan Hai Jing" meme beasts):
# name, description, and the categories we use to recommend real games
# from OUR dataset for them.
TYPES = {
    "WOOD": {"name": "Tung Tung Tung Tung Sahur — The City Builder",
             "desc": "You plan three moves ahead while the others are "
                     "still reading the rules. You build, you optimise, "
                     "you win — or at least you have a spreadsheet "
                     "about it. The city grows because YOU say so.",
             "cats": ["Economic", "City Building", "Civilization"]},
    "SHARK": {"name": "Tralalero Tralala — The Beach Party Animal",
              "desc": "Three legs, one sneaker on each, zero cares. "
                      "You're here to laugh, shout and make sure nobody "
                      "goes home bored. The scoreboard is a suggestion.",
              "cats": ["Party Game", "Action / Dexterity", "Word Game"]},
    "DEER": {"name": "Luguanluguan — The Rule Sheriff",
             "desc": "The time is NOW. The rules are THE RULES. You "
                     "enforce the official rulebook like a sacred text "
                     "and your table starts exactly on time. LUGUAN "
                     "LUGUAN, TIME IS UP.",
             "cats": ["Abstract Strategy", "Deduction"]},
    "CROC": {"name": "Bombardino Crocodillo — The Bombardier",
             "desc": "A crocodile head on a bomber. You don't follow "
                     "the meta — you create the chaos, then laugh at "
                     "the wreckage. Some call it unfair. You call it "
                     "a Tuesday.",
             "cats": ["Dice", "Wargame", "Fighting"]},
}

# one-line trait per creature, used for the short results summary
TRAITS = {
    "WOOD": "plans three moves ahead",
    "SHARK": "keeps the party going",
    "DEER": "knows the rulebook by heart",
    "CROC": "brings the chaos",
}


def _trait_summary_codes(scores: dict) -> list:
    """2-3 creature codes with the highest answer counts (real answers)."""
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    picked = [c for c, s in ranked[:2] if s > 0] or [ranked[0][0]]
    return picked


def _bestiary_picks(games: pd.DataFrame, code: str, cats: list) -> pd.DataFrame:
    """Quality-gated, series-deduplicated recommendations for a creature.

    - Quality gate: users_rated >= 100 and a real average rating (the same
      policy used by the Home/Find pages).
    - Ranking: Bayesian average (BGG's small-sample-corrected quality score)
      so a handful of 10.00 votes cannot dominate the list.
    - Series dedup: one game per series (e.g. one Jenga, one Brass), so the
      three picks are actually different games.
    - Party creatures (SHARK) prefer games that seat at least 3 players;
      if that leaves fewer than 3, the pool is topped up honestly.
    """
    base = games[(games["top_category"].isin(cats))
                 & (games["users_rated"] >= 100)
                 & (games["avg_rating"].notna())].copy()
    if len(base) == 0:
        return base
    pool = base.copy()
    pool["_series"] = pool["name"].apply(_series_key)
    if code == "SHARK":
        # Prefer group games before deduplicating series. Only then fill any
        # remaining slots with smaller-player games; a second global rating
        # sort would otherwise undo the stated multiplayer preference.
        pool["_group_play"] = pool["max_players"].ge(3).fillna(False)
        pool = pool.sort_values(["_group_play", "bayes_rating"],
                                ascending=[False, False], kind="stable")
    else:
        pool = pool.sort_values("bayes_rating", ascending=False, kind="stable")
    pool = pool.drop_duplicates("_series")
    return pool.head(3)


def _bestiary_card_html(g: pd.Series, reason: str) -> str:
    """One game card for the results grid (pure HTML so the grid can
    auto-fit columns; missing fields collapse into one honest line)."""
    meta_parts = [f'<span class="score-strong">{g["avg_rating"]:.2f}</span> '
                  f'BGG · {int(g["users_rated"]):,} ratings']
    players = _players(g)
    if players != "n/a":
        meta_parts.append(f"{players} players")
    if pd.notna(g["playing_time_min"]) and g["playing_time_min"] > 0:
        meta_parts.append(f'{g["playing_time_min"]:.0f} min')
    else:
        meta_parts.append("playtime unavailable")
    meta = " · ".join(meta_parts)

    tags = []
    if pd.notna(g["complexity_weight"]):
        tags.append(f'<span class="neutral-tag">complexity '
                    f'{g["complexity_weight"]:.1f}/5</span>')
    tags.append(f'<span class="neutral-tag">{escape(str(g["top_category"]))}</span>')
    gid = str(int(g["game_id"]))
    return (f'<div class="bestiary-result-game">'
            f'<div style="text-align:center;margin-bottom:10px">'
            f'{_cat_art(g["top_category"], 56)}</div>'
            f'<div class="game-card__title">{escape(str(g["name"]))}</div>'
            f'<div class="game-card__meta">{meta}</div>'
            f'<div class="tag-row">{"".join(tags)}</div>'
            f'<div class="bestiary-reason">{escape(reason)}</div>'
            f'<div class="game-card__action">'
            f'<a href="https://boardgamegeek.com/boardgame/{gid}" '
            f'target="_blank" rel="noopener noreferrer">View on BGG ↗</a></div>'
            f'</div>')


def _render_quiz_question(idx, total, mbti_icons):
    item = QUESTIONS[idx]
    options = item["options"]
    codes = [option["code"] for option in options]
    labels = {option["code"]: f"{chr(65+i)}. {option['text']}" for i, option in enumerate(options)}
    mascot_html = f'<div class="quiz-mascot">{_cat_art("Fantasy", 52)}</div>'
    mascot = mbti_icons / "main.png"
    if mascot.exists():
        import base64
        try:
            b64 = base64.b64encode(mascot.read_bytes()).decode("ascii")
            mascot_html = (f'<img class="quiz-mascot" src="data:image/png;base64,{b64}" '
                           'alt="Board Game Bestiary mascot"/>')
        except OSError:
            pass
    cells = []
    for i in range(total):
        state = "done" if i < idx else "current" if i == idx else ""
        cells.append(f'<div class="quiz-cell {state}"></div>')

    with st.container(key="bestiary_quiz"):
        st.markdown(f'<div class="quiz-head">{mascot_html}<div class="quiz-meta">'
                    f'<div class="quiz-step">Question {idx+1} of {total}</div>'
                    f'<div class="quiz-grid">{"".join(cells)}</div></div></div>'
                    f'<div class="quiz-question">{escape(item["q"])}</div>', unsafe_allow_html=True)
        previous = st.session_state["mbti_answers"].get(idx)
        selection = st.radio("Choose one answer", codes,
                             index=codes.index(previous) if previous in codes else None,
                             format_func=lambda code: labels[code],
                             key=f"mbti_answer_{idx}", label_visibility="collapsed")
        if selection is not None:
            st.session_state["mbti_answers"][idx] = selection
        with st.container(key="quiz_actions"):
            back, forward = st.columns(2)
            with back:
                if idx > 0 and st.button("← Previous", key="mbti_prev", width="content"):
                    st.session_state["mbti_idx"] = idx - 1
                    st.rerun()
            with forward:
                label = "Reveal my creature" if idx == total-1 else "Next →"
                if st.button(label, key="mbti_next", type="primary",
                             width="content", disabled=selection is None):
                    st.session_state["mbti_idx"] = idx + 1
                    st.rerun()
        st.markdown('<div class="quiz-note">Just for fun — your creature reflects your quiz choices.</div>',
                    unsafe_allow_html=True)


def render_bestiary(games: pd.DataFrame, mbti_icons) -> None:
    st.title("Board Game Bestiary")
    st.write(
        "**Answer 8 questions** — get a fun creature and "
        "**3 real game recommendations** picked for you from our "
        f"{len(games):,}-game dataset."
    )

    # one question at a time (answers are stored in the session)
    st.session_state.setdefault("mbti_idx", 0)
    st.session_state.setdefault("mbti_answers", {})

    idx = st.session_state["mbti_idx"]
    total = len(QUESTIONS)

    if idx < total:
        _render_quiz_question(idx, total, mbti_icons)
        return

    # ---------- results: wide independent container (NOT the quiz card) ----
    scores = {"WOOD": 0, "SHARK": 0, "DEER": 0, "CROC": 0}
    for _, code in st.session_state["mbti_answers"].items():
        scores[code] += 1
    order = ["WOOD", "SHARK", "DEER", "CROC"]
    code = max(order, key=lambda c: scores[c])
    t = TYPES[code]

    # "Tralalero Tralala — The Beach Party Animal" -> creature name + title
    parts = t["name"].split(" — ", 1)
    creature_name = parts[0]
    creature_title = parts[1] if len(parts) > 1 else t["name"]

    # per-creature art (140-180px), fall back to the shared mascot
    import base64
    icon_html = ""
    for cand in (mbti_icons / f"{code}.png", mbti_icons / "main.png"):
        if cand.exists():
            try:
                b64 = base64.b64encode(cand.read_bytes()).decode("ascii")
                icon_html = (f'<img class="bestiary-creature-img" '
                             f'src="data:image/png;base64,{b64}" '
                             f'alt="{creature_name}"/>')
            except OSError:
                icon_html = ""
            break

    if not icon_html:
        icon_html = f'<div class="bestiary-creature-img">{_cat_art(t["cats"][0], 144)}</div>'

    # 2-3 short traits from the actual answers
    trait_codes = _trait_summary_codes(scores)
    trait_tags = "".join(
        f'<span class="bestiary-tag">{TRAITS[c]}</span>'
        for c in trait_codes)

    st.markdown(
        f'<div class="bestiary-result">'
        f'<div class="bestiary-hero">{icon_html}'
        f'<div class="bestiary-hero-text">'
        f'<div class="bestiary-step">Quiz complete · your creature</div>'
        f'<div class="bestiary-creature-title">{creature_title}</div>'
        f'<div class="bestiary-creature-name">{creature_name}</div>'
        f'<div class="bestiary-creature-desc">{t["desc"]}</div>'
        f'<div class="tag-row">{trait_tags}</div>'
        f'</div></div></div>',
        unsafe_allow_html=True,
    )

    st.subheader("Games to try")
    picks = _bestiary_picks(games, code, t["cats"])
    if len(picks) == 0:
        st.warning("We couldn't find games that match this creature's themes "
                   "with at least 100 BGG ratings. Try another quiz or see "
                   "all games on Find a game.")
    else:
        why = (f"Picked from games that match your creature's themes "
               f"({', '.join(t['cats'])}), with rating-count checks — "
               f"BGG's Bayesian rating keeps small-sample 10.00s from "
               f"crowding out real quality.")
        if len(picks) < 3:
            why += f" Only {len(picks)} game" + ("s" if len(picks) > 1 else "") \
                   + " passed the quality gate."
        st.markdown(
            f'<div class="bestiary-why">{why}</div>',
            unsafe_allow_html=True,
        )

        # reason per card, honest and data-backed
        cards = []
        for _, g in picks.iterrows():
            cats_hit = [c for c in t["cats"] if c == g["top_category"]]
            reason = (f"Matches your creature's {cats_hit[0]} theme"
                      if cats_hit
                      else f"From the {g['top_category']} family")
            if code == "SHARK" and pd.notna(g["max_players"]):
                if g["max_players"] >= 3:
                    reason += f" · seats up to {int(g['max_players'])} for group play"
                else:
                    reason += f" · a smaller-table alternative for up to {int(g['max_players'])}"
            cards.append(_bestiary_card_html(g, reason))
        st.markdown(
            f'<div class="game-grid bestiary-result-games">{"".join(cards)}</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    if st.button("🎯 Adjust players & playtime on Find a game",
                 width="stretch"):
        switch_to("find")

    share = (f"My board game creature is {creature_title}! "
             f"🎲 What's yours?")
    st.text_input("Share your result:", value=share)
    st.caption("Copy that line and send it to your group chat 😄")

    if st.button("🔄 Find another creature",
                 width="stretch"):
        st.session_state["mbti_idx"] = 0
        st.session_state["mbti_answers"] = {}
        for key in list(st.session_state):
            if key.startswith("mbti_answer_") or key.startswith("mbti_opt_"):
                st.session_state.pop(key, None)
        st.rerun()