# Principles — synthesized from Tufte, Knaflic, Cairo, Andrews

A reference loaded on demand from `SKILL.md`. Read this when you need to ground a design decision in the underlying principle, when explaining *why* a chart should change, or when teaching the user.

## Table of contents

1. Tufte — graphical excellence and integrity
2. Knaflic — context, story, decluttering
3. Cairo — honesty, uncertainty, normalization
4. Andrews — process, trust, audience empathy
5. The unified perceptual hierarchy
6. Gestalt principles in practice
7. Pre-attentive attributes
8. The Lie Factor (with worked example)
9. Trust signals
10. Synthesis: where the four authors agree and disagree

---

## 1. Tufte — graphical excellence and integrity

> "Graphical excellence is that which gives to the viewer the greatest number of ideas in the shortest time with the least ink in the smallest space."

**The five-step editing loop** (apply in order):
1. Show the data.
2. Maximize the data-ink ratio (within reason).
3. Erase non-data-ink.
4. Erase redundant data-ink.
5. Revise and edit.

**Data-ink ratio:** `data-ink / total ink used`. The fraction of ink that varies with the data. Push it toward 1.

**Graphical integrity** — the principle that *visual* size of an effect equals *data* size of the effect. Violations: 3D bars for 1D data, area circles whose radius (not area) scales linearly, truncated bar charts.

**Friendly graphics checklist** (Tufte):
- Words spelled out, no cryptic codes
- Labels directly on the graphic, not in legends
- Type set in serif, mixed case (not all caps)
- Color-blind-safe palette
- Subtle gridlines or none
- Captions integrated with the graphic, near the data they describe
- Little explanatory messages annotating interesting features

**On audience:** *"It is a frequent mistake in thinking about statistical graphics to underestimate the audience. Instead, why not assume that if you understand it, most other readers will, too? Graphics should be as intelligent and sophisticated as the accompanying text."*

---

## 2. Knaflic — context, story, decluttering

**The six lessons:**
1. Understand the context.
2. Choose an appropriate visual.
3. Eliminate clutter.
4. Focus attention where you want it.
5. Think like a designer.
6. Tell a story.

**The Big Idea** (from Duarte, used by Knaflic): one complete sentence that (a) articulates your point of view, (b) conveys what's at stake, (c) is something you'd say out loud.

**The 3-minute story:** the paragraph you'd deliver if your 30-minute slot were cut to 3.

**Decluttering checklist** (apply in order):
1. Remove chart border.
2. Remove gridlines (or make them thin and light gray if essential for lookup).
3. Remove data markers unless they communicate something.
4. Clean axis labels — drop trailing zeros, abbreviate units.
5. Label data directly; eliminate the legend.
6. Use consistent color across label and series.

**Where are your eyes drawn?** Look away from your chart, look back, and notice where your eyes land first. They should land on the message. If they land on a gridline or logo, redesign.

**Action titles, not labels.** A title is precious real estate — make it a takeaway. *"2026 spending is 8% above budget"* beats *"2026 Budget."*

---

## 3. Cairo — honesty, uncertainty, normalization

**Six failure modes** of charts that lie:
1. Poorly designed (encoding mismatched to data).
2. Dubious data (source not credible, sample biased, label misrepresents the metric).
3. Insufficient data (cherry-picked window, missing baseline).
4. Too much data (spaghetti, overload).
5. Concealed uncertainty.
6. Misleading patterns (correlation read as causation, Simpson's paradox).

**Designer's questions** (Cairo's reader-checks turned around):
- What does this chart NOT show?
- Is the scale appropriate?
- Is the source credible? Cite it.
- Rate or count? Show both when both matter.
- Compared to what?
- Unit of analysis (individual, region, country)?
- How uncertain is this? Show CI, error bars, or note "point estimate."
- Could a confounder explain it?

**Critical rules:**
- Bar charts: zero baseline, always. Encoding is length.
- Line / scatter: zero baseline optional. Encoding is position.
- Choropleth: normalize. Map population if you don't.
- Bubble charts: area ∝ value (use `r = sqrt(value/π)`), and direct-label.
- Dual axes: don't. Use indexed series (=100 at t₀) on one axis instead.
- Always show uncertainty when the data has any. *"Error is not mistake; it is uncertainty — disclose it."*

> "A chart shows only what it shows, and nothing else."

---

## 4. Andrews — process, trust, audience empathy

**The probe ↔ humanize cycle:** charts iterate. Sketch → ask establishing questions → transform (log, residuals) → re-sketch. Generative, not transcriptive. *"We draw not to transcribe ideas from our heads but to generate them."*

**Content vs. form:** content is what's true in the data. Form is how you retell it. Two separate decisions. Don't fuse them.

**The museum-curator metaphor for dashboards:** lobby (orient), galleries (decompose), artifacts (detail). The lobby is the hero chart; the artifacts are the data tables and distributions an expert can dig into.

