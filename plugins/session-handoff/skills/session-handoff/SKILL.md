---
name: session-handoff
description: |
  Generate a dense, technical "State of the Project" summary for a clean session
  handoff. Use when the user wants to start a fresh conversation window without
  losing project momentum. Triggers on "handoff", "session handoff", "summarize
  for next session", "context dump", "clear session", "fresh window", or any
  request to summarize the current state for a new chat.
---

# Session Handoff

Generate a **State of the Project** summary that a new Claude Code session can
ingest immediately to pick up exactly where this one left off. The output should
be so dense and specific that the next session needs zero back-and-forth to
resume.

## Tone & style

- Act as a senior software architect writing a technical brief for a peer.
- No generic filler, no pleasantries. Every sentence must carry new information.
- Prefer specific identifiers (file paths, function names, line numbers, flag
  names, schema fields) over prose descriptions.
- Target length: long enough to be complete, short enough to fit in one screen.

---

## Output format

Produce the following six sections in order. Use markdown `##` headers exactly
as shown.

### 1. Current Goal
One paragraph. What is the overarching objective of the work happening right
now? State the problem being solved, not the task list. Include any hard
constraints or deadlines if known.

### 2. Architecture Snapshot
Bullet list. Cover:
- Tech stack (language, framework, runtime, key libraries + their versions if
  they matter)
- Relevant files / modules and their roles (path → what it does)
- How the pieces wire together (data flow, API contracts, IPC, DB schema
  highlights)
- Anything non-obvious about the structure (monorepo layout, generated code,
  external services)

### 3. Completed Milestones
Bullet list of what was finished and verified in this session. For each item,
name the exact feature/bug/refactor and state briefly how it was confirmed
(tests pass, manually tested, diff reviewed, etc.). Do not list things that are
partially done.

### 4. Active State & Modified Files
Table or bullet list:

| File | Status | Notes |
|------|--------|-------|
| `path/to/file` | Modified / New / Deleted | What changed and why |

Include only files touched in this session. Flag any uncommitted changes or
stash entries.

### 5. Open Decisions & Roadblocks
Numbered list. For each item:
- **What it is** — the unresolved question, active bug, or blocked task.
- **Why it's stuck** — missing info, dependency, tradeoff not yet resolved.
- **Options considered** — if any were discussed, list them concisely.

If nothing is blocked, write "None."

### 6. Next Immediate Steps
Numbered, ordered action list. Each step must be:
- Specific enough to execute without clarification (name the file, function,
  command, or API endpoint involved)
- Sequenced correctly (dependencies respected)
- Scoped to what the next session should do *first*, not a full backlog

---

## Procedure

1. **Gather context.** Before writing, collect:
   - Recent git log: `git log --oneline -20`
   - Uncommitted changes: `git status` and `git diff --stat`
   - Any open task list or plan files in the repo
   - Key source files mentioned or edited in this session

2. **Draft.** Write the six sections using the gathered facts. Do not invent
   or speculate — if something is uncertain, flag it as such in section 5.

3. **Deliver.** Output the summary as a fenced markdown block the user can
   copy-paste directly into the next session's opening message. Wrap it in:

   ````
   ```
   STATE OF THE PROJECT — <date>
   
   <the six sections>
   ```
   ````

4. **Offer next steps.** After the block, in one sentence, remind the user
   they can paste this at the top of a new session and Claude will resume
   immediately.
