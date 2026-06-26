---
name: use-llm-wiki
description: Use when the user wants to ingest a source into, or ask a question against, an EXISTING LLM Wiki / knowledge vault — typically from a session that is NOT inside that vault's directory. Triggers on "ingest/add/save this into my <name> wiki/vault", "ask my <name> wiki ...", "what does my <name> vault say about ...", or a question that clearly matches a registered LLM Wiki. Resolves the vault, follows its CLAUDE.md, and handles the commit/push that the vault's own hooks can't fire from an outside session. For creating a NEW wiki, use create-llm-wiki instead.
---

# Using an existing LLM Wiki from anywhere

Operate on an existing LLM Wiki (built by `create-llm-wiki`) without being inside
its directory. Because the session isn't in the vault, the vault's `CLAUDE.md`
won't auto-load and its hooks (auto-sync, lint nudge) won't fire — this skill
does that work explicitly.

## Step 1 — Resolve the target vault
Find the vault's absolute path:
1. Read the `## LLM Wikis` registry in `~/.claude/CLAUDE.md` (between the
   `<!-- BEGIN/END: create-llm-wiki registry -->` markers). Match the user's
   named vault, or — for a question with no named vault — the entry whose
   topic/purpose best fits the question.
2. Fallback if not registered: list `~/wikis/*/` and pick the directory that
   contains both `CLAUDE.md` and `index.md` matching the topic.
3. If nothing matches, or several plausibly do, **ask the user** which vault
   (offer the candidates). Never guess silently.

Let `VAULT` = the resolved absolute path.

## Step 2 — Refresh, then load the vault's schema
**Pull first.** If the vault has an `origin` remote, run
`git -C "<VAULT>" pull --rebase` so you read and write the latest — another
machine (e.g. the user's VDI) may have pushed. Only pull when the tree is clean;
on conflict, stop and tell the user (don't clobber). Then read `<VAULT>/CLAUDE.md`
— the source of truth for that vault's conventions and workflows; follow it
exactly. Operate using **absolute paths** under `<VAULT>/` (don't `cd` and assume
hooks/settings activate; they won't).

## Step 3 — Do the operation

**Ingest** (user gave a source — a link or file):
Follow the vault's two-phase Ingest workflow from its `CLAUDE.md`:

- **Phase 1 — Fetch (low-token).** Get the content into `<VAULT>/raw/<slug>.md`
  using extraction scripts when available (check `<VAULT>/scripts/`). For known
  types (PDF, YouTube, Google Docs JSON), run the matching script directly — no
  need to read the content through the context window. For unknown formats,
  follow the escalation ladder in the vault's schema (probe → ask user →
  small-sample → new script). After extraction, run
  `python <VAULT>/scripts/outline.py <VAULT>/raw/<slug>.md` to produce a compact
  heading outline. **Subagent delegation**: when fetch needs adaptability (auth,
  multi-step), delegate to a background subagent with a tightly scoped prompt
  (fetch + extract only, no wiki updates).

- **Phase 2 — Process (user-guided).** Present the outline and an ingest
  directive template to the user. Read only the sections they flag. Then
  synthesize wiki pages, update indexes/hot cache/log per the vault's schema.
  For small sources (<2000 tokens), skip the directive and process in one pass.

- **Verify every capture succeeded** (non-empty, the expected document, not an
  auth wall / error / blank result). If it fails or is partial, **never assume or
  fabricate the content** — mark it `captured: failed — <reason>` (or `pending`),
  record only what you reliably know, flag the gap in the page/`_hot.md`/log, and
  tell the user. Summaries come only from text actually captured.

**Query** (user asked a question):
- Follow the vault's tiered read protocol: read `<VAULT>/_hot.md` if it exists →
  `<VAULT>/index.md` → the 1–2 relevant `<VAULT>/_index-<domain>.md` → at most
  ~5 pages under `<VAULT>/wiki/` → grep `<VAULT>/wiki/**/*.md` as fallback.
  Answer with citations. If the answer is valuable, offer to file it back as a
  new page (that makes it an ingest-like write — sync in Step 4).

## Step 4 — Sync (after any write: ingest, or a query filed back)
The vault's `Stop` hook can't fire from this session, so commit/push yourself:
- If `<VAULT>/.claude/hooks/sync-wiki.sh` exists:
  `CLAUDE_PROJECT_DIR="<VAULT>" bash "<VAULT>/.claude/hooks/sync-wiki.sh"`
- Else if `<VAULT>` is a git repo: `git -C "<VAULT>" add -A` then commit
  (`git -C "<VAULT>" commit -m "wiki: ingest <name>"`), and
  `git -C "<VAULT>" push` if an `origin` remote exists.
- If `<VAULT>` isn't a git repo, skip silently.

## Step 5 — Lint check (after an ingest)
The `SessionStart` lint nudge can't fire either. Quick check: count `ingest`
entries in `<VAULT>/log.md` since the last `lint` entry; if ≥10 (or run
`<VAULT>/.claude/hooks/lint-check.sh` if present), tell the user a lint pass is
due and offer to run the vault's Lint workflow now.
