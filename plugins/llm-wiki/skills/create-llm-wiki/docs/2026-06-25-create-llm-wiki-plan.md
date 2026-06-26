# create-llm-wiki Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable Claude Code skill, `create-llm-wiki`, that bootstraps a new Karpathy-style LLM Wiki for any topic at `~/wikis/<topic>/`.

**Architecture:** A `SKILL.md` runs a short interview, then scaffolds a wiki directory (raw sources + LLM-owned wiki + index/log) and writes a tailored `CLAUDE.md` schema assembled from bundled templates. The skill is bootstrap-only; the generated `CLAUDE.md` drives all future ingest/query/lint. A verbatim copy of Karpathy's idea file is bundled for grounding.

**Tech Stack:** Markdown skill (`SKILL.md` + templates + references), executed by Claude Code. No runtime/build system. Generated wikis are plain markdown + git.

## Global Constraints

- Skill lives at `~/.claude/skills/create-llm-wiki/`.
- Generated wikis default to `~/wikis/<topic-slug>/`; path is always confirmed; abort if target exists and is non-empty.
- Generated schema file is `CLAUDE.md` only (no AGENTS.md, no symlink).
- Obsidian-compatible conventions: `[[wikilinks]]`, YAML frontmatter on pages, `raw/assets/` for images (only when images enabled).
- `qmd` is documented as optional search, never installed.
- No starter example pages in the generated wiki.
- Each new wiki gets `git init` + one initial commit.
- Skill ends by offering to ingest the first source.
- Template placeholders use `{{TOKEN}}` syntax.

---

### Task 1: Skill directory + bundled reference (Karpathy idea file)

**Files:**
- Create: `~/.claude/skills/create-llm-wiki/references/llm-wiki-pattern.md`

**Interfaces:**
- Produces: a verbatim grounding doc that `SKILL.md` (Task 3) tells Claude to read before scaffolding, so the generated schema faithfully reflects the pattern.

- [ ] **Step 1: Create the references file with Karpathy's idea file verbatim**

Write the full "LLM Wiki" idea file the user supplied (the de-duplicated single copy) into `references/llm-wiki-pattern.md`. It must contain these sections verbatim: title + intro ("A pattern for building personal knowledge bases using LLMs…"), `## The core idea`, `## Architecture` (Raw sources / The wiki / The schema), `## Operations` (Ingest / Query / Lint), `## Indexing and logging` (index.md / log.md), `## Optional: CLI tools` (qmd), `## Tips and tricks`, `## Why this works`, `## Note`.

- [ ] **Step 2: Verify the file is present and non-trivial**

Run: `wc -l ~/.claude/skills/create-llm-wiki/references/llm-wiki-pattern.md && grep -c '^## ' ~/.claude/skills/create-llm-wiki/references/llm-wiki-pattern.md`
Expected: a non-trivial line count (the source is concise prose, ~70+ lines) and at least 8 `## ` headers.

- [ ] **Step 3: Commit**

```bash
cd ~/.claude/skills/create-llm-wiki
git init 2>/dev/null; git add references/llm-wiki-pattern.md
git commit -m "feat(create-llm-wiki): bundle Karpathy LLM Wiki pattern reference"
```
(If `~/.claude/skills` is not a repo and you prefer not to init one, skip the git commands — they are optional bookkeeping, not required for the skill to work.)

---

### Task 2: Scaffolding templates

**Files:**
- Create: `~/.claude/skills/create-llm-wiki/templates/wiki-CLAUDE.md.template`
- Create: `~/.claude/skills/create-llm-wiki/templates/index.md.template`
- Create: `~/.claude/skills/create-llm-wiki/templates/log.md.template`

**Interfaces:**
- Produces: three template files consumed by `SKILL.md` (Task 3). Placeholders filled at scaffold time: `{{TOPIC}}`, `{{PURPOSE}}`, `{{USE_CASE}}`, `{{PAGE_TYPES}}`, `{{IMAGE_GUIDANCE}}`, `{{DATE}}`.

- [ ] **Step 1: Write `templates/index.md.template`**

```markdown
# {{TOPIC}} — Index

> Content catalog for this wiki. The LLM updates this on every ingest.
> Read this first when answering a query, then drill into linked pages.

## Overview
- [[overview]] — high-level summary and current thesis (create on first ingest)

## Sources
<!-- one line per ingested source: [[source-slug]] — one-line summary (YYYY-MM-DD) -->

## Entities
<!-- people, orgs, places, works: [[entity-slug]] — one-liner -->

## Concepts
<!-- ideas, themes, methods: [[concept-slug]] — one-liner -->
```

- [ ] **Step 2: Write `templates/log.md.template`**

