---
name: create-llm-wiki
description: Use when the user wants to create, bootstrap, or start a new LLM Wiki / Karpathy-style markdown knowledge base for a topic or area they want to build up over time. Triggers on "create an LLM wiki", "start a knowledge base for X", "bootstrap a wiki", "new LLM wiki". Scaffolds the directory, schema (CLAUDE.md), index, and log, then offers to ingest the first source.
---

# Creating a new LLM Wiki

Bootstrap a new **LLM Wiki** (Andrej Karpathy's pattern): a persistent,
compounding markdown knowledge base the LLM builds and maintains from curated
sources. This skill is **bootstrap-only** — it creates the wiki and writes the
`CLAUDE.md` schema that makes the wiki self-operating in future sessions.

## Step 0 — Ground yourself
Read `references/llm-wiki-pattern.md` (in this skill dir) so the scaffold and
schema faithfully reflect the pattern.

## Step 1 — Interview (one question at a time)
Ask, and wait for each answer:
1. **Topic & purpose** — what area, and a one-line purpose? Derive a kebab-case
   `<topic-slug>` from the topic; confirm it.
2. **Use-case type** — personal / research / book / business / other. This sets
   which page types the schema emphasizes:
   - personal → entities (people), concepts (habits/goals), overview
   - research → entities, concepts, evolving thesis (overview)
   - book → characters, themes, plot threads, places
   - business → people, projects, decisions, concepts
   - other → entities, concepts, overview
   Record the chosen list as `{{PAGE_TYPES}}`.
3. **Source kinds** — web articles/links and PDFs are always supported (on
   ingest Claude captures a local copy into `raw/`, so the user just pastes a
   link). Also ask:
   - includes **images**? → wiki gets `raw/assets/` + image guidance.
   - includes **YouTube/video**? → schema gets the optional `yt-dlp` transcript
     guidance with a metadata-only fallback.
4. **Path** — default `~/wikis/<topic-slug>/`; confirm. If it exists and is
   non-empty, stop and ask for a different path.
5. **Auto-sync (optional)** — should this wiki commit + push at the end of each
   Claude session? If yes, ask for a git remote URL (e.g. a GitHub repo). They
   may skip the remote and add one later — the hook pushes only when an `origin`
   remote exists, otherwise it just commits locally. Record `{{AUTO_SYNC}}`
   (yes/no) and the remote URL if given.
6. **Lint nudge hook (optional)** — add a `SessionStart` hook that warns when a
   health check is overdue (≥10 ingests since the last lint)? The hook only
   reminds; the lint itself runs in-session. Record `{{LINT_HOOK}}` (yes/no).
7. **Register globally (recommended)** — should this wiki be linked into the
   user's global `~/.claude/CLAUDE.md` so it's discoverable from any session?
   Recommend **yes**: it's what lets the `use-llm-wiki` skill (and any session)
   find and operate on this vault when the user isn't working inside its
   directory — their common case. Record `{{REGISTER}}` (yes/no).

## Step 2 — Compute template values
- `{{TOPIC}}` = the topic (human title)
- `{{PURPOSE}}` = the one-line purpose
- `{{USE_CASE}}` = chosen use-case type
- `{{PAGE_TYPES}}` = comma-separated page types from Step 1
- `{{DATE}}` = today's date (YYYY-MM-DD)
- `{{IMAGE_GUIDANCE}}` =
  - if images: a newline + indented sentence — `\n  Images live in \`raw/assets/\`. You cannot read markdown with inline images in one pass — read the text first, then view referenced images separately when needed.`
  - else: `` (empty string)
- `{{VIDEO_GUIDANCE}}` =
  - if YouTube/video: a newline + new bullet — `\n- **YouTube / video** → if \`yt-dlp\` is available, pull the transcript (\`yt-dlp --write-auto-subs --skip-download --sub-format vtt <url>\`) and save it as \`raw/<slug>.txt\`. If it isn't installed, ask the human whether to install it; if they decline, capture the watch page's title, channel, and description via \`WebFetch\` into \`raw/<slug>.md\` and note that no full transcript was captured.`
  - else: `` (empty string)

## Step 3 — Scaffold
Create the directory tree:
```
<wiki-path>/
├── CLAUDE.md            # from templates/wiki-CLAUDE.md.template
├── OBSIDIAN.md          # from templates/obsidian-guide.md.template (human-facing)
├── index.md             # from templates/index.md.template (master index)
├── log.md               # from templates/log.md.template
├── raw/                 # (+ raw/assets/ only if images enabled)
├── scripts/             # extraction scripts for two-phase ingest
│   ├── extract-pdf.py
│   ├── extract-youtube.py
│   └── outline.py
└── wiki/
```
Do **not** create `_hot.md` or any `_index-<domain>.md` — both are created
lazily per the schema (the hot cache on the first wiki-modifying session; a
domain sub-index when that domain grows large enough). A fresh wiki has neither.

Fill every `{{PLACEHOLDER}}` from Step 2. Leave `raw/` and `wiki/` empty (no
example pages). Add a `.gitkeep` to `raw/`, `wiki/`, and — if images are
enabled — `raw/assets/`, so git tracks the empty directories.

**Always create the `scripts/` directory** with at least these extraction scripts
(copy them from `templates/scripts/`):
- `extract-pdf.py` — PDF to markdown (tries pymupdf4llm, pymupdf, pdftotext)
- `extract-youtube.py` — YouTube URL or VTT/SRT to timestamped markdown
- `outline.py` — extracts headings with line numbers from any markdown file
Make all scripts executable (`chmod +x`). These support the two-phase ingest
protocol described in the wiki's CLAUDE.md — the Fetch phase runs these scripts
to extract content without consuming main-model tokens.

Always create `.gitattributes` from `templates/gitattributes.template` (union-merge
for `log.md` so the append-only log doesn't conflict across machines).

If **auto-sync** (`{{AUTO_SYNC}}` = yes) **or** **lint nudge** (`{{LINT_HOOK}}` =
yes) is enabled, create `.claude/` with the relevant hooks:
- `.claude/settings.json` — from `templates/hooks-settings.json.template`. Auto-sync
  owns the `Stop` (`sync-wiki.sh stop`, change-triggered), the `SessionStart`
  `refresh-wiki.sh` entry (pull on start), and the `SessionEnd` (`sync-wiki.sh end`,
  guaranteed push). Lint nudge owns the `SessionStart` `lint-check.sh` entry. Keep
  only enabled pieces: if no auto-sync, drop `Stop`, `SessionEnd`, and the refresh
  entry; if no lint nudge, drop the lint entry; drop a now-empty `SessionStart`.
- `.claude/hooks/sync-wiki.sh` + `.claude/hooks/refresh-wiki.sh` — iff auto-sync.
- `.claude/hooks/lint-check.sh` — iff lint nudge.
- `chmod +x` every script under `.claude/hooks/`.
Note: the vault's `.claude/settings.json` is tracked in the vault repo, so this
hook config propagates to every clone (laptop, VDI) automatically on pull.

## Step 4 — git init
```bash
cd <wiki-path>
git init
git add .
git commit -m "chore: bootstrap LLM Wiki for <topic>"
```
If auto-sync is on and a remote URL was given, wire it up and push the first
commit (sets the upstream so the Stop hook can push thereafter):
```bash
git remote add origin <remote-url>
git push -u origin HEAD
```

## Step 5 — Register in global CLAUDE.md (if `{{REGISTER}}` = yes)
Link the wiki into `~/.claude/CLAUDE.md` so it's discoverable from any session.
Be idempotent — never duplicate an entry, never clobber the file:

1. Read `~/.claude/CLAUDE.md`. Look for the markers
   `<!-- BEGIN: create-llm-wiki registry -->` … `<!-- END: create-llm-wiki registry -->`.
2. If the markers are **absent**, append the block from
   `templates/registry-block.md.template` to the end of the file.
3. Build the entry line (use the `~/wikis/<slug>/` form for readability):
   `- **{{TOPIC}}** — \`<wiki-path>\` — {{PURPOSE}}`
4. If an entry whose path equals `<wiki-path>` already exists between the
   markers, stop (already registered). Otherwise insert the entry line on its
   own line immediately **before** the `<!-- END: create-llm-wiki registry -->`
   marker.

## Step 6 — Summarize & demonstrate the first ingest
Print: the path created, the tree, which options were enabled (auto-sync, lint
nudge, global registration), and a reminder that `CLAUDE.md` now drives
ingest/query/lint with a hot-cache-first read protocol.

Then **guide the user through their first ingest as a live demonstration** —
don't just offer. Ask for a first source (a link or file); once they give one,
read the new wiki's `CLAUDE.md` and walk through its full Ingest workflow out
loud, showing each step move once: capture into `raw/` → write the summary page
→ update `index.md` (+ a domain sub-index only if one already exists) →
create/refresh `_hot.md` (this
first ingest is what brings it into existence) → update/create entity & concept
pages → append to `log.md`.
The goal is that the user sees the whole workflow exercised end-to-end on real
material, so the schema is concrete rather than abstract. If they have no source
ready, briefly narrate what that first ingest will look like so they know what to
expect next session.
