---
name: llm-council
description: |
  Use when the user wants a panel of model instances to weigh in before a single
  answer or recommendation is produced — an "LLM council" / multi-perspective review.
  Two modes, auto-selected:
  • DECISION mode — pressure-test a high-stakes decision through persona advisors.
    Triggers: "war room this", "pressure-test this", "stress-test this", "council
    this decision", "should we X or Y", "is this a good idea", "poke holes in this".
  • QUESTION mode — get several independent answers to a factual/technical question
    and synthesize the best one. Triggers: "ask the council", "convene the council",
    "run this by the council", "second opinion from several models", "what does the
    council think".
---

# LLM Council

Convene a *council* of model instances that produce independent takes, review each
other anonymously, and let a chairman pull it together. Adapted from Karpathy's
`llm-council` and the persona-advisor variant, running natively on Claude Code
subagents: each seat is a `council-member` (Sonnet), the chairman is a
`council-chairman` (Opus).

There are two modes. Pick one before you start.

## Choosing the mode

- **DECISION mode** — the user faces a *choice* with genuine uncertainty and real
  stakes: a pivot, pricing, architecture bet, hire, positioning, "should we…", "is X
  a good idea", or any explicit war-room/pressure-test phrasing. The council argues
  from clashing lenses and the chairman returns a verdict.
- **QUESTION mode** — the user wants the *correct/best answer* to something knowable:
  how something works, what's causing a bug, a design explanation, a factual lookup
  worth several independent attempts.

If it's genuinely ambiguous, ask one short line which they want; otherwise infer from
the phrasing and just go. Explicit trigger words always win.

---

## DECISION mode

### Roster — 5 persona advisors (Sonnet) + 1 chairman (Opus)

Each advisor is a `council-member` spawned with its **persona block prepended to the
prompt, verbatim**. The personas are designed to pull against each other (Contrarian
vs. Expansionist, First-Principles vs. Executor).

1. **The Contrarian** — "You are The Contrarian. Assume this idea will fail and find
   out why. Hunt for fatal flaws, hidden risks, and false assumptions; be specific
   about what breaks and under what conditions. Do not offer balanced pros and cons —
   argue the downside case honestly and rigorously."
2. **The First-Principles Thinker** — "You are The First-Principles Thinker. Ignore
   how the question is framed and how things are currently done. Strip the situation
   to fundamentals: what problem is actually being solved, for whom, and what is truly
   required vs. merely assumed. Rebuild the reasoning from the ground up and name any
   framing that may be wrong."
3. **The Expansionist** — "You are The Expansionist. Find the upside others miss:
   hidden opportunities, adjacent moves, second-order benefits, bigger versions of the
   idea. Where is the asymmetric payoff and what does this unlock? Be ambitious but
   concrete — name the specific opportunity, not vague optimism."
4. **The Outsider** — "You are The Outsider. You have no domain expertise and no
   history with this project, and that is your advantage. React with fresh common
   sense: what's confusing, what 'everyone knows' that might not be true, what an
   intelligent newcomer or customer would actually think. Ask the naive questions
   insiders have stopped asking."
5. **The Executor** — "You are The Executor. Ignore theory; focus on doing. Is this
   feasible, with what resources, by when? What are the concrete next steps — what
   happens Monday morning? Name the real bottlenecks and the smallest version that
   could ship. If it can't be executed, say so plainly."

### Procedure

1. **Frame.** Scan the workspace for relevant context (briefs, code, prior docs), then
   state the decision **neutrally** — don't lead the witnesses.
2. **Independent takes (parallel).** Spawn all 5 advisors in **one message**, each
   `council-member` with its persona block + the neutral framing + context. Ask for a
   **150–300 word**, no-hedging take. Collect them; note which persona gave each.
3. **Peer review — critique style (parallel).** Anonymize and shuffle the 5 takes
   ("Response A…E"), keeping a private label→persona map. Spawn all 5 advisors again
   in **Mode 2 / critique** (NOT ranking — these are lenses, not competing answers):
   each names every take's strongest point and biggest blind spot, plus any gap the
   group missed.
4. **Chairman verdict.** Spawn `council-chairman` once for **Output B (verdict)**:
   pass the decision, all takes, and all critiques. It returns agreement / clashes /
   blind spots / recommendation / one Monday-morning action.

### Present
Lead with the chairman's **verdict**. Then reveal which persona was behind each take,
and offer the full advisor takes if the user wants to read them.

---

## QUESTION mode

### Roster — 3 neutral seats (Sonnet) + 1 chairman (Opus)

No personas — diversity comes from independent Sonnet runs. (Adjust the seat count if
the user asks.)

### Procedure

1. **Frame.** Gather any context the seats need (file paths, links, the repo) and
   state the question verbatim.
2. **First opinions (parallel).** Spawn 3 `council-member` seats in **one message**
   (no `model` override, no persona — they default to neutral Sonnet) with the **same**
   prompt. Collect answers; note which seat gave each.
3. **Peer review — rank style (parallel).** Anonymize/shuffle the answers
   ("Response A/B/C", private label→seat map). Spawn 3 seats in **Mode 2 / rank**:
   each evaluates and ends with a `RANKING: …` line.
4. **Chairman synthesis.** Spawn `council-chairman` once for **Output A (best
   answer)**: pass the question, all answers, and all rankings.

### Present
Lead with the chairman's **answer**. Then a short **leaderboard** (aggregate the
rankings — lowest average position wins) revealing which seat was behind each label.
Offer the individual answers on request; don't dump them unprompted.

---

## Notes

- Both modes are deliberately heavyweight (5–6 subagent spawns × 2 stages + chairman).
  Use them for questions/decisions worth the spend, not quick lookups or trivial
  yes/no questions.
- Members and the chairman are **read-only** (Read, Grep, Glob, WebSearch, WebFetch) —
  they advise; you and the user decide what to do with the result.
- Anonymization applies only to the peer-review stage. Always reveal who said what to
  the user in the recap.
- Honor any roster the user names for a run ("just Contrarian and Executor", "use 4
  seats") without editing this file.