```markdown
# {{TOPIC}} — Log

> Append-only chronological record. Each entry starts with `## [YYYY-MM-DD] <op> | <title>`
> so it is greppable: `grep "^## \[" log.md | tail -5`.

## [{{DATE}}] create | Wiki initialized
Bootstrapped LLM Wiki for "{{TOPIC}}". Purpose: {{PURPOSE}}. Use-case: {{USE_CASE}}.
```

- [ ] **Step 3: Write `templates/wiki-CLAUDE.md.template`**

```markdown
# {{TOPIC}} — LLM Wiki Schema

This directory is an **LLM Wiki**: a persistent, compounding knowledge base that
*you* (the LLM) build and maintain from curated sources. Purpose: {{PURPOSE}}.

You are a disciplined wiki maintainer, not a generic chatbot. Your job is the
bookkeeping — summarizing, cross-referencing, filing, keeping pages consistent.
The human curates sources, asks questions, and decides what matters.

## Layers

- `raw/` — **immutable** source documents (the source of truth). Read from here;
  never modify these files.{{IMAGE_GUIDANCE}}
- `wiki/` — markdown pages you own: summaries, entity pages, concept pages,
  comparisons, an `overview.md` synthesis. You create and update these.
- `index.md` — content catalog. Read first on any query; update on every ingest.
- `log.md` — append-only chronological record.

## Conventions

- Cross-reference with `[[wikilinks]]` (Obsidian-compatible). Link liberally.
- Every wiki page starts with YAML frontmatter:
  ```yaml
  ---
  title: <human title>
  type: source | entity | concept | overview | comparison
  date: <YYYY-MM-DD>
  sources: <count of raw sources backing this page>
  tags: [<topic-specific>]
  ---
  ```
- Page filenames are kebab-case slugs. One page = one entity/concept/source.
- This wiki emphasizes these page types: {{PAGE_TYPES}}.

## Operations

### Ingest (a new source was added to `raw/`)
1. Read the source. Discuss key takeaways with the human.
2. Write a summary page in `wiki/` (`type: source`).
3. Update `index.md` (add the source; add/adjust entity & concept entries).
4. Update relevant entity/concept pages across `wiki/` — note where the new
   source contradicts or strengthens existing claims.
5. Append a log entry: `## [YYYY-MM-DD] ingest | <source title>`.
   A single source may touch 10–15 pages.

### Query (the human asks a question)
1. Read `index.md`, then drill into relevant pages.
2. Synthesize an answer with citations to wiki pages / sources.
3. If the answer is valuable (a comparison, analysis, discovered connection),
   offer to file it back as a new wiki page so it compounds.

### Lint (periodic health check)
Scan for: contradictions between pages, stale claims superseded by newer
sources, orphan pages (no inbound links), important concepts lacking a page,
missing cross-references, and data gaps worth a web search. Suggest new
questions to investigate and sources to find.

