# Anti-patterns — what never to ship, and why

A reference loaded on demand. Use when critiquing a chart, when the user proposes a problematic form, or when explaining why a default library output is unacceptable.

For each anti-pattern: **mechanism** (why it misleads or fails), **fix** (the smallest change that resolves it).

## Encoding anti-patterns

### Pie charts (Knaflic: "pie charts are evil")
**Mechanism.** Humans cannot accurately decode 2D angles or areas. Adjacent slices are also rotated relative to one another, defeating the perceptual hierarchy. With >3 slices, ranking becomes guesswork.
**Fix.** Sorted horizontal bar, share labels at the end of each bar. If part-to-whole emphasis matters, a single stacked horizontal bar (100%-stacked).

### Donut charts
**Mechanism.** Worse than pie: removes the angle cue and asks the eye to compare arc lengths along different radii.
**Fix.** Same as pie.

### 3D bars / 3D pies / 3D line charts
**Mechanism.** Adds two information-carrying dimensions that don't correspond to data dimensions. Tufte's principle: *"The number of information-carrying dimensions depicted should not exceed the number of dimensions in the data."* Tangent-plane intersection in Excel produces literally wrong bar heights.
**Fix.** 2D version of the same chart.

### Dual y-axes
**Mechanism.** Choice of scale on either axis fabricates apparent correlation. Reader cannot tell which series belongs to which axis without legend lookup. The Planned Parenthood "screenings vs abortions" chart is the canonical example.
**Fix.** (a) Indexed series on a single axis: divide each by its starting value × 100, so both start at 100. (b) Two stacked panels sharing the x-axis.

### Truncated bar y-axis
**Mechanism.** Bars encode by length. Cutting the baseline above zero makes a 39.6%→35% bar look 5× as different as it is. The Fox News tax-rate chart is the canonical example.
**Fix.** Zero baseline. Always.

### Truncated line y-axis (the inverse mistake)
**Mechanism.** "All charts must start at zero" is wrong. Line charts encode by position, not length. Forcing a zero baseline can flatten a meaningful 0.85°C climate anomaly into invisibility.
**Fix.** Choose the y-axis range to expose the meaningful variation. Annotate the baseline (e.g., "1951–1980 mean") so the reader understands the reference.

### Bubble charts where diameter ∝ value (not area)
**Mechanism.** Doubling the radius gives 4× the visual area. The eye perceives area. So values are exaggerated by the square of the intended ratio.
**Fix.** Area ∝ value (use `r = sqrt(value/π)`). Always direct-label bubble values; area is gist-only encoding.

### Rainbow color scales for ordered data
**Mechanism.** Rainbow is non-monotonic in perceived brightness, so it implies false categorical boundaries. Red-yellow regions seem qualitatively different from green-blue.
**Fix.** Sequential single-hue or perceptually uniform palettes (viridis, magma, plasma, cividis).

### Choropleth of raw counts
**Mechanism.** The map shows population, not the phenomenon. Cook County leads in any raw-count map because Chicago is there.
**Fix.** Normalize: rate per capita, per area, per relevant denominator. If denominator is ambiguous, use a cartogram weighted by population.

### Area encoding for precise comparison
**Mechanism.** Sixth on the perceptual hierarchy. Eyes systematically underestimate large areas.
**Fix.** Encode with length or position instead. If you must use area (treemap, bubble), always include direct value labels.

## Composition anti-patterns

### Chartjunk: dark dominating gridlines
**Mechanism.** Steals attention from data. Reduces data-ink ratio.
**Fix.** Light gray gridlines, or none. Use whitespace to align bars instead of grid.

### Chartjunk: moiré patterns
**Mechanism.** Cross-hatching and dense pattern fills "shimmer" — eye strain, no information value.
**Fix.** Solid gray fills at varying intensity.

### Chartjunk: decorative "ducks"
**Mechanism.** Named for the duck-shaped building. The chart's form becomes its own subject (illustrated bars, animated transitions on static reports, glow effects, gradient fills).
**Fix.** Plain rectangles. Beauty is in proportion and alignment, not ornament.

### Too many overlapping series ("spaghetti")
**Mechanism.** Five or more lines on one axes are individually unreadable; the reader gets gist of "stuff is happening" but cannot extract a specific value.
**Fix.** Small multiples (one panel per series, shared axes) for systematic comparison. Highlight chart (one bold, rest gray) when one series is the subject.

### Legends instead of direct labels
**Mechanism.** Forces a saccade between data and legend for every value the reader inspects. Multiplies cognitive load.
**Fix.** Place the series label at the end of the line, or under the bar, in the same color.

