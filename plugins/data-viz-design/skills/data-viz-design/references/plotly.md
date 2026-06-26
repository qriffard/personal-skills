# Plotly / Altair — interactive defaults

A reference loaded on demand. Use when the user asks for plotly, altair, bokeh, or "an interactive chart." For static charts, see `matplotlib.md`. For full apps, see `dashboards.md`.

The same principles apply: spare, dense, labeled. Interactivity is *not* a license to over-decorate.

## Plotly Express baseline

```python
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

GREY    = "#9CA3AF"
ACCENT  = "#D97706"
ACCENT2 = "#2E5A88"
TEXT    = "#1F2937"
MUTED   = "#6B7280"

# Custom theme — apply globally.
pio.templates["clean"] = go.layout.Template(
    layout=dict(
        font=dict(family="Inter, DejaVu Sans, system-ui", size=12, color=TEXT),
        title=dict(font=dict(size=16, color=TEXT), x=0, xanchor="left", pad=dict(t=10, b=10)),
        plot_bgcolor="white",
        paper_bgcolor="white",
        colorway=["#2E5A88", "#D97706", "#5A8F29", "#A03333",
                  "#7A4FA1", "#0E7C7B", "#A07E1F", "#5C5C5C"],
        xaxis=dict(
            showgrid=False, zeroline=False, showline=True, linecolor="#666",
            ticks="outside", tickcolor="#666", tickfont=dict(size=11, color=MUTED),
            title=dict(font=dict(size=11, color=MUTED)),
        ),
        yaxis=dict(
            showgrid=True, gridcolor="#eee", zeroline=False,
            showline=False, ticks="outside", tickcolor="#666",
            tickfont=dict(size=11, color=MUTED),
            title=dict(font=dict(size=11, color=MUTED)),
        ),
        legend=dict(orientation="h", y=-0.18, x=0, font=dict(size=11, color=TEXT)),
        margin=dict(l=60, r=30, t=60, b=60),
        hoverlabel=dict(bgcolor="white", font=dict(family="Inter", size=12, color=TEXT)),
    )
)
pio.templates.default = "clean"
```

## Patterns

### Action title + descriptive subtitle

Plotly's `title` accepts HTML. Use a `<br>` to layer a subtitle.

```python
fig.update_layout(
    title=dict(
        text=(
            "<b>Customer churn has risen 3.2 pts since the March price change</b>"
            "<br><span style='font-size:12px;color:#6B7280'>"
            "Monthly cohort churn, % of MAU. 95% CI shaded. n=4,217."
            "</span>"
        ),
    ),
)
```

### Source footer (as an annotation)

```python
fig.add_annotation(
    text="Source: Internal billing system, May 2026.",
    xref="paper", yref="paper", x=0, y=-0.22, xanchor="left", yanchor="top",
    showarrow=False, font=dict(size=10, color=MUTED),
)
```

### Highlight one series, mute the rest

```python
def highlight_traces(fig, highlight_name, accent=ACCENT, ground=GREY):
    for tr in fig.data:
        if tr.name == highlight_name:
            tr.line = dict(color=accent, width=2.4)
            tr.marker = dict(color=accent, size=7)
        else:
            tr.line = dict(color=ground, width=1.2)
            tr.marker = dict(color=ground, size=4)
            tr.showlegend = False
    return fig
```

Prefer in-chart annotations over legends when there are ≤4 series:

```python
fig.add_annotation(
    x=last_x, y=last_y, text=highlight_name,
    xanchor="left", yanchor="middle", xshift=8,
    showarrow=False, font=dict(color=ACCENT, size=11),
)
fig.update_layout(showlegend=False)
```

### Confidence band

```python
def add_ci_band(fig, x, lo, hi, color=ACCENT, opacity=0.15, name=None):
    fig.add_trace(go.Scatter(
        x=list(x) + list(x[::-1]),
        y=list(hi) + list(lo[::-1]),
        fill="toself", fillcolor=color, opacity=opacity,
        line=dict(width=0), hoverinfo="skip",
        name=name, showlegend=False,
    ))
```