## Navigation & search
`index.md` is enough at small scale. As the wiki grows, `qmd`
(https://github.com/tobi/qmd) is the recommended on-device markdown search
(BM25 + vector, CLI + MCP). Not installed by default — install it when you
outgrow the index.

## Notes
This wiki is a git repo of markdown — commit meaningful ingest/lint passes.
Co-evolve this schema with the human as you learn what works for this domain.
```

- [ ] **Step 4: Verify all three templates exist and contain their placeholders**

Run: `cd ~/.claude/skills/create-llm-wiki/templates && grep -l '{{TOPIC}}' *.template && grep -c '{{' wiki-CLAUDE.md.template`
Expected: all three filenames listed for `{{TOPIC}}`, and a non-zero placeholder count in the schema template.

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/create-llm-wiki
git add templates/
git commit -m "feat(create-llm-wiki): add wiki scaffolding templates"
```

---

### Task 3: SKILL.md (interview + scaffolding procedure)

**Files:**
- Create: `~/.claude/skills/create-llm-wiki/SKILL.md`

**Interfaces:**
- Consumes: `references/llm-wiki-pattern.md` (Task 1), the three templates (Task 2).
- Produces: the invocable skill. Frontmatter `name: create-llm-wiki` and a triggering `description`.

- [ ] **Step 1: Write `SKILL.md`**

````markdown
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
3. **Source kinds** — text-only, or includes images/PDFs? If images, the wiki
   gets `raw/assets/` and image guidance; if text-only, omit both.
4. **Path** — default `~/wikis/<topic-slug>/`; confirm. If it exists and is
   non-empty, stop and ask for a different path.

## Step 2 — Compute template values
- `{{TOPIC}}` = the topic (human title)
- `{{PURPOSE}}` = the one-line purpose
- `{{USE_CASE}}` = chosen use-case type
- `{{PAGE_TYPES}}` = comma-separated page types from Step 1
- `{{DATE}}` = today's date (YYYY-MM-DD)
- `{{IMAGE_GUIDANCE}}` =
  - if images: ` Images live in \`raw/assets/\`. You cannot read markdown with inline images in one pass — read the text first, then view referenced images separately when needed.`
  - if text-only: `` (empty string)

## Step 3 — Scaffold
Create the directory tree:
```
<wiki-path>/
├── CLAUDE.md      # from templates/wiki-CLAUDE.md.template, placeholders filled
├── index.md       # from templates/index.md.template
├── log.md         # from templates/log.md.template
├── raw/           # (+ raw/assets/ only if images enabled)
└── wiki/
```
Fill every `{{PLACEHOLDER}}` from Step 2. Leave `raw/` and `wiki/` empty (no
example pages). Add a `.gitkeep` to `raw/` and `wiki/` so git tracks them.

## Step 4 — git init
```bash
cd <wiki-path>
git init
git add .
git commit -m "chore: bootstrap LLM Wiki for <topic>"
```

## Step 5 — Summarize & hand off
Print: the path created, the tree, and a reminder that `CLAUDE.md` now drives
ingest/query/lint. Then **offer to ingest the first source now**: if the user
agrees, read the new wiki's `CLAUDE.md` and follow its Ingest workflow.
````

- [ ] **Step 2: Verify frontmatter and structure**

Run: `head -5 ~/.claude/skills/create-llm-wiki/SKILL.md && grep -c '## Step' ~/.claude/skills/create-llm-wiki/SKILL.md`
Expected: frontmatter with `name: create-llm-wiki` and a `description:`, and 6 `## Step` headers (Step 0–5).

- [ ] **Step 3: Commit**

```bash
cd ~/.claude/skills/create-llm-wiki
git add SKILL.md
git commit -m "feat(create-llm-wiki): add interview + scaffolding procedure"
```

---

### Task 4: End-to-end dry-run verification

**Files:**
- Temporary: `~/wikis/_smoketest/` (created then removed)

**Interfaces:**
- Consumes: the full skill (Tasks 1–3).
- Produces: confidence that scaffolding yields the correct tree and filled schema.

- [ ] **Step 1: Manually simulate the scaffold for a throwaway topic**

Using the templates, scaffold a test wiki (topic "Smoke Test", purpose "verify the skill", use-case research, text-only) at `~/wikis/_smoketest/`. Fill placeholders by hand to mimic what the skill does:

```bash
mkdir -p ~/wikis/_smoketest/raw ~/wikis/_smoketest/wiki
touch ~/wikis/_smoketest/raw/.gitkeep ~/wikis/_smoketest/wiki/.gitkeep
```
Then render the three templates into `CLAUDE.md`, `index.md`, `log.md` with the test values.

- [ ] **Step 2: Verify the tree and that no placeholders remain**

Run: `ls -R ~/wikis/_smoketest && grep -R '{{' ~/wikis/_smoketest/*.md`
Expected: tree shows `CLAUDE.md index.md log.md raw/ wiki/`; the `grep` for `{{` returns **nothing** (all placeholders filled).

- [ ] **Step 3: Verify the schema content is coherent**

Run: `grep -E 'Ingest|Query|Lint|wikilinks|qmd' ~/wikis/_smoketest/CLAUDE.md`
Expected: all five terms present.

- [ ] **Step 4: Clean up the smoke test**

Run: `rm -rf ~/wikis/_smoketest`
Expected: directory removed.

- [ ] **Step 5: Commit (docs only, if anything changed)**

```bash
cd ~/.claude/skills/create-llm-wiki
git add -A
git commit -m "test(create-llm-wiki): verify end-to-end scaffold (no tracked artifacts)" --allow-empty
```

---

## Self-Review

**Spec coverage:** bootstrap-only (Tasks 3); `~/wikis/<topic>/` default + confirm + collision abort (Task 3 Step 1.4); CLAUDE.md only (Task 2/3); Obsidian conventions + frontmatter + assets (Task 2 schema, Task 3 image guidance); qmd note no-install (Task 2 schema); no example pages (Task 3 Step 3); git init (Task 3 Step 4); index.md + log.md with date-prefix convention (Task 2); offer first ingest (Task 3 Step 5); verbatim pattern grounding (Task 1). All covered.

**Placeholder scan:** `{{TOKEN}}` occurrences are intentional template syntax, not plan placeholders. No "TBD/TODO/handle edge cases" left.

**Type consistency:** placeholder token names (`{{TOPIC}}`, `{{PURPOSE}}`, `{{USE_CASE}}`, `{{PAGE_TYPES}}`, `{{IMAGE_GUIDANCE}}`, `{{DATE}}`) are identical across Task 2 templates and Task 3 fill step. Directory names (`raw/`, `wiki/`, `index.md`, `log.md`, `CLAUDE.md`) consistent across all tasks.
