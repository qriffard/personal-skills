# Design: `create-llm-wiki` skill

**Date:** 2026-06-25
**Status:** Approved (pending written-spec review)

## Purpose

A general, reusable skill that bootstraps a new **LLM Wiki** for any area the
user wants to build knowledge on, following Andrej Karpathy's "LLM Wiki"
pattern. The user invokes it, answers a short interview, and the skill scaffolds
a fresh wiki at `~/wikis/<topic>/` — directory structure, a tailored `CLAUDE.md`
schema, `index.md`, `log.md`, an initial git commit — then offers to ingest the
first source.

The skill is **bootstrap-only**. It creates the wiki and writes the schema that
makes the wiki self-operating. Ongoing ingest / query / lint operations are
driven by the generated `CLAUDE.md` in future sessions, not by this skill.

## The pattern (grounding)

Karpathy's LLM Wiki has three layers:

- **Raw sources** — curated, immutable source documents. The LLM reads but never
  modifies them. Source of truth.
- **The wiki** — LLM-owned markdown: summaries, entity pages, concept pages,
  comparisons, overview/synthesis. The LLM creates, updates, cross-references,
  and keeps it consistent.
- **The schema** — a `CLAUDE.md` that tells the LLM how the wiki is structured,
  its conventions, and the ingest/query/lint workflows. This is what turns a
  generic chatbot into a disciplined wiki maintainer.

Two navigation files: `index.md` (content catalog) and `log.md` (append-only
chronological record with a `## [YYYY-MM-DD] <op> | <title>` prefix convention).

The verbatim idea file is bundled at `references/llm-wiki-pattern.md` so the
skill is self-grounding.

## Skill structure

```
~/.claude/skills/create-llm-wiki/
├── SKILL.md                       # interview + scaffolding procedure
├── templates/
│   ├── wiki-CLAUDE.md.template     # the schema written into each new wiki
│   ├── index.md.template
│   └── log.md.template
├── references/
│   └── llm-wiki-pattern.md         # Karpathy's idea file, verbatim
└── docs/
    └── 2026-06-25-create-llm-wiki-design.md
```

Rationale: the generated schema is long and stable, so it lives as a template
file rather than inline prose — easier to read, consistent output. Templates use
simple `{{PLACEHOLDER}}` tokens filled from the interview answers.

## The interview

Asked one question at a time when the skill is invoked:

1. **Topic / area + one-line purpose.** Used to derive the `<topic-slug>`
   (kebab-case) and to seed the wiki's overview.
2. **Use-case type** — personal / research / book / business / other. Tunes which
   page types the generated schema emphasizes (e.g. characters+themes+plot for a
   book; entities+concepts+thesis for research).
3. **Source kinds** — text-only, or includes images/PDFs. Toggles the
   `raw/assets/` image-handling guidance in the schema and whether the assets
   folder is created.
4. **Confirm path** — default `~/wikis/<topic-slug>/`, always confirmed. Abort
   with a clear message if the path already exists and is non-empty.

## What gets scaffolded

```
~/wikis/<topic>/
├── CLAUDE.md          # tailored schema (structure, conventions, ops)
├── index.md           # content catalog — category headers, no entries yet
├── log.md             # chronological log, seeded with the creation entry
├── raw/               # immutable sources (+ raw/assets/ if images enabled)
└── wiki/              # LLM-owned markdown pages (empty)
```

No starter example pages — empty folders plus a schema that explains the
conventions is enough; example pages would just become deletable clutter.

### Conventions baked into the generated `CLAUDE.md`

- `[[wikilinks]]` for cross-references; YAML frontmatter on every wiki page
  (tags, date, source count) — Obsidian-vault compatible out of the box.
- `qmd` named as the recommended on-device search tool **once the wiki grows**;
  `index.md` is the default navigation. No install required or performed.
- The three operations spelled out explicitly:
  - **Ingest** — read source → discuss takeaways → write summary page → update
    index → update relevant entity/concept pages → append to log.
  - **Query** — read index → drill into relevant pages → synthesize with
    citations → offer to file good answers back as new pages.
  - **Lint** — health-check: contradictions, stale claims, orphan pages, missing
    pages/cross-references, data gaps.