### Diagonal x-axis labels (45° rotation)
**Mechanism.** Read ~52% slower than horizontal text (Knaflic citing readability research).
**Fix.** Horizontal bar chart (so labels are naturally horizontal), or use fewer / abbreviated x-axis categories.

### Vertical y-axis title (rotated 90°)
**Mechanism.** Read ~205% slower than horizontal text.
**Fix.** Place the y-axis unit in the chart title or above the y-axis as horizontal text.

### Chart border that frames the plot area
**Mechanism.** Non-data ink. Encloses the chart visually but adds nothing. Combined with internal gridlines, the chart looks heavy and cluttered.
**Fix.** Remove. Closure (Gestalt) lets the eye complete the rectangle.

## Statistical anti-patterns

### Showing the mean alone, when the data is skewed
**Mechanism.** "The average family saves $1,182" hides that the distribution is heavy-tailed. The median family saves much less.
**Fix.** Show distribution (histogram, dot strip, box). At minimum: median + p10/p90 in a small text table.

### Cherry-picked time window
**Mechanism.** Choose a start date that produces the trend you want. Krugman's murder chart stopping at 2014; political "since I took office" charts.
**Fix.** Default time window: include enough history to see the pre-existing trend. Annotate the start of the period if you have to cite it.

### Aggregate-only chart when a confounder reverses the story (Simpson's paradox)
**Mechanism.** Aggregating across groups hides a confounding variable. The aggregate trend can be the opposite of the within-group trend (UC Berkeley admissions; smoking-vs-life-expectancy).
**Fix.** Disaggregate. If aggregate and disaggregate tell different stories, show both.

### Ecological fallacy
**Mechanism.** Inferring about individuals from group-level data. "Countries that smoke more live longer" does not mean "smoking helps."
**Fix.** State the unit of analysis explicitly (country, county, individual). Use small multiples to show within-group patterns.

### Naked point estimates (no uncertainty shown)
**Mechanism.** A crisp line implies precision the data doesn't have. Reader treats the chart as gospel.
**Fix.** Confidence bands on time series. Error bars on bars (use sparingly — they clutter at high counts). Fan charts for forecasts. If uncertainty cannot be quantified, label "point estimate" in the footer.

### Correlation drawn as causation
**Mechanism.** A scatter with a regression line invites a causal read. Spurious correlations on dual axes invite it harder.
**Fix.** Annotate plausible confounders. State the direction of inference you're claiming. Show a residual plot if relevant.

### Map projection that distorts the property being shown
**Mechanism.** Mercator inflates polar regions. A Mercator world map of GDP misleads about high-latitude countries.
**Fix.** Equal-area projection (Equal Earth, Mollweide, Albers) for prevalence/density maps.

## Audience-targeting anti-patterns

### Descriptive title ("2026 Budget")
**Mechanism.** Wastes the most prominent text on the page. Doesn't move a decision. Reader must work to extract the takeaway.
**Fix.** Action title: state the finding. "2026 spending tracking 8% above budget."

### Hedged action title ("Spending may be tracking somewhat above budget, pending review")
**Mechanism.** Conveys uncertainty about the *finding*, not about the data, which is what uncertainty bands are for. Communicates lack of conviction.
**Fix.** State the finding plainly in the title. Show uncertainty in the chart (CI band, error bar). The two channels are independent.

### Color used as decoration
**Mechanism.** Three or more accent colors compete; none catches the eye. Reader doesn't know what to look at.
**Fix.** Gray default + one accent color used consistently for the thing that matters.

### Color reused with different meanings on the same page
**Mechanism.** Blue means "current" in chart 1 and "Europe" in chart 2 — the reader has to remember context per panel.
**Fix.** Consistent semantic palette across an artifact. Reserve one color for one meaning.

### No source / no date
**Mechanism.** Reader can't verify, can't reproduce, can't trust.
**Fix.** Source, access date, sample type in small gray text at the bottom. Always.

### Decimal places that imply false precision
**Mechanism.** "Population per 1,000: 14.32" implies precision the survey doesn't support. Worse: percentages on counts of people produce literal fractional people.
**Fix.** Match the rendered precision to the data precision. Round to the precision the decision needs.

## Single most-common violations (in order)

These are the ones to flag immediately when critiquing a chart:

1. Descriptive title instead of action title
2. No uncertainty shown
3. Pie chart (or any of: donut, 3D, dual y-axis)
4. Truncated bar baseline
5. Gridlines too dark
6. Legend instead of direct labels
7. Color used as decoration (three or more accents)
8. No source / no date / no denominator
9. Raw counts on a choropleth
10. Mean only, with no distribution shown
