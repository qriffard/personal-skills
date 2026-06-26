# create-llm-wiki

A Claude Code skill that bootstraps a new **LLM Wiki** — a persistent,
compounding markdown knowledge base that an LLM builds and maintains for you
from curated sources. Based on Andrej Karpathy's "LLM Wiki" pattern.

## What's an LLM Wiki?

Most LLM-over-documents setups are RAG: you upload files, the model retrieves
chunks at query time, and rediscovers everything from scratch on every question.
Nothing accumulates.

An LLM Wiki is different. The LLM **incrementally builds and maintains** a
structured, interlinked set of markdown pages that sit between you and your raw
sources. Add a source and the LLM reads it, summarizes it, updates entity and
concept pages, flags contradictions, and keeps the cross-references consistent.
The knowledge is compiled once and kept current — not re-derived each time.

You curate sources and ask good questions. The LLM does the bookkeeping —
summarizing, cross-referencing, filing — that makes humans abandon wikis. Pair
it with Obsidian (vault open on one side, Claude on the other) and you browse
the graph in real time as it's written.

Good for: research deep-dives, reading a book, personal/health journaling,
team/business knowledge, competitive analysis, trip planning, course notes —
anything where knowledge accumulates over time.

## What the skill does

Invoke it and it runs a short interview, then scaffolds a ready-to-use wiki:

```
~/wikis/<topic>/
├── CLAUDE.md            # the schema: conventions + ingest/query/lint workflows
├── OBSIDIAN.md          # human-facing: open + visualize the vault in Obsidian
├── index.md             # master index (Recently Active + domain sub-indexes)
├── log.md               # append-only chronological record
├── raw/                 # your immutable captured sources
└── wiki/                # the LLM-owned markdown pages
```

Two files are created lazily, not at bootstrap: **`_hot.md`** (the hot cache — a
disposable, regenerable working set, appears on your first ingest) and
**`_index-<domain>.md`** (per-domain sub-indexes — auto-created when a cluster of
pages sharing a `tags` value grows past ~8 and clutters the master index; the LLM
names and creates it on its own during lint/ingest). A fresh wiki has neither.
More below.

It then `git init`s the wiki and offers to ingest your first source. From then
on the generated `CLAUDE.md` drives everything — the skill is bootstrap-only.

The interview asks: the **topic & purpose**, the **use-case type** (personal /
research / book / business / other, which tunes the page types), the **source
kinds** you'll feed it, the **path** (defaults to `~/wikis/<topic-slug>/`), and
the optional **auto-sync** / **lint nudge** / **global registration** add-ons.

### Reading protocol (keeping queries cheap)

The schema gives the LLM a tiered read order so big wikis stay fast: **`_hot.md`
first** (resolves ~70% of queries) → **master `index.md`** → the 1–2 relevant
**domain sub-indexes** → at most ~5 wiki pages → keyword **grep fallback**. It
never loads the whole wiki for one question.

`_hot.md` is a ~500-token **working-memory scratch pad** — active threads and key
numbers, read first each session. It's **lossy, disposable, and derived**: no
fact lives only there (the indexes and pages are the source of truth), so if it
goes stale or is deleted the LLM just regenerates it. It isn't scaffolded at
creation; it's created and refreshed during any session that modifies wiki pages
(starting with your first ingest).

### Browsing in Obsidian

The vault is an Obsidian vault out of the box (`[[wikilinks]]` + YAML
frontmatter). Each new vault ships an `OBSIDIAN.md` orientation page: how to open
the folder as a vault, use **graph view** / backlinks to see structure and spot
orphans, get sources in via the **Web Clipper**, and optional **Dataview** /
**Marp** plugins. The model: Obsidian is the IDE you read in; Claude does the
writing.

### Ingesting by link

You don't pre-download anything. Hand Claude a **link** and it captures an
immutable local copy into `raw/` itself, then summarizes and cross-references:

- **Web articles / pages** → fetched and saved as markdown.
- **PDFs** (URL or local) → downloaded and read.
- **YouTube / video** → transcript via `yt-dlp` if available (optional, not
  installed); otherwise the link plus whatever title/description/channel can be
  read from the watch page.

The original URL and capture date are recorded in each source page's
frontmatter, so citations stay stable even if the link later rots.

**Capture vs. pointer.** Capture is the default, but for **tools or reference
sites you just want to bookmark** (not archive), choose *pointer mode*: the LLM
keeps only the link — a one-liner under `## Tools & links` in the index (or a
small `type: link` page) — and skips the local copy and full synthesis. You pick
per source.

### Auto-sync (optional)

