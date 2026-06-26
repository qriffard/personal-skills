# use-llm-wiki

Companion to [`create-llm-wiki`](../create-llm-wiki/). Where `create-llm-wiki`
*bootstraps* a vault, `use-llm-wiki` lets you **ingest into or query an existing
vault from any Claude session** — without opening the session inside the vault
directory.

## Why it exists

A vault's `CLAUDE.md` only auto-loads, and its hooks (auto-sync, lint nudge) only
fire, when your session runs *inside* that vault. If you usually work elsewhere
(your Desktop, a project) and just say *"ingest this into my jazz vault"* or
*"what does my jazz vault say about X"*, none of that machinery is active. This
skill bridges the gap:

1. **Resolves** the target vault from the `## LLM Wikis` registry in your global
   `~/.claude/CLAUDE.md` (falling back to scanning `~/wikis/`).
2. **Reads that vault's `CLAUDE.md`** and follows its ingest or query workflow
   against absolute paths.
3. **Runs the commit/push itself** (reusing the vault's `sync-wiki.sh`), because
   the vault's `Stop` hook can't fire from an outside session — so an ingest done
   from elsewhere still gets saved and pushed.
4. **Checks if a lint is due** (the `SessionStart` nudge can't fire either).

## Usage

From any session: *"ingest https://… into my marathon vault"*, *"add this PDF to
my jazz wiki"*, *"ask my jazz vault who influenced bebop"*. The skill triggers on
these phrasings, or on a question that clearly matches a registered vault. You
can also invoke it explicitly with `/use-llm-wiki`.

> Tip: enable **global registration** when you create a vault (a `create-llm-wiki`
> option) — it's what lets this skill (and any session) discover your vaults.

## Sharing

Self-contained: copy this directory into `~/.claude/skills/`. It pairs with
`create-llm-wiki` but needs no other dependencies. No install step.
