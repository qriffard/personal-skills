---
name: find-research-papers
description: Search the internet for recent research papers relevant to the user's interests, where interests are derived from one of the user's LLM Wikis under ~/wikis/. Trigger on "find papers", "any new research on X", "search for papers related to my interests", "what's new in <topic>", or any request to discover research literature. Renders a ranked digest as a local self-contained HTML page (opened in the browser), with an optional on-demand "deep dive" that reads a chosen paper (via a subagent) and appends an idea diagram + mechanism explanation — it does not ingest anything.
---

# Find research papers

Discover recent research papers relevant to the user, using one of their LLM Wikis as the source of "interests", and present a ranked digest. This skill **only presents** — it never writes to a wiki or ingests. If the user wants to save a hit, they invoke `use-llm-wiki` separately.

## Workflow

### Step 1 — Ask which wiki

The interests always come from a wiki. List the vaults under `~/wikis/` (currently `ai-research`, `zoox`) and ask which one to base the search on. Do not guess — the same request means different papers depending on the vault.

If the user already named a topic in their request (e.g. "find papers on speculative decoding"), still confirm which wiki to anchor relevance against, then treat their topic as the primary query and the wiki as supporting context.

### Step 2 — Derive interests from that wiki

Read, in order, only as much as you need:

1. `~/wikis/<vault>/_hot.md` — the hot cache; current working focus.
2. `~/wikis/<vault>/index.md` — master index and "Recently Active".
3. 1–2 relevant `_index-<domain>.md` sub-indexes if the request points at a specific area.

From these, extract 3–6 concrete **core** search topics/keywords (methods, model families, problem areas).

Then derive 2–3 **adjacent** topics — deliberately one step outside the current scope, chosen to expand it. Good adjacencies: a neighboring subfield that shares methods (e.g. RL ↔ control theory), the same technique applied in another domain, an upstream/downstream part of the pipeline the wiki doesn't yet cover, or a competing paradigm to what the wiki favors. Avoid topics so far out they're unrelated — the goal is reachable expansion, not noise.

Show the user both lists in one line (`core: … | adjacent: …`) before searching, so they can redirect. Keep it to keywords — do **not** paste wiki contents into any outbound request.

### Step 3 — Search the three sources

Run these in parallel, issuing queries for **both** the core and adjacent topics (tag each result with which topic it came from so you can separate them in Step 4).

**Cover both recency bands deliberately** — a single relevance-sorted query skews toward older, well-cited work and misses fresh preprints. For each topic, run it twice:
- once `sortBy=relevance` (surfaces the established, canonical papers), and
- once `sortBy=submittedDate&sortOrder=descending` (surfaces the last few months, however lightly cited).

Compute the **recency cutoff = today − 6 months** and record each paper's publication/submission date so Step 4 can classify it. Papers on/after the cutoff are **new**; before it are **older**. Aim to surface *both* — at least a couple of genuinely new (past-6-months) hits per section, not only the canonical older ones. arXiv id prefixes encode the month (`YYMM…`), a quick sanity check on recency.

**arXiv API** (structured, primary for ML/AI/robotics preprints):
```
curl -sLG "https://export.arxiv.org/api/query" \
  --data-urlencode "search_query=all:<keywords>" \
  --data-urlencode "start=0" \
  --data-urlencode "max_results=15" \
  --data-urlencode "sortBy=submittedDate" \
  --data-urlencode "sortOrder=descending"
```
Parse the Atom feed for title, authors, summary, published date, and the `abs` link.

**Semantic Scholar API** (citation graph + relevance ranking):
```
curl -sG "https://api.semanticscholar.org/graph/v1/paper/search" \
  --data-urlencode "query=<keywords>" \
  --data-urlencode "limit=15" \
  --data-urlencode "fields=title,authors,year,abstract,citationCount,influentialCitationCount,url,externalIds"
```
If it returns HTTP 429 (rate limit), wait a few seconds and retry once; note the throttle if it still fails.

**WebSearch** (general — catches Google Scholar, conference/workshop pages, blog write-ups, and papers not on arXiv). Run one or two `WebSearch` queries combining the top keywords with terms like "2025 paper", "arxiv", or the relevant venue (NeurIPS/ICML/ICLR/CoRL/RSS).

**Media search** (blogs/press + video/podcast — the non-paper channel). Run 2–3 more `WebSearch` queries aimed at accessible write-ups and talks on the core topics:
- Blog / press: combine keywords with terms like "blog", "explained", or likely outlets (company research blogs, `distill.pub`, `The Gradient`, `arXiv-sanity`, major tech/AV press). Prefer primary/authoritative sources over content farms.
- Video / podcast: combine keywords with "YouTube talk", "lecture", "podcast", "interview", or known series (e.g. conference keynotes, research-group channels).
Capture for each: title, outlet/channel, author or host, date if available, medium (blog / press / video / podcast), and the URL. Skip anything that's just SEO filler or a paywalled stub with no substance.

Only outbound query keywords leave the machine — never wiki file contents. These are public read-only research APIs (arXiv, Semantic Scholar) and the built-in web search; no approval needed.

**Free sources only.** Stick to arXiv + Semantic Scholar + WebSearch. Do not propose or add paid-API backends (e.g. Exa) — the user has declined subscription-gated sources for this skill.

### Step 4 — Rank, then build a local results page

Dedupe across sources (match on title / arXiv id / DOI). Split the results into two groups:

- **Core** — directly on the wiki's focus. Keep the top ~8–10, ranked by relevance, then recency, then citation signal.
- **Expand your scope** — adjacent hits. Keep 2–3, chosen for how usefully they stretch the scope (a new method, domain, or paradigm), not just raw relevance. For these, the **Why relevant** line should explain *the connection to the current scope and what it opens up*, not why it's central.

Render both groups on the page under separate headings, core first.

**Classify every paper by recency** (orthogonal to core/adjacent): compare its publication/submission date to the cutoff (today − 6 months).
- 🔥 **New** — on/after the cutoff. "Hot off the press", possibly not yet widely cited.
- **Older** — before the cutoff. Established / canonical.

Within each section, sort **New first**, then older. Give each card a visible badge (`🔥 New` vs `Older`) and show the exact publication date in the meta line so the user can see how fresh it is. The goal is to let the user tell at a glance what just dropped versus what they may have missed earlier.

For each kept paper, prepare:
- **Title**, authors (first few + et al.), exact publication date, arXiv id / venue, citation count if known, and the link.
- **Recency badge** — 🔥 New or Older, per the cutoff.
- **Summary** — 2–3 sentences on the contribution.
- **Why relevant** — one line tying it to the wiki's focus / derived topic.
- **Takeaways** — up to 5 bullet points, the concrete things worth knowing.

After the two paper sections, add a **Media & talks** section for the blog/press and video/podcast hits. These are lighter-weight than papers — one compact card each with: title (linked), outlet/channel + author/host, date, a **medium tag** (Blog / Press / Video / Podcast), the same 🔥 New / Older recency badge, and a one-line why-relevant. No formal summary or takeaways needed unless a piece is substantial. Group by medium or just sort New-first; keep to ~4–8 items total, quality over quantity. If the media search turns up nothing worthwhile, omit the section rather than padding it.

Render these into a **single self-contained HTML file** and open it in the browser. The page is local-only — no external uploads, no CDN links, all CSS inline (this both respects the no-external-transfer policy and keeps the page working offline).

1. Write the file to the session scratchpad, e.g. `<scratchpad>/research-<vault>-<YYYYMMDD-HHMM>.html`.
2. Open it: `open "<path>"` (macOS).
3. In the chat, print only a one-line pointer to the file path, a one-line note that any hit can be ingested into the `<vault>` wiki via `use-llm-wiki`, and offer the **deep dive** (Step 5). Do not re-dump the full digest as text and do not ingest automatically.

### Step 5 — Deep dive (optional, on demand)

The digest cards are built from **abstracts only** (cheap). A deep dive reads the actual paper to produce an **idea diagram + mechanism explanation** — do this **only for the papers the user picks**, never for the whole digest (cost scales with their curiosity, not the search size).

**Offload the reading to a subagent.** For each chosen paper, launch a `general-purpose` agent so the large paper text stays out of the main context — the subagent returns only a small distilled result. Scope its prompt tightly:

> Read arXiv paper `<id>` (`<title>`) and return ONLY a distilled result — do not write files, do not search.
> 1. Fetch the text cheaply: try the HTML first (`https://arxiv.org/html/<id>` or `https://ar5iv.org/abs/<id>`); fall back to the PDF (`https://arxiv.org/pdf/<id>`) extracted with `pdftotext`/`pymupdf`. If the vault has `scripts/extract-arxiv.py` or `extract-pdf.py`, use it.
> 2. Read ONLY abstract + introduction + the core method section + figure captions. Do NOT read related-work, experiments tables, or appendices.
> 3. Return: (a) **mechanism** — 150–250 words explaining how the idea actually works, plain language; (b) **diagram** — 3–6 stages of the idea as an ordered flow, each a short `label` + one-line `detail`, plus the arrows between them (linear `A→B→C`, or note any branch/loop). Keep it to the essential pipeline, not every detail.

Then **render each returned deep dive as a new card appended to the page** (regenerate the HTML, or append before `</body>` and re-open): the mechanism paragraph plus an **offline CSS box-and-arrow diagram** built from the returned stages — use the `.pipeline` / `.flow-node` / `.flow-arrow` pattern in the template. **No Mermaid, no CDN, no JS** — pure CSS/HTML so the page stays self-contained.

Keep the subagent's returned payload small (~400–600 tokens); that distillation is the whole point — the main conversation pays for the compact output, not the ~15k-token paper.

**Use the bundled template** `templates/digest-template.html` — copy it and fill the `{{PLACEHOLDERS}}`; don't hand-roll the CSS. It carries the Zoox visual-explainer aesthetic: light/dark CSS custom properties, a gradient-mesh background, a hero header, a KPI summary row (New / Core / Adjacent / Media counts), monospace section labels, depth-tiered `.ve-card`s with hover-lift and staggered `fadeUp` (set `--i` per card), a `.why` callout, and `.badge`/`.medium` chips. Sections are color-coded — Core = blue (`--node-a`), Expand = orange (`--node-c`), Media = green (`--node-b`).

Fonts must stay offline: the template names `Figtree` / `JetBrains Mono` but falls back to the system stack — never add a Google Fonts or other CDN `<link>` (breaks the no-external-transfer rule and offline use). For richer components (data tables, KPI variants, collapsibles, pipelines), the canonical reference is the visual-explainer skill's `references/css-patterns.md` under `.claude/plugins/marketplaces/zoox-plugin-marketplace/plugins/visual-explainer/skills/visual-explainer/` — read it if you need a pattern the template doesn't already cover.

## Notes

- If a source returns nothing useful, say so rather than padding the digest.
- If the wiki is brand-new / nearly empty (no `_hot.md`, thin index), fall back to asking the user for 2–3 topics directly.
- Respect the user's terse style: lead with the digest, skip preamble.