**The seven trust signals** (in order):
1. First impressions — aesthetic quality signals care
2. Accuracy — errors destroy trust
3. Accessibility — clarity over cleverness
4. Directness — use familiar conventions
5. Transparency — show sources and limitations
6. Vulnerability — stand by your work
7. Trusting the audience — never condescend

> "We must aspire to meet readers where they already perceive the world."

> "Successful encoding yields successful decoding."

**Beauty earns trust.** Where Tufte is austere, Andrews argues care visibly invested in craft is itself a signal of analytical seriousness. Both are right at different moments — but a chart that looks "thrown together" loses executive trust before the data is read.

---

## 5. The unified perceptual hierarchy

Cleveland & McGill, accepted by all four authors. Most-accurate to least-accurate human decoding of quantitative values:

1. **Position along a common scale** (scatter, line, bar) — most accurate
2. **Position along non-aligned scales** (small multiples)
3. **Length** (bar charts)
4. **Angle / slope** (slopegraph)
5. **Area** (bubble, treemap) — gist only, label values
6. **Volume / 3D** — avoid
7. **Color hue** (categorical only, not quantitative)
8. **Color saturation** (sequential, low precision)

**Rule:** for precise comparison, encode with position or length. For gist, area / color are acceptable but require direct labels.

---

## 6. Gestalt principles (Knaflic's working set)

Use these to find what to *remove* from a chart as well as how to compose what stays.

- **Proximity** — items close together read as a group. Place labels next to their data (kills legends).
- **Similarity** — same color/shape/size implies belonging. Color a label the same as its series.
- **Enclosure** — light shading is enough to group. Shade a forecast region instead of drawing a separate panel.
- **Closure** — viewers fill gaps. You can delete a chart border and the eye still completes the rectangle.
- **Continuity** — eyes follow smooth lines. You can delete an axis line if whitespace aligns the bars.
- **Connection** — physically connecting beats colored grouping. This is why line charts work.

---

## 7. Pre-attentive attributes (Few, used by Knaflic)

Features processed before conscious attention (~250 ms):

- Orientation, shape, line length, line width, size, curvature
- Added marks (a tick or dot on a line)
- Enclosure
- Hue, intensity, spatial position
- Motion (only useful interactively)

**Quantitative encoders** (good for precise reading): line length, line width, size, intensity, spatial position.
**Categorical encoders** (good for grouping, bad for magnitude): hue, shape, orientation.

Spend at most 2 pre-attentive attributes per chart for focus. Three or more compete.

---

## 8. The Lie Factor (Tufte, exact formula)

```
Lie Factor = (size of effect shown in graphic) / (size of effect in data)
```

A Lie Factor of 1.0 is perfect integrity. Tufte considers 0.95–1.05 acceptable.

**Worked example** (Tufte's NYT fuel-economy chart):
- Data effect: 18.0 → 27.5 mpg = (27.5 − 18) / 18 = **53% increase**
- Visual effect (the line lengths he drew): 0.6 in → 5.3 in = (5.3 − 0.6) / 0.6 = **783% increase**
- Lie Factor = 783 / 53 = **14.8** → wildly exaggerated

When redesigning an existing chart, compute the Lie Factor and report it.

---

## 9. Trust signals — composite checklist

Across all four authors, the artifacts that build trust:

- Cited source + date + sample type
- Stated denominator and unit of analysis
- Visible uncertainty (CI, error bars, fan)
- Comparison / baseline shown (no naked "compared to nothing")
- Action title that names the takeaway
- One accent color, used consistently
- Distributions, not just means, when underlying data is skewed
- Spelled-out words on the chart (no cryptic codes or legends)
- Subdued gridlines, generous white space
- Annotation directly on the marks
- Aesthetic care visible (alignment, type, spacing — Andrews's first impression)

---

## 10. Synthesis — where the four agree, where they diverge

**They all agree on:**
- Zero baseline for bar charts.
- Position and length over area and angle.
- Direct labels over legends.
- Show distributions / show context.
- Avoid pie, 3D, rainbow.

**They diverge on:**
- **Density.** Tufte loves it; Knaflic prefers focus and restraint. Resolution: layer the artifact. Density in the body for experts, focus in the title and accent for executives.
- **Beauty.** Tufte minimizes ink; Andrews argues craft and beauty earn trust. Resolution: the right look is *spare, dense, and labeled* — not bare, and not decorated.
- **Annotation.** Tufte: little explanatory messages near the marks. Knaflic: bold action title plus targeted annotation. Cairo: state what the chart doesn't show. All three usable; the limit is reader cognitive load.
- **Audience.** Tufte: trust them with detail. Knaflic: design for one decision-maker. Cairo: assume they will misread the chart if you let them. Andrews: meet them where they perceive the world. For mixed exec/expert: title and hero for execs, body and footer for experts, all on the same artifact.
