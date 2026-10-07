"""
part2_explore.py - Ezeme Onyenezi Innocent's part: the interactive "Explore the data" page
===========================================================================
Task checklist:
  1. Every chart must react to the filters. In particular the category
     boxplot must follow the "Categories to compare" multi-select.
  2. Check the legend logic: non-top categories collapse into "Other".
  3. An empty filter selection must degrade gracefully (a message, not
     an error).

This file is imported by webapp/app.py:
    from part2_explore import render_explore
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Warm palette, shared with the app theme.
# Kept local to this file so each part stays self-contained.
PALETTE = ["#A94F35", "#C97B63", "#7A8B6F", "#C8A45C", "#8C4A36",
           "#6B706A", "#9A8260", "#A9A9A1", "#B5634C", "#7D7D75",
           "#5E5D59"]


def _style(fig, palette=None):
    """Apply the app-wide chart style (white plot area, pale grid).

    One place to control how every chart looks. Call it right after
    creating a figure, before extra layout tweaks.
    """
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Space Grotesk, system-ui, sans-serif",
                  size=14, color="#293027"),
        title_font=dict(
            family="Space Grotesk, system-ui, sans-serif",
            size=16, color="#262B2B"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=32, r=24, t=56, b=42),
        title_x=0.02,
        legend=dict(font=dict(size=12), bgcolor="rgba(0,0,0,0)"),
        colorway=palette or PALETTE,
        height=360,
    )
    fig.update_xaxes(gridcolor="#EFEDE5", linecolor="#D8D3C8",
                     zeroline=False, title_font=dict(size=12),
                     tickfont=dict(size=13), automargin=True)
    fig.update_yaxes(gridcolor="#EFEDE5", linecolor="#D8D3C8",
                     zeroline=False, title_font=dict(size=12),
                     tickfont=dict(size=13), automargin=True)
    return fig


def render_explore(games, research_palette) -> None:
    st.title("Explore the data")
    st.write(f"Explore {len(games):,} base games. Filter the collection, "
             "hover for details and zoom in on what interests you.")

    top_cats = games["top_category"].value_counts().head(10).index.tolist()
    # A category keeps the same colour after filtering and in every chart.
    colours = {cat: research_palette[i % len(research_palette)]
               for i, cat in enumerate(top_cats)}
    colours["Other"] = "#909080"

    defaults = {"f_year": (1990, 2026), "f_comp": (1.0, 5.0), "f_solo": False}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    def reset_filters():
        # Assign through the callback so Streamlit also updates the browser.
        # Widgets below omit a second explicit default.
        for key, value in defaults.items():
            st.session_state[key] = value

    # ---------------- global filters (year / complexity / solo) ----------------
    with st.container(key="explore_filters"):
        with st.container(key="explore_filter_header"):
            t1, t2 = st.columns([3, 1])
            with t1:
                st.markdown(
                    '<div class="panel-title">Filters</div>',
                    unsafe_allow_html=True)
            with t2:
                st.button("Reset filters", key="f_reset",
                          type="secondary", on_click=reset_filters)

        # controls row: two wide ranges + one narrow solo toggle
        with st.container(key="explore_controls"):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                year_range = st.slider("Release year", 1950, 2026,
                                       step=1, key="f_year")
            with fc2:
                comp_range = st.slider("Complexity range", 1.0, 5.0,
                                       step=0.5, key="f_comp")
            with fc3:
                solo_only = st.checkbox("Solo-playable only", key="f_solo")

    # filtered dataset used by all charts
    d = games[
        games["year_published"].between(*year_range)
        & games["complexity_weight"].between(*comp_range)
        & games["avg_rating"].notna()
    ].copy()
    if solo_only:
        d = d[d["is_solo"] == 1]
    # keep the legend readable: non-top categories become "Other"
    d["cat_plot"] = d["top_category"].where(d["top_category"].isin(top_cats),
                                            "Other")

    # prominent filter summary (white surface, normal state, not a banner)
    st.markdown(
        f'<div class="summary-bar">Showing <b>{len(d):,} of '
        f'{len(games):,}</b> games &nbsp;·&nbsp; year '
        f'{year_range[0]}–{year_range[1]} &nbsp;·&nbsp; complexity '
        f'{comp_range[0]:.1f}–{comp_range[1]:.1f}'
        f'{" &nbsp;·&nbsp; solo only" if solo_only else ""}</div>',
        unsafe_allow_html=True,
    )

    with st.expander("Dataset summary & data notes"):
        med_rating = games["avg_rating"].median()
        med_time = games["playing_time_min"].median()
        miss_time = int(games["playing_time_min"].isna().sum())
        miss_comp = int(games["complexity_weight"].isna().sum())
        st.markdown(
            f"- **{len(games):,} base games** in the cleaned dataset "
            f"(expansions/re-implementations removed).\n"
            f"- Median BGG rating **{med_rating:.2f}/10**; median playtime "
            f"**{med_time:.0f} min**; **{games['top_category'].nunique()}** "
            f"top categories.\n"
            f"- Missing values: **{miss_time:,}** games have no listed "
            f"playtime, **{miss_comp:,}** have no complexity (BGG stores "
            f"'no data' as 0 — we converted those to missing).\n"
            f"- Each game is grouped by its first listed category in these charts."
        )

    if d.empty:
        st.info("No games match these filters. Widen the ranges or reset the filters above.")
        return

    # ---------------- 1. rating histogram ----------------
    st.subheader("Ratings")
    fig1 = px.histogram(
        d, x="avg_rating", nbins=24,
        labels={"avg_rating": "BGG rating",
                "count": "Number of games"},
        title="BGG rating distribution",
        color_discrete_sequence=[research_palette[0]])
    _style(fig1, research_palette)
    fig1.update_layout(bargap=0.05)
    fig1.update_yaxes(title_text="Number of games")
    st.plotly_chart(fig1, width="stretch")
    st.caption(f"N = {len(d):,} games in the current filter range. "
               "Hover a bar for the exact count; drag to zoom, double-click "
               "to reset; camera icon = download PNG.")

    # ---------------- 2. complexity vs rating scatter ----------------
    st.subheader("Complexity vs rating")
    fig2 = px.scatter(
        d, x="complexity_weight", y="avg_rating", color="cat_plot",
        hover_name="name", size="users_rated", opacity=0.72,
        labels={"complexity_weight": "Complexity (1–5)",
                "avg_rating": "BGG rating", "cat_plot": "Category"},
        title="Complexity and BGG rating",
        category_orders={"cat_plot": [*top_cats, "Other"]},
        color_discrete_map=colours)
    _style(fig2, research_palette)
    fig2.update_layout(height=500, margin=dict(b=100),
                       legend=dict(orientation="h", yanchor="top", y=-0.2,
                                   x=0, title_text="", maxheight=120,
                                   font=dict(size=12), entrywidth=110))
    fig2.update_traces(marker=dict(sizemin=4))
    st.plotly_chart(fig2, width="stretch")
    st.caption(f"N = {len(d):,} games with both complexity and rating "
               "recorded. Larger dots represent more ratings. "
               "Click a legend entry to show/hide that category; "
               "scroll the legend to see more categories on a small screen.")

    # ---------------- 3. category box comparison (local selection) ----------------
    st.subheader("Rating by category")
    if "f_cats_local" not in st.session_state:
        st.session_state["f_cats_local"] = top_cats[:3]

    def reset_categories():
        st.session_state["f_cats_local"] = top_cats[:3]

    with st.container(key="category_filters"):
        with st.container(key="category_filter_header"):
            cb1, cb2 = st.columns([3, 1])
            with cb1:
                sel_cats = st.multiselect("Categories to compare", top_cats,
                                          key="f_cats_local")
            with cb2:
                st.button("Reset categories", key="f_cats_reset", on_click=reset_categories)
    st.caption("Compare your selected categories within the current filters.")
    if sel_cats:
        d3 = d[d["top_category"].isin(sel_cats)]
        available_cats = [cat for cat in sel_cats
                          if (d3["top_category"] == cat).any()]
        missing_cats = [cat for cat in sel_cats if cat not in available_cats]
        if d3.empty:
            st.info("Your selected categories have no games in the current filters. "
                    "Choose another category or widen the filters above.")
        else:
            fig3 = px.box(
                d3, y="top_category", x="avg_rating", color="top_category",
                orientation="h", category_orders={"top_category": available_cats},
                labels={"top_category": "Category",
                        "avg_rating": "BGG rating"},
                title="Ratings by category",
                color_discrete_map=colours)
            _style(fig3, research_palette)
            fig3.update_layout(showlegend=False, height=max(320, 54 * len(available_cats) + 110))
            st.plotly_chart(fig3, width="stretch")
            st.caption(f"N = {len(d3):,}. Box = middle 50% of games, line inside "
                       "= median. Each game is grouped by its first listed category.")
            if missing_cats:
                st.caption("No games within these filters: " + ", ".join(missing_cats) + ".")
    else:
        st.info("Pick at least one category above to compare ratings.")

    # ---------------- 4. growth over time ----------------
    st.subheader("Growth over time")
    dec = d[d["decade"] > 0]["decade"].value_counts().sort_index()
    if len(dec):
        fig4 = px.bar(
            x=dec.index.astype(str), y=dec.values,
            labels={"x": "Decade", "y": "Number of games"},
            title="Releases by decade",
            color_discrete_sequence=[research_palette[0]])
        _style(fig4, research_palette)
        fig4.update_layout(bargap=0.2)
        st.plotly_chart(fig4, width="stretch")
        st.caption(f"N = {len(d):,} games in the current filter range.")

    # ---------------- 5. search & highlight ----------------
    st.subheader("Find a game in the data")
    search = st.text_input("Type a game name (try 'Catan' or 'Pandemic'):")
    if search:
        hit = d[d["name"].str.contains(search, case=False, na=False, regex=False)].head(5)
        if len(hit):
            fig5 = px.scatter(
                d, x="complexity_weight", y="avg_rating",
                hover_name="name", opacity=0.25,
                labels={"complexity_weight": "Complexity (1–5)",
                        "avg_rating": "BGG rating"},
                title="Matches in the collection",
                color_discrete_sequence=[research_palette[0]])
            fig5.add_trace(go.Scatter(
                x=hit["complexity_weight"], y=hit["avg_rating"],
                mode="markers+text", text=hit["name"],
                textposition="top center",
                marker=dict(color=research_palette[1], size=14),
                name="Search matches", showlegend=False))
            _style(fig5, research_palette)
            st.plotly_chart(fig5, width="stretch")
            st.caption(f"{len(hit)} matching game" + ("s" if len(hit) != 1 else "")
                       + " highlighted in purple; showing up to 5 matches.")
            st.dataframe(
                hit[["name", "year_published", "avg_rating",
                     "complexity_weight", "top_category"]].round(2),
                hide_index=True, width="stretch")
        else:
            st.info("No game matches that name in the current filter range.")
    else:
        st.caption("Search finds the game in the filtered data and highlights "
                   "it on the chart — try 'Catan'.")