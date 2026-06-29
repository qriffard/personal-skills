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

Options:
- `--sessions N` — analyze N most recent sessions (default: 10)
- `--config-only` — skip session analysis
- `--sessions-only` — skip config audit
- `--transcripts DIR` — add extra transcript directories to scan
- `--json` — output raw JSON instead of formatted report

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
| -1 | >30% trivial shell calls |
| -3 | >50% trivial shell calls |
| -1 | Any repeated corrections |
| -2 | >2 repeated correction instances |
| -1 | No subagent usage in long sessions (>30 avg msgs) |
| -1 | ≥30% sessions classified as cheap (Haiku-tier) |
| -2 | ≥50% sessions classified as cheap (Haiku-tier) |

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