If you opt in during the interview, the wiki gets a self-contained
`.claude/settings.json` + hooks that mirror the config-repo sync:
- **`Stop`** → `sync-wiki.sh stop` — change-triggered: commits, `git pull --rebase`s,
  and pushes whenever you've changed something; **no-op with no network when clean**
  (so it doesn't sync on every turn).
- **`SessionStart`** → `refresh-wiki.sh` — pulls the latest *before* you edit.
- **`SessionEnd`** → `sync-wiki.sh end` — a guaranteed final reconcile + push (also
  catches a commit a prior push failed to deliver).

Editing the same vault from more than one machine is safe (the writer rebases onto
the remote instead of getting rejected); a failed push is non-fatal; on a genuine
conflict the sync **stops and tells you** rather than clobbering. No remote yet? It
just commits locally until you add one. Because `.claude/settings.json` is tracked
in the vault repo, this hook config rides along to every clone (laptop, VDI) on pull.

### Multi-machine (e.g. laptop + VDI)

Because the vault is a git repo with a remote, you can work on it from several
machines. On each one:

1. `git clone <remote> ~/wikis/<topic>` — the `.claude/` hooks and `.gitattributes`
   come with the clone, so pull-on-start / sync-on-stop work immediately.
2. **In-vault (simplest):** run Claude with that directory as the cwd — the vault's
   `CLAUDE.md` auto-loads and the hooks fire. No skills required.
3. **From outside the vault dir:** also install the `create-llm-wiki` /
   `use-llm-wiki` skills on that machine (`~/.claude/skills/`) and register the
   vault in that machine's `~/.claude/CLAUDE.md`.

`log.md` is union-merged (`.gitattributes`) so the append-only log never conflicts.
Edit sequentially across machines (the start-of-session pull keeps you current);
the hooks reconcile the rest.

### Lint nudge (optional)

Karpathy's pattern says to health-check ("lint") the wiki periodically — but
"periodically" relies on you remembering. Opt in and the wiki gets a
`SessionStart` hook (`.claude/hooks/lint-check.sh`) that counts ingests since the
last lint and, past a threshold (10), injects a "lint due" notice when you open a
session. A hook can't *run* the lint — that's an LLM reasoning pass — so it only
detects and reminds; Claude then runs the pass per the schema.

### Global registration (optional)

If you opt in, the skill links the wiki into your global `~/.claude/CLAUDE.md`
under a managed `## LLM Wikis` section (between marker comments). It adds one
concise line — topic, path, and purpose — so any future session knows the wiki
exists and reads its `CLAUDE.md` when the topic comes up. The edit is idempotent
(no duplicate entries) and never touches anything outside the marked section.

## Usage

In Claude Code, just say what you want — e.g. *"create an LLM wiki for the
history of jazz"* or *"start a knowledge base on my marathon training"*. The
skill triggers automatically. You can also invoke it explicitly with
`/create-llm-wiki`.

## Installing / sharing

The skill is a self-contained directory:

```
create-llm-wiki/
├── SKILL.md                       # the procedure Claude follows
├── README.md                      # this file
├── templates/                     # files rendered into each new wiki
│   ├── wiki-CLAUDE.md.template
│   ├── obsidian-guide.md.template
│   ├── index.md.template
│   ├── log.md.template
│   ├── hooks-settings.json.template
│   ├── sync-wiki.sh.template
│   ├── lint-check.sh.template
│   └── registry-block.md.template
├── references/
│   └── llm-wiki-pattern.md        # Karpathy's idea file, verbatim
└── docs/                          # design + plan (optional, safe to drop)
```

To share, copy the whole `create-llm-wiki/` directory into someone's
`~/.claude/skills/` (or your project's `.claude/skills/`). No dependencies, no
install step. Claude Code discovers it on next launch. The `docs/` folder is
just design history — delete it before sharing if you like.

## The three layers (how it works once running)

- **Raw sources** (`raw/`) — immutable local copies the LLM captures from your
  links/files on ingest. The LLM reads but never edits them.
- **The wiki** (`wiki/`) — LLM-owned markdown pages with `[[wikilinks]]` and
  YAML frontmatter (Obsidian-compatible), navigated via `_hot.md` → `index.md` →
  domain sub-indexes.
- **The schema** (`CLAUDE.md`) — tells the LLM how the wiki is structured and
  the workflows for **ingest** (process a new source), **query** (answer with
  citations, optionally file the answer back), and **lint** (health-check for
  contradictions, stale claims, and orphan pages).

`index.md` is enough navigation at small scale; for large wikis the schema
points at [qmd](https://github.com/tobi/qmd) for on-device search (optional, not
installed).

## Companion skill: using a vault from anywhere

This skill only *bootstraps* a vault. Day-to-day you'll often want to ingest into
or query a vault from a session that **isn't** inside its directory (your
Desktop, a project) — where the vault's `CLAUDE.md` doesn't auto-load and its
hooks don't fire. The companion **`use-llm-wiki`** skill handles that: it resolves
the vault from the global registry, follows its `CLAUDE.md`, and runs the
commit/push itself. Enable **global registration** here so it can find your
vaults.

## Credit

Pattern by [Andrej Karpathy](https://github.com/karpathy). The full idea file is
bundled verbatim at `references/llm-wiki-pattern.md`.
