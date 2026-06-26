# llm-wiki

Create and operate **LLM Wikis** (Andrej Karpathy's pattern): a persistent,
compounding markdown knowledge base that the LLM builds and maintains from
curated sources. You curate sources and ask questions; the LLM does the
summarizing, cross-referencing, filing, and bookkeeping.

## Skills

- **`create-llm-wiki`** — bootstrap a new vault: a short interview, then it
  scaffolds the directory, a tailored `CLAUDE.md` schema (tiered read protocol,
  hot cache, capture/pointer ingest, lint cadence), `index.md` / `log.md`, an
  `OBSIDIAN.md` guide, optional auto-sync + lint hooks, optional global
  registration, then offers to ingest your first source.
- **`use-llm-wiki`** — ingest into or query an existing vault from **any** session
  (you needn't be inside the vault dir): it resolves the vault, follows its
  `CLAUDE.md`, verifies captures, and handles commit/push the vault's own hooks
  can't fire from outside.

## Usage

After installing this plugin (see the marketplace README), just say things like
*"create an LLM wiki for X"*, *"ingest this link into my <vault>"*, or
*"what does my <vault> say about Y"*. Both skills trigger automatically.
