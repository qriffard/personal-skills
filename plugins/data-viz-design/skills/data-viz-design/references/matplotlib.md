# matplotlib / seaborn — Tufte-style defaults

A reference loaded on demand. Use when the user asks for matplotlib, seaborn, or "a Python static chart." If they haven't named a library, default to matplotlib for static figures.

The goal of this reference: produce charts that look *spare, dense, and labeled* — not default matplotlib (gray box, navy bars, dense ticks) and not the seaborn `whitegrid` (heavy grid, blue palette).

## Baseline style

Set these once at the top of any plotting script.

```python
import matplotlib.pyplot as plt
import matplotlib as mpl

# Tufte-leaning rcParams. Apply once.
mpl.rcParams.update({
    "figure.figsize": (9, 5.5),          # ~1.6:1 (golden ratio) default
    "figure.dpi": 110,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",

    # Type — readable, with mixed case (Tufte: avoid all-caps).
    "font.family": "DejaVu Sans",        # swap for Inter / Source Sans / system font
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "semibold",
    "axes.titlelocation": "left",        # action titles sit at top-left, like a headline
    "axes.labelsize": 11,
    "axes.labelweight": "regular",

    # Spines: hide top and right by default.
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#666666",
    "axes.linewidth": 0.8,

    # Ticks: short, light, outside.
    "xtick.color": "#666666",
    "ytick.color": "#666666",
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "xtick.major.pad": 4,
    "ytick.major.pad": 4,

    # Grid: only if needed, pale, behind data.
    "axes.grid": False,                  # opt-in per chart
    "grid.color": "#dddddd",
    "grid.linewidth": 0.6,
    "grid.linestyle": "-",
    "axes.axisbelow": True,

    # Legend: no frame by default; prefer direct labels.
    "legend.frameon": False,
    "legend.fontsize": 10,

    # Color cycle: muted, colorblind-safer than default.
    "axes.prop_cycle": plt.cycler(color=[
        "#2E5A88", "#D97706", "#5A8F29", "#A03333",
        "#7A4FA1", "#0E7C7B", "#A07E1F", "#5C5C5C",
    ]),
})

# Standard semantic colors used across the skill:
GREY    = "#9CA3AF"   # de-emphasized series, background lines
ACCENT  = "#D97706"   # the one thing the title points at
ACCENT2 = "#2E5A88"   # secondary accent for "before vs after" / "us vs them"
TEXT    = "#1F2937"   # title and main text
MUTED   = "#6B7280"   # subtitle, footer, axis labels
```

## Recurrent patterns

### Range-frame (Tufte)

Trim axis spines to the data range. Keeps the axes informative without extending to a round number.

```python
def range_frame(ax, x, y):
    """Trim axis spines to the data range. Call after plotting."""
    ax.spines["left"].set_bounds(min(y), max(y))
    ax.spines["bottom"].set_bounds(min(x), max(x))
```

Caveat: for bar charts, *do not* trim the y-axis — the zero baseline is required.

### Action title + descriptive subtitle

```python
def title_block(ax, title, subtitle=None):
    ax.set_title(title, loc="left", pad=18, fontsize=14, weight="semibold", color=TEXT)
    if subtitle:
        ax.text(
            0, 1.02, subtitle,
            transform=ax.transAxes, ha="left", va="bottom",
            fontsize=10.5, color=MUTED,
        )
```

Example call:
```python
title_block(
    ax,
    "Customer churn has risen 3.2 pts since the March price change",
    "Monthly cohort churn, % of MAU. Shaded region is the 95% CI. n=4,217.",
)
```

### Source footer

```python
def source_footer(fig, text):
    fig.text(
        0.0, -0.04, text, ha="left", va="top",
        fontsize=9, color=MUTED, transform=fig.transFigure,
    )
```

### Highlight one series, gray the rest

```python
def highlight(ax, series_dict, highlight_key, accent=ACCENT, ground=GREY):
    """series_dict: {label: (x_array, y_array)}. Highlights one series."""
    for label, (x, y) in series_dict.items():
        if label == highlight_key:
            ax.plot(x, y, color=accent, linewidth=2.2, label=label, zorder=3)
            ax.annotate(label, xy=(x[-1], y[-1]), xytext=(6, 0),
                        textcoords="offset points", color=accent, fontsize=10, va="center")
        else:
            ax.plot(x, y, color=ground, linewidth=1.1, label=label, zorder=2)
```

### Direct labels on the end of a line

```python
def label_line_end(ax, x, y, label, color, dx=6):
    ax.annotate(label, xy=(x[-1], y[-1]), xytext=(dx, 0),
                textcoords="offset points", va="center", color=color, fontsize=10)
```

### Small multiples with shared axes

