---
name: quentin-writing-style
description: Write or edit technical documents in Quentin's personal voice — design docs, DESIGN_DOC.md, Confluence pages, reports, papers, abstracts, proposals, methodology write-ups. Use whenever drafting or revising multi-paragraph technical prose "for me", "in my style", "as if I wrote it", or any document Quentin will sign — even if style isn't mentioned. Works for English and French. NOT for PR descriptions, commit messages, Slack, emails, code comments, or CLAUDE.md/memory edits — those follow their own conventions (stack-pr-workflow, terse defaults).
---

# Quentin's technical writing style

Voice distilled from his first-author physics publications (arXiv 1602.01738, 1602.01030, 1504.05865, 1306.4173, 1801.06653) and French PhD thesis. Formal-technical register: guided, methodical, collective-voice prose. Full evidence-backed profile in [references/style-profile.md](references/style-profile.md) — read it when writing anything longer than a few paragraphs, when writing French, or when unsure how a pattern applies.

## Core voice

- **Collective "we", always** — even for solo work: "we propose", "we have shown". Never "I" in documents (French exception: conclusions claiming personal contribution may use "j'ai montré"). No contractions.
- **Guide the reader through observations**: "we can observe that", "we can note that", "we can clearly identify", "Note that…". The author walks the reader through the evidence rather than asserting conclusions cold. This is the most distinctive tic — use it, don't sand it off.
- **Hedge predictions, assert measurements.** Future/expected behavior gets "should", "expected to", "roughly", "of the order of". Measured or verified facts are stated flat: "This analysis shows that…".
- Novelty stated plainly: "an original method", "for the first time" — no marketing superlatives beyond "the first" / "the most precise".

## Architecture

- **Purpose-first sentences**: open with "In order to X, …", "In this context, …", "For [X], …" then the action.
- **Paragraphs are context-first, claim-last**: 1–2 sentences of setup, the observation, then one interpretation sentence ("It indicates that…", "This is consistent with…"). Keep measurement and interpretation in separate sentences.
- **Sections open with a goal restatement** ("In this section, we present…") and long documents get an explicit roadmap paragraph at the end of the intro ("First, … Then, … Finally, …").
- **Close sub-arguments explicitly**: "In conclusion, …" is allowed mid-document to seal a local argument.
- **End on perspectives, not limitations**: conclusions recap ("we have presented…"), restate the headline number, then "The next step will be…".
- Sentences medium-long (20–35 words): main claim first, mechanism in a trailing "which/that" or participial clause. Prose over bullets — bullets only for enumerated definitions (cuts, cases, criteria).

## Connectors (use his actual inventory)

English: "Indeed," (signature — justifies the previous sentence), "Moreover,", "Thus,", "Hence,", "However,", "In addition,", "First, … Second, … Finally,", "As mentioned before,", "As shown in figure X".
French: "Ainsi," (conclusive opener), "En effet,", "De plus,", "Cependant,", "Par ailleurs,", "Dans un second temps,", "nous nous proposons de…", "Il est important de noter que".

Avoid connectors he never uses: "That said,", "Interestingly,", em-dash asides, rhetorical questions (English; French allows one as a pivot: "La question que nous pouvons nous poser est : … ? Pour y répondre, nous nous proposons de…").

## Technical presentation

- Numbers: value ± uncertainty with unit; ranges "[7, 120] keV" or "ranging from 5.5 to 8.8"; approximations "roughly 57", "about 40%".
- Figures/tables are active subjects: "Figure 4 shows…", "This figure highlights…". Reference them inline, lowercase "figure 2" mid-sentence.
- Expand acronyms at first use: "WIMP (Weakly Interacting Massive Particle)". Paired quantities via "(resp. …)". "i.e."/"e.g." inline freely.
- Definitions formalized: "X is defined as the ratio between…".
- Methods as temporal chain: "First, … Next, … Then, … Finally, …", naming tools explicitly.

## Preserve vs smooth

Preserve these French-influenced patterns — they ARE the voice: "Indeed," as justifier; "we can + perception verb"; "allows one to / allows the measurement of"; "In order to" openers; "(resp. …)"; "an original X" meaning novel.

Silently fix these — errors, not style: article slips, subject-verb agreement, "allows to + verb" (→ "allows us to"), "instead of" meaning "whereas", faux amis ("performant", "the complementary of"), comma splices (split, or join with "Indeed," or a semicolon).

## Self-check before delivering a draft

- Any "I", contraction, or rhetorical question (English)? Remove.
- Does each results paragraph separate observation from interpretation?
- At least one reader-guiding construction ("we can note/observe…") per page?
- Long doc: intro roadmap present? Conclusion ends on next steps?
- Prose, not bullet-walls?

## Example

Request: "write the methodology section of my metrics design doc"

Flat/generic: "This doc describes the new comfort metric. The metric is computed per scenario. Results show it works well."

His voice: "In order to quantify ride comfort at scale, we propose an original per-scenario metric derived from the logged acceleration profiles. First, the raw signals are filtered and aggregated per event. We can note that the resulting distribution presents two distinct populations, corresponding to nominal and degraded rides (resp. 94% and 6% of the total). Indeed, this separation allows us to define a rejection threshold directly from data. The next step will be the extension of this method to the full simulation corpus."

Rationale: purpose-first opener, collective "we", "an original", temporal chain, reader-guidance ("We can note"), "(resp. …)", "Indeed," justifier, perspectives close.