### Small multiples (faceting)

```python
fig = px.line(
    df, x="month", y="value", color="segment",
    facet_col="region", facet_col_wrap=4,
    height=600, color_discrete_sequence=["#9CA3AF"] * len(df["segment"].unique()),
)
# Highlight the segment of interest after building.
for tr in fig.data:
    if tr.name == "Enterprise":
        tr.line.color = ACCENT
        tr.line.width = 2.4
# Strip the "facet_col=" prefix that plotly appends.
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
```

### Horizontal bar, sorted

```python
df_sorted = df.sort_values("value")
fig = go.Figure(go.Bar(
    x=df_sorted["value"],
    y=df_sorted["category"],
    orientation="h",
    marker_color=[ACCENT if c == highlight_cat else GREY for c in df_sorted["category"]],
    text=[f"{v:,.0f}" for v in df_sorted["value"]],
    textposition="outside",
    textfont=dict(color=TEXT, size=11),
    cliponaxis=False,
))
fig.update_xaxes(showticklabels=False, showline=False, ticks="")
fig.update_yaxes(showgrid=False)
fig.update_layout(margin=dict(l=140, r=80))
```

## Interactivity rules

Interactivity is a tool, not a substitute for design. Apply these:

- **No interactivity without a default state that already tells the story.** If the user has to drag a slider or hover to see the takeaway, the chart has failed for the executive audience.
- **Tooltip is for *precise values*, not for the headline finding.** Tooltips should show: the category, the value, the unit, optionally the n. Not the analysis ("This is high because…").
- **Hide the modebar** (zoom/pan controls) for executive consumption. Show it for expert tools.
  ```python
  fig.show(config={"displayModeBar": False})  # or {"displayModeBar": "hover"} for expert tools
  ```
- **Disable double-click reset** if the chart's default view is the canonical one — it's a foot-gun.
- **Avoid animation as the primary encoding.** Animation conveys change-over-time well to a focused viewer, badly to a skimmer. Provide a non-animated alternative (small multiples) for printed / paused viewing.
- **Cross-filtering between panels** (linked brushing) belongs in expert dashboards. Don't add it for executive readouts — the interaction surface is too high.

## Altair

Altair encodes the principles particularly well because its grammar makes encoding choices explicit. Baseline:

```python
import altair as alt

alt.themes.register("clean", lambda: {
    "config": {
        "view": {"stroke": "transparent"},
        "axis": {
            "domain": False, "grid": False, "labelColor": "#6B7280", "tickColor": "#666",
            "labelFontSize": 11, "titleColor": "#6B7280", "titleFontSize": 11,
        },
        "axisY": {"grid": True, "gridColor": "#eee"},
        "legend": {"labelColor": "#1F2937", "titleColor": "#6B7280"},
        "title": {"fontSize": 16, "color": "#1F2937", "anchor": "start", "offset": 12},
        "range": {"category": ["#2E5A88", "#D97706", "#5A8F29", "#A03333",
                               "#7A4FA1", "#0E7C7B", "#A07E1F", "#5C5C5C"]},
    },
})
alt.themes.enable("clean")
```

Altair's `mark_*` methods + `encoding` channels enforce the perceptual hierarchy by name: prefer `x`/`y` (position) over `size` (area) over `color` (hue). When the encoding feels wrong, the chart usually is.

## Things to refuse in interactive form

- **Carousel of charts** as a substitute for a hero. Make the choice for the reader.
- **Drill-down trees** where the user must click through levels to find a number. Show the relevant level by default.
- **Donut / pie with hover.** Hover doesn't fix the encoding problem.
- **Gauge charts** with a "speedometer" needle. Same encoding problems as pie. Use a horizontal bar with a target line.
- **Word clouds.** Encode by font size = magnitude, with random positioning. Bar chart of word counts is strictly better.
