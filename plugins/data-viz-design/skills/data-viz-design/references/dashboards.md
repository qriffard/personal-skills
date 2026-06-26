# Dashboards — composition and layout

A reference loaded on demand. Use when the user asks for a dashboard, Streamlit app, Dash app, KPI page, scorecard, or "a page showing X data." For single charts, see `chart-selection.md`.

A dashboard is not "a grid of charts." It is a **hierarchy** designed for a specific user, answering a specific question, with a specific level of detail at each layer.

## The museum-curator model (Andrews)

Borrowed from museum design — manages attention across the artifact.

| Layer | Purpose | Read time | What goes here |
|---|---|---|---|
| **Lobby** (top) | Orient. Single takeaway. | 5 seconds | Hero chart or KPI strip. Action headline. |
| **Galleries** (middle) | Decompose the headline. | 30 seconds | 2–5 supporting charts. Small multiples. Segmented views. |
| **Artifacts** (bottom / expandable) | Audit trail. | Minutes, for the curious | Tables, distributions, sources, methodology, raw-data link. |

**Decide the hero first.** Until you know the headline, you can't decide what supports it.

## Anatomy of a one-page dashboard

```
┌────────────────────────────────────────────────────────────────┐
│ DASHBOARD TITLE — what this is, dated.                         │
│ Big-picture headline finding (action sentence, plain English). │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│   [   HERO CHART   /   KPI STRIP   ]                          │
│   The single artifact that answers the headline.               │
│   One accent color. Action title.                              │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│ │ panel 1  │ │ panel 2  │ │ panel 3  │ │ panel 4  │ GALLERIES  │
│ │ (small   │ │ (small   │ │ (small   │ │ (small   │            │
│ │  multi)  │ │  multi)  │ │  multi)  │ │  multi)  │            │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘            │
│   Each panel answers a sub-question: "by region",              │
│   "by cohort", "by product", etc. Shared scales.               │
├────────────────────────────────────────────────────────────────┤
│   ▸ Distribution detail                                        │
│   ▸ Methodology                       (collapsible "artifacts")│
│   ▸ Source data                                                │
│                                                                │
│   Source: ... · Updated YYYY-MM-DD · n=...                     │
└────────────────────────────────────────────────────────────────┘
```

## KPI strips — when to use, how to design

A KPI strip is the right hero when:
- There are 3–6 metrics the audience tracks on a recurring cadence
- Each metric has a target or a prior period for comparison
- The audience makes "is anything off?" decisions, not deep dives

**Each KPI tile contains:**
- Metric name (small, gray)
- Current value (large, bold)
- Comparison: change vs. target / prior, signed and colored (single accent for "needs attention")
- Tiny sparkline of the last N periods (optional but useful)
- Sample size / denominator (very small, gray, in corner)

**Don't:**
- Use traffic-light colors (red/green) — colorblind-unfriendly and politically loaded
- Show 12 KPIs at once — at that point, no one of them is a "key" indicator
- Render KPIs as gauges or speedometers (encoding problems)

```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ MAU          │ │ Churn        │ │ NPS          │ │ Revenue      │
│ 4.21M        │ │  1.2%        │ │  42          │ │ $8.3M        │
│ +3.2% vs Q1  │ │ ▲ 0.3 pts ⚠  │ │  ─ flat      │ │ +1.1% vs Q1  │
│ ▁▂▂▃▅▆▇▇▆    │ │ ▁▁▁▂▃▄▆▇▇    │ │ ▆▅▆▆▆▇▆▆     │ │ ▂▃▄▄▅▅▆▆▆    │
│ n=4.21M      │ │ n=4.21M      │ │ n=2,140      │ │ n=accts      │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
                  ^accent — the one that needs attention this period
```

## Streamlit pattern

```python
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Customer Health · Q2 2026", layout="wide")

# --- LOBBY ---------------------------------------------------------
st.title("Customer Health · Q2 2026")
st.markdown(
    "**Churn has risen 3.2 pts since the March price change. "
    "Enterprise segment is driving the change; SMB is stable.**"
)

# KPI strip
k1, k2, k3, k4 = st.columns(4)
k1.metric("MAU",          "4.21M", "+3.2%")
k2.metric("Churn",        "1.2%",   "+0.3 pts", delta_color="inverse")
k3.metric("NPS",          "42",     "flat", delta_color="off")
k4.metric("Revenue (Q)",  "$8.3M",  "+1.1%")

# Hero chart
st.plotly_chart(make_hero_chart(df), use_container_width=True, config={"displayModeBar": False})

# --- GALLERIES -----------------------------------------------------
st.subheader("Where the change is coming from")
g1, g2 = st.columns(2)
with g1:
    st.plotly_chart(by_segment_panel(df),  use_container_width=True, config={"displayModeBar": False})
with g2:
    st.plotly_chart(by_region_panel(df),   use_container_width=True, config={"displayModeBar": False})

g3, g4 = st.columns(2)
with g3:
    st.plotly_chart(by_cohort_panel(df),   use_container_width=True, config={"displayModeBar": False})
with g4:
    st.plotly_chart(by_tenure_panel(df),   use_container_width=True, config={"displayModeBar": False})

# --- ARTIFACTS -----------------------------------------------------
with st.expander("Distribution detail"):
    st.plotly_chart(distribution_panel(df), use_container_width=True)
with st.expander("Methodology"):
    st.markdown(open("methodology.md").read())
with st.expander("Source data"):
    st.dataframe(df_summary)

st.caption("Source: Internal billing system. Updated 2026-05-15. n=4,217 monthly cohorts.")
```

