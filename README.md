# personal-skills

A private [Claude Code](https://claude.com/claude-code) plugin marketplace —
Quentin Riffard's personal skills, packaged as installable, versioned plugins
and shareable across machines and with other people.

## Plugins

| Plugin | What it does |
|--------|--------------|
| **llm-wiki** | Create and operate Karpathy-style LLM Wikis (`create-llm-wiki`, `use-llm-wiki`). |
| **data-viz-design** | Publication-grade plots, charts, and dashboards for expert/executive audiences. |
| **diagnose-network-latency** | Diagnose slow/laggy internet on macOS and pinpoint the root cause. |
| **llm-council** | Convene a panel of model instances to pressure-test a decision or answer a question. |
| **everything-tracker** | Sync Kobo highlights into the personal LLM wiki (`kobo-sync`). |
| **storm-research** | Multi-perspective research pipeline (Stanford STORM): 5 lenses → contradiction map → verified HTML briefing, wiki-aware. |

## Install

Add the marketplace and enable a plugin in your `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "personal-skills": {
      "source": { "source": "git", "url": "git@github.com:qriffard/personal-skills.git" },
      "autoUpdate": true
    }
  },
  "enabledPlugins": { "llm-wiki@personal-skills": true }
}
```

Then restart Claude Code (or open `/plugin`). With `autoUpdate: true`, pushes to
this repo propagate to every machine automatically.

## Layout

```
.claude-plugin/marketplace.json     # lists the plugins
plugins/<name>/
  .claude-plugin/plugin.json        # plugin manifest (name, version, …)
  skills/<skill>/SKILL.md           # the skills
```

Adding a skill = drop it under a plugin's `skills/`, bump the version, push.
A new plugin = new `plugins/<name>/` dir + an entry in `marketplace.json`.