- Schema targets **`CLAUDE.md` only** (Claude Code).

## Source capture (link-based ingest)

Sources are provided to the LLM **by link** (or file); the user does not
pre-download anything. The generated `CLAUDE.md` ingest workflow begins with a
**capture-first** step that saves an immutable local copy into `raw/`:

- **Web article / page** → `WebFetch`, saved as `raw/<slug>.md`.
- **PDF** (URL or local) → downloaded to `raw/<slug>.pdf`, read natively.
- **YouTube / video** → transcript via `yt-dlp` if available (documented as
  optional, never installed by the skill); if declined/unavailable, fall back to
  the link plus title/channel/description scraped from the watch page.

Each source page records `source_url` and `captured` (date) in frontmatter so
citations stay stable against link rot. The interview's "source kinds" question
gates the image (`raw/assets/`) and video (`yt-dlp`) guidance in the schema.

**Capture vs. pointer mode.** Ingest is per-source: *capture* (default) archives
an immutable copy; *pointer* keeps only the link for tools/reference sites you
want to bookmark rather than archive — a one-liner under `## Tools & links` in
the index (or a `type: link` page), `captured: none (pointer)`, no `raw/` copy
and no multi-page synthesis. Logged as a `pointer` entry.

## Auto-sync (optional, per-wiki)

The interview includes an opt-in question for git auto-sync. When enabled, the
scaffold drops a self-contained, project-level `.claude/` into the wiki:

- `.claude/settings.json` — a **Stop hook** running `.claude/hooks/sync-wiki.sh`.
- `.claude/hooks/sync-wiki.sh` — phase-aware (mirrors the config repo's cloud-sync):
  `stop` (Stop hook, every turn) syncs only when something changed and skips the
  network when clean; `end` (SessionEnd) / no-arg (the use-llm-wiki router) always
  reconcile + push, catching unpushed work. commit → `git pull --rebase` → push.
  Multi-machine safe; on a real conflict it stops and reports (never clobbers).
- `.claude/hooks/refresh-wiki.sh` — SessionStart pull, so a session starts on the
  latest (only when the tree is clean).
- The vault's `.claude/settings.json` is **tracked in the vault repo**, so the hook
  wiring propagates to every clone on pull — no per-machine setup (unlike `~/.claude`,
  whose settings.json is machine-local).
- `.gitattributes` — `log.md merge=union` so the append-only log never conflicts
  across machines. Created for every vault.

Multi-machine: `git clone` the vault on each machine (hooks travel with it). Work
in-vault (CLAUDE.md auto-loads, hooks fire) or install the skills + register the
vault on that machine to operate from outside its directory.

If a remote URL is provided, Step 4 runs `git remote add origin <url>` and
`git push -u origin HEAD` to set the upstream. The automation is scoped to the
wiki directory — it never touches global settings. (Stop fires per assistant
response; switching the hook key to `SessionEnd` would make it once-per-session.)

## Retrieval & maintenance (hot cache, read protocol, lint cadence)

Adapted from a community LLM-wiki schema. The generated `CLAUDE.md` enforces a
**tiered read protocol** so query context stays small as the wiki grows:

1. `_hot.md` — a ~500-token hot-cache working set (active threads + key numbers),
   read first; resolves ~70% of queries. It is **lossy, disposable, and derived**
   (never the sole source of any fact; regenerable from Recently Active + the
   log). **Not scaffolded at bootstrap** — created/refreshed lazily on the first
   (and every subsequent) wiki-modifying session.
2. `index.md` — master index with a "Recently Active" section + links to domain
   sub-indexes.
3. `_index-<domain>.md` — per-domain sub-indexes; open only the 1–2 relevant
   ones, never all. **Created lazily and autonomously** (like `_hot.md`) — not
   scaffolded at bootstrap. A domain = a cluster of pages sharing a `tags` value
   / theme; the LLM promotes it to a sub-index on its own (no confirmation) once
   the cluster grows past ~8 pages and clutters the master index, during a lint
   or ingest. Format spec lives in the generated `CLAUDE.md`.
4. ≤5 wiki pages per query; never load the whole wiki.
5. Keyword grep fallback over `wiki/**/*.md` for unindexed pages.

**Lint cadence.** The schema instructs a lint pass after every 10 ingests
(counted from `log.md`), recorded as a `lint` log entry. An optional per-wiki
`SessionStart` hook (`lint-check.sh`) deterministically detects an overdue lint
and injects a "lint due" notice — it only reminds; the lint reasoning runs
in-session. It shares the wiki's `.claude/` with the auto-sync `Stop` hook;
`hooks-settings.json` carries whichever hooks are enabled.

## Global registration (optional, per-wiki)

An opt-in interview question links the wiki into the user's global
`~/.claude/CLAUDE.md` so it's discoverable from any session (not only when the
cwd is the wiki). The skill maintains a single managed section delimited by
`<!-- BEGIN: create-llm-wiki registry -->` / `<!-- END: ... -->` markers
(skeleton in `templates/registry-block.md.template`):