```python
def small_multiples(data_by_group, plot_fn, ncols=4, sharey=True, figsize=None):
    """data_by_group: {group_name: data}. plot_fn(ax, data, name) draws one panel."""
    n = len(data_by_group)
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(
        nrows, ncols,
        figsize=figsize or (3.0 * ncols, 2.2 * nrows),
        sharex=True, sharey=sharey,
    )
    axes = axes.flatten()
    for ax, (name, data) in zip(axes, data_by_group.items()):
        plot_fn(ax, data, name)
        ax.set_title(name, loc="left", fontsize=10.5, color=TEXT, pad=6)
        ax.tick_params(labelsize=9)
    # Hide unused axes.
    for ax in axes[n:]:
        ax.set_visible(False)
    fig.tight_layout()
    return fig, axes
```

Apply the principle: same scales, minimal chrome per panel, label only the outer edges.

### Horizontal bar chart, sorted, with end-of-bar labels

```python
def hbar_sorted(ax, labels, values, accent_idx=None, unit_format="{:,.0f}"):
    order = sorted(range(len(values)), key=lambda i: values[i])
    labels = [labels[i] for i in order]
    values = [values[i] for i in order]
    colors = [ACCENT if i == accent_idx else GREY for i in order]
    bars = ax.barh(labels, values, color=colors, height=0.7)

    # End-of-bar labels.
    for bar, v in zip(bars, values):
        ax.text(bar.get_width() + max(values) * 0.01,
                bar.get_y() + bar.get_height() / 2,
                unit_format.format(v),
                va="center", fontsize=10, color=TEXT)
    # No x-axis ticks / no x-grid — labels carry the magnitude.
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="y", left=False)
    ax.set_xlim(0, max(values) * 1.15)
```

### Confidence band

```python
def line_with_ci(ax, x, mean, lo, hi, color=ACCENT, label=None):
    ax.fill_between(x, lo, hi, color=color, alpha=0.15, linewidth=0)
    ax.plot(x, mean, color=color, linewidth=2.0, label=label, zorder=3)
```

### Slopegraph (two timepoints, many categories)

```python
def slopegraph(ax, names, values_t0, values_t1, accent=ACCENT, ground=GREY,
               accent_names=()):
    for n, a, b in zip(names, values_t0, values_t1):
        c = accent if n in accent_names else ground
        ax.plot([0, 1], [a, b], color=c, linewidth=1.6, alpha=0.9, zorder=3 if c == accent else 2)
        ax.text(-0.04, a, f"{n}  {a:,.1f}", ha="right", va="center", color=c, fontsize=10)
        ax.text( 1.04, b, f"{b:,.1f}  {n}", ha="left",  va="center", color=c, fontsize=10)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["t₀", "t₁"], color=TEXT, fontsize=10)
    for s in ("left", "right", "bottom", "top"):
        ax.spines[s].set_visible(False)
    ax.tick_params(left=False, labelleft=False, bottom=False)
    ax.set_xlim(-0.5, 1.5)
```

## Anti-defaults to override

When inheriting a script that uses defaults, fix these in order:

1. **Drop `plt.style.use('seaborn')` / `'ggplot'`.** Both bring heavy grids.
2. **Set `axes.spines.top` and `axes.spines.right` to False.**
3. **Replace any default blue bar series with `GREY` + one `ACCENT`.**
4. **Remove the legend; direct-label.**
5. **Strip trailing zeros from tick labels.** Use a `FuncFormatter`:
   ```python
   from matplotlib.ticker import FuncFormatter
   ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
   ```
6. **Limit tick count** to ~5 per axis:
   ```python
   from matplotlib.ticker import MaxNLocator
   ax.yaxis.set_major_locator(MaxNLocator(5))
   ```
7. **Replace any 45° rotated x-tick labels** with a horizontal bar chart or with abbreviated labels.

## When to use seaborn

Seaborn is fine for the *data-handling* layer (`relplot`, `displot`, `catplot` are convenient for faceting), but **disable its built-in styles**. Apply the matplotlib rcParams above *after* importing seaborn.

```python
import seaborn as sns
sns.set_theme(style="white", context="notebook", font_scale=1.0)
# Then override with the rcParams block above.
mpl.rcParams.update({...})
```

Seaborn's `whitegrid` and `darkgrid` styles violate the data-ink ratio with a heavy gridline pattern. Use `white` and add a light grid only where needed.

## Saving figures

```python
fig.savefig("figure.png", dpi=200, bbox_inches="tight", facecolor="white")
fig.savefig("figure.svg", bbox_inches="tight")   # vector for reports
```

For slides, export PNG at 200 DPI minimum. For reports, prefer SVG or PDF. For web, PNG at 1.5× to 2× the rendered size.