Key choices in this pattern:
- `layout="wide"` for breathing room.
- Hero chart at full width.
- Galleries in a 2×2 (or 4×1) shared-scale grid.
- Artifacts behind `st.expander` so they don't compete for executive attention.
- One source footer at the bottom, not under every chart.

## Dash pattern

```python
from dash import Dash, dcc, html
import plotly.graph_objects as go

app = Dash(__name__)
app.layout = html.Div(
    style={"maxWidth": "1280px", "margin": "0 auto", "padding": "24px",
           "fontFamily": "Inter, system-ui"},
    children=[
        # Lobby
        html.H1("Customer Health · Q2 2026", style={"marginBottom": "4px"}),
        html.P("Churn has risen 3.2 pts since the March price change. "
               "Enterprise segment is driving the change; SMB is stable.",
               style={"color": "#374151", "marginTop": "0", "fontSize": "16px"}),

        # KPI strip
        html.Div(style={"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)",
                        "gap": "16px", "margin": "24px 0"},
                 children=[kpi_card(*k) for k in KPIS]),

        # Hero
        dcc.Graph(figure=make_hero_chart(df),
                  config={"displayModeBar": False},
                  style={"height": "420px"}),

        # Galleries
        html.H2("Where the change is coming from", style={"marginTop": "32px"}),
        html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px"},
                 children=[
                     dcc.Graph(figure=by_segment_panel(df), config={"displayModeBar": False}),
                     dcc.Graph(figure=by_region_panel(df),  config={"displayModeBar": False}),
                     dcc.Graph(figure=by_cohort_panel(df),  config={"displayModeBar": False}),
                     dcc.Graph(figure=by_tenure_panel(df),  config={"displayModeBar": False}),
                 ]),

        # Footer
        html.Hr(style={"marginTop": "32px"}),
        html.P("Source: Internal billing system. Updated 2026-05-15. n=4,217.",
               style={"color": "#6B7280", "fontSize": "12px"}),
    ],
)
```

## Composition rules

### Shared scales across small multiples
If the four gallery panels show the same metric across different cuts (region, segment, cohort), the y-axes must share scale. Otherwise the visual size of bars across panels doesn't correspond to the magnitude of values, and you've created a Lie Factor across the dashboard.

### One source of "current period"
Decide what "now" means (e.g., May 2026) at the top of the dashboard. Every chart uses the same reference. Mixing date ranges across panels confuses both audiences.

### One color logic across the dashboard
- Grey = de-emphasized series.
- Accent 1 = the thing the headline is about. Same color across every panel.
- Accent 2 (sparingly) = the comparison ("before vs after," "us vs them"). Same across panels.

When a categorical palette is needed inside a small multiple (e.g., 4 product lines on one panel), keep it confined to that panel and call it out in a small inline legend.

### Whitespace separates groups
Use whitespace as the primary divider between lobby / galleries / artifacts. Resist boxing them in. Closure (Gestalt) makes the eye complete the grouping without the box.

### Don't waste vertical space on filters above the fold
Filters belong in a sidebar (Streamlit / Dash) or at the bottom of each panel, not in a row above the hero. The hero is the first thing the eye sees; don't put a date picker there.

### Don't number panels with "Chart 1", "Chart 2"
The action title of each panel is its identity. If you find yourself reaching for chart numbers, your titles are too generic — rewrite them as findings.

## Refusals

- **Dashboards with no hero.** "Here are 12 panels, you tell me what's interesting." That's an analysis report, not a dashboard. Add a hero, or rebrand it.
- **Dashboards that paginate.** A dashboard fits on one screen (or one scroll for a long report). Pagination breaks the layered-attention contract.
- **Dashboards with filter-controlled headlines.** If the headline changes based on what the user selects, the headline isn't the headline — it's a caption. Either lock the headline (the canonical view) or rephrase it as a question.
- **Dashboards updated nightly but timestamped only "live."** Always show the last-updated date in the footer.
- **Embedded dashboards inside slides as a screenshot.** A screenshot of a dashboard pasted into a slide is invariably illegible. Build the slide chart natively at slide resolution.

## Quotable principles

- Andrews: *"To see data, we must build a visual world for it to inhabit."* — The dashboard is the world; choose it intentionally.
- Knaflic: *"Horizontal logic — read only the titles top to bottom and the story should be there."* — Applies to dashboard headings, not just slide decks.
- Tufte: *"Above all else show the data."* — Filter chrome and navigation chrome are not data.
- Cairo: *"Different levels of thinking require different levels of data aggregation."* — Lobby ≠ galleries ≠ artifacts; aggregate differently at each.