- If the markers are absent, the block is appended once.
- A one-line entry — `- **<Topic>** — \`<wiki-path>\` — <purpose>` — is inserted
  before the END marker.
- The edit is idempotent: an entry for an already-registered path is not
  duplicated, and nothing outside the marked section is modified.

Cost is intentionally minimal (one line per wiki) since the global file loads
into every session.

## Obsidian companion (`OBSIDIAN.md`)

Each vault ships a human-facing `OBSIDIAN.md` at its root (from
`templates/obsidian-guide.md.template`) — open-as-vault steps, graph-view /
backlinks visualization, Web Clipper for sourcing, image attachment-folder
setup, and optional Dataview / Marp plugins. It is deliberately **not** in
`CLAUDE.md` (that's the LLM's file; a human setup guide there would just cost
context every session). Generated at bootstrap (not lazy) because it's useful the
moment the vault is opened; delete it if Obsidian isn't used.

## Closing step

After scaffolding and the initial git commit, the skill:

1. Prints a summary of what was created (path, structure, next steps).
2. **Offers to ingest the user's first source(s) now**, handing off to the
   ingest workflow in the freshly written `CLAUDE.md`. If the user accepts in the
   same session, the skill points Claude at the new wiki's `CLAUDE.md` and the
   ingest proceeds there.

## Out-of-vault operation (companion skill)

The auto-load of a vault's `CLAUDE.md` and the per-vault hooks only apply when a
session runs *inside* the vault. The common workflow is the opposite — a session
elsewhere asking to ingest into or query a named vault. Two mechanisms cover it:

1. **Strengthened global registry** — the `## LLM Wikis` block in
   `~/.claude/CLAUDE.md` (always loaded) carries general instructions for
   querying and ingesting a vault from outside, including running the vault's
   `sync-wiki.sh` afterward (since the `Stop` hook won't fire from an outside
   session).
2. **`use-llm-wiki` skill** — a globally-discoverable router: resolves the vault
   (registry → fallback scan of `~/wikis/`), reads its `CLAUDE.md`, runs the
   ingest/query against absolute paths, and performs the commit/push and lint
   check that the vault's hooks would otherwise handle.

Global registration is therefore **recommended** (not just optional) — it's the
discovery mechanism both rely on. The per-vault hooks remain a useful safety net
for the occasional in-vault session.

## Scope / non-goals

- Not a full-lifecycle operator. Ingest/query/lint live in the generated schema.
- No `qmd` installation, no MCP setup, no Obsidian plugin configuration — only
  documented as optional in the generated schema.
- No multi-agent schema (no AGENTS.md). `CLAUDE.md` only.
- No starter example pages.

## Open considerations (resolved)

- **Path collision:** if the target dir exists and is non-empty, abort and ask
  for a different path rather than risk overwriting.
- **Slug derivation:** kebab-case the topic; if ambiguous, confirm the slug with
  the user as part of the path confirmation step.
