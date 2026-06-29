---
name: agent-practice-audit
description: >-
  Audit coding agent practices for accuracy and cost efficiency. Inspects
  CLAUDE.md config files, skill inventory, MCP servers, and recent session
  transcripts for anti-patterns (bloated config, kitchen-sink sessions, missed
  plan mode, trivial command delegation, repeated corrections). Produces a scored
  report with actionable recommendations. Trigger on "audit my practices",
  "check my agent hygiene", "how am I using agents", or "agent health check".
disable-model-invocation: true
---

# Agent Practice Audit

Inspect your coding agent setup and recent session patterns against best
practices. Produces a scored report (Config Health + Session Patterns, each
out of 10) with specific recommendations.

## How to run

Run the audit script — it does all the heavy parsing so you don't burn tokens
reading transcripts:

```bash
python <SKILL_DIR>/scripts/audit.py
```

The script automatically finds:
- `~/.claude/CLAUDE.md` and project-level CLAUDE.md files
- Skills in `~/.cursor/skills/` and `~/.claude/skills/`
- MCP servers in settings.json
- Session transcripts in `~/.cursor/projects/*/agent-transcripts/`

## After running the script

1. Read the script's output (it's compact — typically <50 lines).
2. Interpret the scores and issues for the user.
3. For each recommendation, explain *why* it matters (link to the principle)
   and suggest a concrete fix.
4. If config files are flagged as bloated, offer to review them and suggest
   specific lines to cut (ask: "would removing this cause a mistake?").
5. If session anti-patterns are found, suggest workflow adjustments.

## Options

- `--sessions N` — analyze N most recent sessions (default: 10)
- `--config-only` — skip session and skill analysis
- `--sessions-only` — skip config and skill analysis
- `--skills-only` — only run skill audit
- `--transcripts DIR` — add extra transcript directories to scan
- `--json` — output raw JSON instead of formatted report

## Scoring rubric

### Config Health (out of 10)

| Deduction | Condition |
|-----------|-----------|
| -1 | Any CLAUDE.md >3000 tokens |
| -3 | Any CLAUDE.md >5000 tokens |
| -1 per skill (max -3) | SKILL.md >500 lines |
| -1 | >5 MCP servers connected |
| -2 | >10 MCP servers connected |

### Session Patterns (out of 10)

| Deduction | Condition |
|-----------|-----------|
| -2 | Any kitchen-sink session (>50 messages) |
| -2 per session (max -4) | Multi-file edits without Plan mode |
| -2 per session (max -4) | Jumped to code: >3 file edits, ≤1 read, no Plan mode |
| -1 | >30% trivial shell calls |
| -3 | >50% trivial shell calls |
| -1 | Any repeated corrections |
| -2 | >2 repeated correction instances |
| -1 | No subagent usage in long sessions (>30 avg msgs) |
| -1 | ≥30% sessions classified as cheap (Haiku-tier) |
| -2 | ≥50% sessions classified as cheap (Haiku-tier) |

### Skill Health (out of 10)

| Deduction | Condition |
|-----------|-----------|
| -1 | >2 dead user-owned skills (never triggered in any transcript) |
| -2 | >5 dead user-owned skills |
| -3 | >50% of user-owned skills dead |
| -1 per (max -2) | Duplicate skills across sources |
| -1 | Any trigger issues (missing/vague/bloated descriptions) |
| -2 | >5 trigger issues |
| -1 | Any model-fit issues |
| -2 | >3 model-fit issues |

#### What it checks

- **Dead skills**: user-owned skills never read in any session transcript
- **Duplicates**: same skill name provided by different sources (e.g. both
  in `~/.claude/skills/` and from a plugin)
- **Trigger issues**: missing description (will never fire), description
  <30 chars (too vague), description >200 tokens (bloated, wastes context)
- **Model-fit issues**:
  - Skills with scripts but `disable-model-invocation: false` — the model
    wastes tokens reasoning about what the script already does
  - Skills >300 lines with no scripts — large prompt-only skills are
    token-expensive; consider extracting logic into a script

### Model-Level Fit

Each session is classified into a complexity tier based on observable signals
(file edits, message count, unique tool types):

| Tier | Criteria | Recommended model |
|------|----------|-------------------|
| **cheap** | ≤2 file edits, ≤10 messages, ≤3 tool types | Haiku / fast model |
| **standard** | ≤15 file edits, ≤40 messages, ≤8 tool types | Sonnet / Composer |
| **frontier** | Above standard thresholds | Opus / opusplan |

The audit flags sessions where a cheaper model would have sufficed and complex
sessions that skipped Plan mode (where opusplan's plan-then-execute would help).

## Best practices reference

Based on the Zoox internal guide (Amit Navindgi) and general agent discipline:

**Accuracy**: Plan before coding, give the agent self-verification, be specific
(name files/patterns), keep CLAUDE.md as a lookup table, use fresh-context
review, course-correct early.

**Cost**: Short scoped sessions, match model to task (Sonnet default, Opus for
hard problems, Haiku for trivial), clear context between unrelated tasks,
delegate verbose work to subagents, diagnose before optimizing.
