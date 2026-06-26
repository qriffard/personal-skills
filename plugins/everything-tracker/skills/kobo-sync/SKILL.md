---
name: kobo-sync
description: |
  Sync Kobo highlights into the personal LLM wiki. Triggers on:
  "sync my Kobo highlights", "pull my reading highlights", "kobo-sync",
  "update my reading wiki", "import Kobo quotes", "sync books to wiki",
  "what books have I highlighted", "add my Kobo highlights to my wiki".
---

# Kobo → Wiki Sync

Pulls highlights from the Kobo cloud API, enriches each book with Open Library
metadata (summary, subjects), writes one `raw/kobo-<slug>.md` per book into
`~/wikis/personal/raw/`, then ingests new files into the wiki.

## Step 1 — Check credentials

The script needs `KOBO_EMAIL` and `KOBO_PASSWORD` in the environment.

Check with:
```bash
echo "KOBO_EMAIL=${KOBO_EMAIL:-NOT SET}  KOBO_PASSWORD=${KOBO_PASSWORD:+SET}"
```

If either is missing, tell the user:
> Run `source ~/claude-code/everything_tracker/.env` in your terminal (prefix the
> command with `!` to run it here), then re-invoke this skill.

Never hardcode or echo credentials.

## Step 2 — Run the sync script

```bash
python ~/.claude/plugins/cache/personal-skills/everything-tracker/1.0.0/skills/kobo-sync/scripts/kobo_to_wiki.py
```

Flags to pass when the user asks:
- `--refresh` — overwrite raw files that already exist
- `--all` — include books with no highlights (still writes metadata + summary)
- `--wiki <path>` — override the default `~/wikis/personal`

The script prints a list of files written to `raw/`.

## Step 3 — Ingest new files into the wiki

For **each new file** the script wrote (not skipped), ingest it into the
personal wiki at `~/wikis/personal/` by following that wiki's full ingest
protocol (read its `CLAUDE.md` for the exact steps):

1. Read `~/wikis/personal/CLAUDE.md` (do this once before the first ingest,
   not once per book).
2. For each new `raw/kobo-<slug>.md`:
   - Read the raw file. The frontmatter gives author, year, status, subjects,
     and summary. The body has all the highlights.
   - Create or update a wiki page in `wiki/` (kebab-case slug, no `kobo-`
     prefix in the wiki page name — e.g. `raw/kobo-the-pragmatic-programmer.md`
     → `wiki/the-pragmatic-programmer.md`). Page type: `source` if it is purely
     a highlight dump, or `entity` if the book is rich enough to become a
     standing reference.
   - Frontmatter: set `type`, `date` (today), `tags` (derive from subjects),
     `captured` (today), `source_url` (omit — no URL), `sources: 1`.
   - Body: title, author, year, summary paragraph, then all highlights as
     blockquotes. Group highlights thematically when there are 10+.
   - Update `~/wikis/personal/index.md` (add entry, refresh "Recently Active").
   - Update the relevant `_index-<domain>.md` if one exists for reading/books.
   - Refresh `~/wikis/personal/_hot.md`.
   - Append to `~/wikis/personal/log.md`:
     `## [YYYY-MM-DD] ingest | <Book Title> (Kobo highlights)`
3. After all books are ingested, give the user a summary:
   - How many books were synced and ingested
   - List of wiki pages created or updated
   - Any books skipped (no highlights, or already present)

## Notes

- The script is **idempotent**: re-running without `--refresh` skips books
  whose raw files already exist.
- Open Library lookups are best-effort. If no summary is found, the raw file
  has an empty Summary section — still ingest it; the highlights are the value.
- If a book has 0 highlights and `--all` was not passed, it is silently skipped
  by the script. Mention this in the final summary so the user knows.
- The script requires `requests` (`pip install requests`). If it fails with
  `ModuleNotFoundError`, tell the user to install it or source the everything
  tracker virtualenv.
