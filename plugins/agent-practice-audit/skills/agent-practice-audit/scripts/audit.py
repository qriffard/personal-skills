#!/usr/bin/env python3
"""Agent practice audit — inspects config files and session transcripts.

Usage:
    python audit.py [OPTIONS]

Options:
    --sessions N        Number of recent sessions to analyze (default: 10)
    --config-only       Skip session analysis
    --sessions-only     Skip config audit
    --transcripts DIR   Additional transcript directory to scan
    --json              Output raw JSON (default: human-readable summary)

Outputs a compact report the LLM can format into a scored assessment.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


HOME = Path.home()

TRIVIAL_COMMANDS = re.compile(
    r"^(ls|pwd|echo|cat |head |tail |wc |file |which |whoami|hostname|date|"
    r"git status|git log|git diff|git branch|git remote|"
    r"npm --version|node --version|python3? --version)"
)

# Heuristic complexity tiers based on observable session signals.
# "frontier" = Opus / o3 territory, "standard" = Sonnet / Composer,
# "cheap" = Haiku / fast model.  We can't read the actual model from
# transcripts, so we infer what *should* have been used and let the
# user compare against what they actually ran.
COMPLEXITY_THRESHOLDS = {
    "cheap": {
        "max_files_edited": 2,
        "max_messages": 10,
        "max_unique_tools": 3,
        "description": "Simple lookup / single-file edit — Haiku-tier model sufficient",
    },
    "standard": {
        "max_files_edited": 15,
        "max_messages": 40,
        "max_unique_tools": 8,
        "description": "Moderate multi-file work — Sonnet / Composer appropriate",
    },
    # anything above "standard" thresholds → "frontier"
}

TRANSCRIPT_DIRS = [
    HOME / ".cursor" / "projects",
    HOME / ".claude" / "projects",
]

# All known skill locations across both platforms
SKILL_DIRS = [
    HOME / ".claude" / "skills",
    HOME / ".cursor" / "skills",
    HOME / ".cursor" / "skills-cursor",
    HOME / ".claude" / "plugins" / "cache",
    HOME / ".cursor" / "plugins" / "cache",
]

# Config/rules files that load every turn
CONFIG_FILES = {
    "claude": [
        HOME / ".claude" / "CLAUDE.md",
    ],
    "cursor": [
        HOME / ".cursor" / "rules",
    ],
}

# MCP server config locations
MCP_CONFIG_PATHS = [
    HOME / ".claude" / "settings.json",
    HOME / ".claude" / "settings.local.json",
    HOME / ".cursor" / "mcp.json",
]


def estimate_tokens(text: str) -> int:
    return len(text) // 4


def audit_config() -> dict:
    results = {
        "config_files": [],
        "skills": [],
        "mcp_servers": {"count": 0, "sources": []},
        "issues": [],
    }

    # --- Global config files (CLAUDE.md, Cursor rules) ---
    # Claude Code: CLAUDE.md
    global_claude = HOME / ".claude" / "CLAUDE.md"
    if global_claude.exists():
        text = global_claude.read_text(errors="replace")
        tokens = estimate_tokens(text)
        lines = len(text.splitlines())
        results["config_files"].append({
            "path": str(global_claude),
            "tokens": tokens,
            "lines": lines,
            "platform": "claude",
        })
        if tokens > 3000:
            results["issues"].append(
                f"~/.claude/CLAUDE.md is {tokens} tokens — consider trimming "
                f"(loads every turn, never evicted)"
            )

    # Cursor: rules directory (each .mdc or .md file loads per turn)
    rules_dir = HOME / ".cursor" / "rules"
    if rules_dir.is_dir():
        total_rule_tokens = 0
        rule_count = 0
        for rule_file in sorted(rules_dir.iterdir()):
            if rule_file.suffix in (".md", ".mdc", ".txt"):
                text = rule_file.read_text(errors="replace")
                tokens = estimate_tokens(text)
                total_rule_tokens += tokens
                rule_count += 1
                results["config_files"].append({
                    "path": str(rule_file),
                    "tokens": tokens,
                    "lines": len(text.splitlines()),
                    "platform": "cursor",
                })
                if tokens > 3000:
                    results["issues"].append(
                        f"{rule_file.name} is {tokens} tokens — review for bloat"
                    )
        if total_rule_tokens > 5000:
            results["issues"].append(
                f"Cursor rules total {total_rule_tokens} tokens across "
                f"{rule_count} files — all load every turn"
            )

    # Project-level CLAUDE.md files (both platforms)
    for projects_dir in [HOME / ".cursor" / "projects", HOME / ".claude" / "projects"]:
        if projects_dir.exists():
            for claude_md in projects_dir.rglob("CLAUDE.md"):
                if "agent-transcripts" in str(claude_md):
                    continue
                text = claude_md.read_text(errors="replace")
                tokens = estimate_tokens(text)
                platform = "cursor" if ".cursor" in str(claude_md) else "claude"
                results["config_files"].append({
                    "path": str(claude_md),
                    "tokens": tokens,
                    "lines": len(text.splitlines()),
                    "platform": platform,
                })
                if tokens > 3000:
                    results["issues"].append(
                        f"{claude_md} is {tokens} tokens — review for bloat"
                    )

    # --- Skill count (user-owned only, for summary) ---
    user_skill_dirs = [
        HOME / ".claude" / "skills",
        HOME / ".cursor" / "skills",
        HOME / ".cursor" / "skills-cursor",
    ]
    for skills_dir in user_skill_dirs:
        if not skills_dir.exists():
            continue
        for skill_md in skills_dir.rglob("SKILL.md"):
            lines = len(skill_md.read_text(errors="replace").splitlines())
            platform = "cursor" if ".cursor" in str(skill_md) else "claude"
            results["skills"].append({
                "path": str(skill_md),
                "lines": lines,
                "platform": platform,
            })

    # --- MCP server count ---
    for settings_path in MCP_CONFIG_PATHS:
        if not settings_path.exists():
            continue
        try:
            settings = json.loads(settings_path.read_text())
            servers = settings.get("mcpServers", {})
            if servers:
                platform = "cursor" if ".cursor" in str(settings_path) else "claude"
                results["mcp_servers"]["count"] += len(servers)
                results["mcp_servers"]["sources"].append({
                    "path": str(settings_path),
                    "count": len(servers),
                    "platform": platform,
                    "names": list(servers.keys()),
                })
        except (json.JSONDecodeError, KeyError):
            pass

    return results


def _parse_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    try:
        import yaml
        return yaml.safe_load(m.group(1)) or {}
    except Exception:
        meta = {}
        for line in m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip().strip("'\"")
        return meta


def _has_script(skill_dir: Path) -> bool:
    """Check if a skill directory contains executable scripts."""
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.is_dir() and any(scripts_dir.iterdir()):
        return True
    for ext in ("*.py", "*.sh", "*.bash", "*.js", "*.ts"):
        if list(skill_dir.rglob(ext)):
            return True
    return False


def audit_skills(transcript_dirs: list[str] | None = None) -> dict:
    """Deep audit of all installed skills: triggers, usage, model fit, duplicates."""
    results = {
        "total": 0,
        "skills": [],
        "dead_skills": [],
        "duplicate_groups": [],
        "trigger_issues": [],
        "model_fit_issues": [],
        "issues": [],
    }

    # 1. Inventory all skills (both Claude Code and Cursor)
    skill_search_dirs = list(SKILL_DIRS)

    all_skills = []
    seen_names: dict[str, list[dict]] = defaultdict(list)
    # Track the latest version of each cached plugin skill to avoid
    # counting multiple cached versions as duplicates.
    cache_dedup: dict[str, dict] = {}

    for base in skill_search_dirs:
        if not base.exists():
            continue
        for sm in base.rglob("SKILL.md"):
            path_str = str(sm)
            # Skip marketplace source repos — only count installed/cached copies
            if "marketplaces" in path_str:
                continue

            text = sm.read_text(errors="replace")
            meta = _parse_frontmatter(text)
            lines = len(text.splitlines())
            name = meta.get("name", sm.parent.name)
            desc = meta.get("description", "")
            has_scripts = _has_script(sm.parent)
            disable_model = meta.get("disable-model-invocation", False)

            # Determine source: user-owned (in ~/.claude/skills,
            # ~/.cursor/skills, or ~/.cursor/skills-cursor) vs
            # plugin-provided (in plugins/cache)
            is_plugin = "plugins/cache" in path_str
            # For plugin-cached skills, deduplicate by (marketplace, plugin, skill)
            # keeping only the most recent version path
            if is_plugin:
                # key = marketplace/plugin/skillname
                parts = Path(path_str).parts
                try:
                    ci = parts.index("cache")
                    key = f"{parts[ci+1]}/{parts[ci+2]}/{name}"
                except (ValueError, IndexError):
                    key = name
                existing = cache_dedup.get(key)
                if existing:
                    # Keep whichever has the newer mtime
                    if sm.stat().st_mtime > Path(existing["path"]).stat().st_mtime:
                        cache_dedup[key] = None  # will be replaced below
                    else:
                        continue
                cache_dedup[key] = {"placeholder": True}  # filled below

            entry = {
                "name": name,
                "path": path_str,
                "lines": lines,
                "description": desc,
                "desc_tokens": estimate_tokens(desc) if desc else 0,
                "disable_model_invocation": bool(disable_model),
                "has_scripts": has_scripts,
                "is_user_owned": not is_plugin,
                "source": "user" if not is_plugin else "plugin",
            }

            if is_plugin:
                parts = Path(path_str).parts
                try:
                    ci = parts.index("cache")
                    key = f"{parts[ci+1]}/{parts[ci+2]}/{name}"
                except (ValueError, IndexError):
                    key = name
                cache_dedup[key] = entry
            else:
                all_skills.append(entry)
                seen_names[name].append(entry)

    # Add deduplicated plugin skills
    for entry in cache_dedup.values():
        if isinstance(entry, dict) and "name" in entry:
            all_skills.append(entry)
            seen_names[entry["name"]].append(entry)

    results["total"] = len(all_skills)

    # 2. Cross-reference with transcript usage
    skill_reads = Counter()
    search_dirs = list(TRANSCRIPT_DIRS)
    if transcript_dirs:
        search_dirs.extend(Path(d) for d in transcript_dirs)

    for base in search_dirs:
        if not base.exists():
            continue
        for jsonl in base.rglob("*.jsonl"):
            if "agent-transcripts" not in str(jsonl):
                continue
            try:
                with open(jsonl) as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            msg = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        for block in msg.get("message", {}).get("content", []):
                            if not isinstance(block, dict):
                                continue
                            if (block.get("type") == "tool_use"
                                    and block.get("name") == "Read"):
                                path = block.get("input", {}).get("path", "")
                                if "SKILL.md" in path:
                                    parts = Path(path).parts
                                    for i, p in enumerate(parts):
                                        if p == "skills" and i + 1 < len(parts):
                                            skill_reads[parts[i + 1]] += 1
                                            break
            except Exception:
                continue

    # 3. Analyze each skill
    for s in all_skills:
        s["usage_count"] = skill_reads.get(s["name"], 0)
        results["skills"].append({
            "name": s["name"],
            "lines": s["lines"],
            "desc_tokens": s["desc_tokens"],
            "disable_model": s["disable_model_invocation"],
            "has_scripts": s["has_scripts"],
            "usage_count": s["usage_count"],
        })

    # 4. Dead skills: user-owned skills never read in any transcript
    # Only flag user-owned skills as dead — plugin skills are available but
    # not necessarily expected to be used regularly.
    for s in all_skills:
        if s["usage_count"] == 0 and s.get("is_user_owned", False):
            results["dead_skills"].append(s["name"])

    if results["dead_skills"]:
        n = len(results["dead_skills"])
        names = ", ".join(results["dead_skills"][:8])
        suffix = f" (+{n - 8} more)" if n > 8 else ""
        results["issues"].append(
            f"{n} user-owned skill(s) never triggered: {names}{suffix}"
        )

    # 5. Duplicate skills (same name provided by different sources)
    for name, entries in seen_names.items():
        if len(entries) > 1:
            # Deduplicate paths that differ only by cache version
            unique_sources = set()
            for e in entries:
                p = e["path"]
                if "plugins/cache" in p:
                    parts = Path(p).parts
                    try:
                        ci = parts.index("cache")
                        unique_sources.add(f"{parts[ci+1]}/{parts[ci+2]}")
                    except (ValueError, IndexError):
                        unique_sources.add(p)
                else:
                    unique_sources.add(p)
            if len(unique_sources) > 1:
                results["duplicate_groups"].append({
                    "name": name,
                    "locations": list(unique_sources),
                })

    if results["duplicate_groups"]:
        n = len(results["duplicate_groups"])
        names = ", ".join(g["name"] for g in results["duplicate_groups"][:5])
        results["issues"].append(
            f"{n} skill(s) duplicated across sources: {names}"
        )

    # 6. Trigger / description issues
    for s in all_skills:
        desc = s["description"]
        if not desc:
            results["trigger_issues"].append(
                f"{s['name']}: missing description (trigger will never fire)"
            )
        elif len(desc) < 30:
            results["trigger_issues"].append(
                f"{s['name']}: description too short ({len(desc)} chars) — "
                f"vague triggers cause false positives or missed activations"
            )
        elif estimate_tokens(desc) > 200:
            results["trigger_issues"].append(
                f"{s['name']}: description is {estimate_tokens(desc)} tokens — "
                f"bloated trigger descriptions waste context on every turn"
            )

    if results["trigger_issues"]:
        results["issues"].append(
            f"{len(results['trigger_issues'])} skill trigger issue(s) found"
        )

    # 7. Model-fit issues: skills with scripts that should use disable-model-invocation
    for s in all_skills:
        if s["has_scripts"] and not s["disable_model_invocation"]:
            results["model_fit_issues"].append(
                f"{s['name']}: has scripts but disable-model-invocation is false — "
                f"if the script does the heavy work, set this flag to avoid "
                f"burning tokens on model reasoning"
            )
        if s["lines"] > 300 and not s["has_scripts"]:
            results["model_fit_issues"].append(
                f"{s['name']}: {s['lines']} lines with no scripts — "
                f"large prompt-only skills are token-expensive; "
                f"consider extracting logic into a script"
            )

    if results["model_fit_issues"]:
        results["issues"].append(
            f"{len(results['model_fit_issues'])} model-fit issue(s) in skills"
        )

    return results


def find_transcripts(extra_dirs: list[str] | None = None) -> list[Path]:
    """Find all JSONL transcript files, sorted by modification time (newest first)."""
    jsonl_files = []
    search_dirs = list(TRANSCRIPT_DIRS)
    if extra_dirs:
        search_dirs.extend(Path(d) for d in extra_dirs)

    for base in search_dirs:
        if not base.exists():
            continue
        for jsonl in base.rglob("*.jsonl"):
            if "agent-transcripts" in str(jsonl):
                jsonl_files.append(jsonl)

    jsonl_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return jsonl_files


def analyze_session(jsonl_path: Path) -> dict:
    """Analyze a single session transcript for anti-patterns."""
    result = {
        "path": str(jsonl_path),
        "message_count": 0,
        "user_messages": 0,
        "assistant_messages": 0,
        "shell_calls": 0,
        "trivial_shell_calls": 0,
        "files_edited": 0,
        "reads_before_first_edit": 0,
        "first_edit_tool_index": None,
        "plan_mode_used": False,
        "jumped_to_code": False,
        "subagents_used": 0,
        "repeated_corrections": 0,
        "unique_tools": set(),
        "complexity_tier": "cheap",
        "topics": [],
    }

    messages = []
    try:
        with open(jsonl_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    messages.append(msg)
                except json.JSONDecodeError:
                    continue
    except Exception:
        return result

    result["message_count"] = len(messages)
    user_texts = []

    EXPLORE_TOOLS = {"Read", "Glob", "Grep", "WebSearch", "WebFetch"}
    EDIT_TOOLS = {"Write", "StrReplace", "EditNotebook"}
    tool_call_index = 0

    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("message", {}).get("content", [])

        if role == "user":
            result["user_messages"] += 1
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    user_texts.append(block.get("text", ""))

        elif role == "assistant":
            result["assistant_messages"] += 1
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    tool_name = block.get("name", "")
                    tool_input = block.get("input", {})
                    result["unique_tools"].add(tool_name)
                    tool_call_index += 1

                    if tool_name in EXPLORE_TOOLS:
                        if result["first_edit_tool_index"] is None:
                            result["reads_before_first_edit"] += 1

                    if tool_name == "Shell":
                        result["shell_calls"] += 1
                        cmd = tool_input.get("command", "")
                        if TRIVIAL_COMMANDS.match(cmd):
                            result["trivial_shell_calls"] += 1

                    elif tool_name in EDIT_TOOLS:
                        result["files_edited"] += 1
                        if result["first_edit_tool_index"] is None:
                            result["first_edit_tool_index"] = tool_call_index

                    elif tool_name == "SwitchMode":
                        if tool_input.get("target_mode_id") == "plan":
                            result["plan_mode_used"] = True

                    elif tool_name == "Task":
                        result["subagents_used"] += 1

                elif block.get("type") == "text":
                    text = block.get("text", "")
                    if "plan" in text.lower() and "mode" in text.lower():
                        result["plan_mode_used"] = True

    # Detect repeated corrections (user sending similar short messages in sequence)
    correction_streak = 0
    for i in range(1, len(user_texts)):
        prev = user_texts[i - 1].strip().lower()[:100]
        curr = user_texts[i].strip().lower()[:100]
        if len(curr) < 50 and (
            "no" in curr or "wrong" in curr or "fix" in curr
            or "again" in curr or "that's not" in curr or "try again" in curr
        ):
            correction_streak += 1
        else:
            if correction_streak >= 2:
                result["repeated_corrections"] += 1
            correction_streak = 0

    # Detect "jumped to code" — editing multiple files with minimal exploration
    if (result["files_edited"] > 3
            and result["reads_before_first_edit"] <= 1
            and not result["plan_mode_used"]):
        result["jumped_to_code"] = True

    # Classify complexity tier
    n_tools = len(result["unique_tools"])
    cheap = COMPLEXITY_THRESHOLDS["cheap"]
    standard = COMPLEXITY_THRESHOLDS["standard"]

    if (result["files_edited"] <= cheap["max_files_edited"]
            and result["message_count"] <= cheap["max_messages"]
            and n_tools <= cheap["max_unique_tools"]):
        result["complexity_tier"] = "cheap"
    elif (result["files_edited"] <= standard["max_files_edited"]
            and result["message_count"] <= standard["max_messages"]
            and n_tools <= standard["max_unique_tools"]):
        result["complexity_tier"] = "standard"
    else:
        result["complexity_tier"] = "frontier"

    result["unique_tools"] = list(result["unique_tools"])
    return result


def audit_sessions(max_sessions: int, extra_dirs: list[str] | None = None) -> dict:
    transcripts = find_transcripts(extra_dirs)[:max_sessions]
    results = {
        "sessions_analyzed": len(transcripts),
        "sessions": [],
        "summary": {},
        "issues": [],
    }

    if not transcripts:
        results["issues"].append("No session transcripts found to analyze.")
        return results

    all_sessions = []
    for t in transcripts:
        analysis = analyze_session(t)
        all_sessions.append(analysis)
        results["sessions"].append({
            "path": analysis["path"],
            "messages": analysis["message_count"],
            "files_edited": analysis["files_edited"],
            "plan_mode": analysis["plan_mode_used"],
            "jumped_to_code": analysis["jumped_to_code"],
            "reads_before_edit": analysis["reads_before_first_edit"],
            "shell_calls": analysis["shell_calls"],
            "trivial_shell": analysis["trivial_shell_calls"],
            "subagents": analysis["subagents_used"],
            "complexity_tier": analysis["complexity_tier"],
        })

    total_messages = sum(s["message_count"] for s in all_sessions)
    total_shell = sum(s["shell_calls"] for s in all_sessions)
    total_trivial = sum(s["trivial_shell_calls"] for s in all_sessions)
    total_edits = sum(s["files_edited"] for s in all_sessions)
    plan_used = sum(1 for s in all_sessions if s["plan_mode_used"])
    multi_file_sessions = sum(1 for s in all_sessions if s["files_edited"] > 5)
    multi_file_no_plan = sum(
        1 for s in all_sessions
        if s["files_edited"] > 5 and not s["plan_mode_used"]
    )
    total_subagents = sum(s["subagents_used"] for s in all_sessions)
    total_corrections = sum(s["repeated_corrections"] for s in all_sessions)
    kitchen_sink = sum(1 for s in all_sessions if s["message_count"] > 50)

    tier_counts = Counter(s["complexity_tier"] for s in all_sessions)
    jumped_to_code = sum(1 for s in all_sessions if s["jumped_to_code"])

    results["summary"] = {
        "avg_messages_per_session": round(total_messages / len(all_sessions), 1),
        "total_shell_calls": total_shell,
        "trivial_shell_pct": round(100 * total_trivial / total_shell, 1) if total_shell else 0,
        "plan_mode_usage": f"{plan_used}/{len(all_sessions)} sessions",
        "multi_file_without_plan": f"{multi_file_no_plan}/{multi_file_sessions} multi-file sessions",
        "jumped_to_code": jumped_to_code,
        "subagents_used": total_subagents,
        "repeated_corrections": total_corrections,
        "kitchen_sink_sessions": kitchen_sink,
        "complexity_tiers": {
            "cheap": tier_counts.get("cheap", 0),
            "standard": tier_counts.get("standard", 0),
            "frontier": tier_counts.get("frontier", 0),
        },
    }

    if kitchen_sink > 0:
        results["issues"].append(
            f"{kitchen_sink} session(s) had >50 messages — consider breaking into "
            f"shorter, scoped sessions"
        )
    if multi_file_no_plan > 0:
        results["issues"].append(
            f"{multi_file_no_plan} multi-file session(s) skipped Plan mode"
        )
    if total_shell and (total_trivial / total_shell) > 0.3:
        results["issues"].append(
            f"{total_trivial}/{total_shell} shell calls ({results['summary']['trivial_shell_pct']}%) "
            f"were trivial commands — run these directly in your terminal"
        )
    if total_corrections > 0:
        results["issues"].append(
            f"{total_corrections} instance(s) of repeated corrections — "
            f"consider /clear and rewriting the prompt"
        )
    if jumped_to_code > 0:
        results["issues"].append(
            f"{jumped_to_code} session(s) jumped straight to editing (>3 files) "
            f"with ≤1 read and no Plan mode — use Explore → Plan → Code"
        )
    n_cheap = tier_counts.get("cheap", 0)
    n_total = len(all_sessions)
    if n_cheap > 0:
        results["issues"].append(
            f"{n_cheap}/{n_total} session(s) were simple enough for a cheap model "
            f"(Haiku-tier) — ≤2 file edits, ≤10 messages, ≤3 tool types. "
            f"If you ran these on Opus/Sonnet, consider downgrading for similar tasks"
        )
    n_frontier = tier_counts.get("frontier", 0)
    if n_frontier > 0:
        frontier_no_plan = sum(
            1 for s in all_sessions
            if s["complexity_tier"] == "frontier" and not s["plan_mode_used"]
        )
        if frontier_no_plan > 0:
            results["issues"].append(
                f"{frontier_no_plan} complex session(s) (frontier-tier) didn't use "
                f"Plan mode — for heavy sessions consider opusplan or plan-then-execute"
            )

    return results


def score(config_results: dict, session_results: dict | None,
          skill_results: dict | None = None) -> dict:
    config_score = 10
    session_score = 10
    skill_score = 10

    # Config deductions
    config_files = config_results.get("config_files", config_results.get("claude_md", []))
    for cm in config_files:
        if cm["tokens"] > 5000:
            config_score -= 3
        elif cm["tokens"] > 3000:
            config_score -= 1

    mcp = config_results.get("mcp_servers", 0)
    mcp_count = mcp["count"] if isinstance(mcp, dict) else mcp
    if mcp_count > 10:
        config_score -= 2
    elif mcp_count > 5:
        config_score -= 1

    config_score = max(0, config_score)

    # Session deductions
    if session_results:
        summary = session_results.get("summary", {})

        if summary.get("kitchen_sink_sessions", 0) > 0:
            session_score -= 2

        multi_no_plan = summary.get("multi_file_without_plan", "0/0")
        try:
            n = int(multi_no_plan.split("/")[0])
            if n > 0:
                session_score -= min(n * 2, 4)
        except ValueError:
            pass

        jumped = summary.get("jumped_to_code", 0)
        if jumped > 0:
            session_score -= min(jumped * 2, 4)

        trivial_pct = summary.get("trivial_shell_pct", 0)
        if trivial_pct > 50:
            session_score -= 3
        elif trivial_pct > 30:
            session_score -= 1

        if summary.get("repeated_corrections", 0) > 2:
            session_score -= 2
        elif summary.get("repeated_corrections", 0) > 0:
            session_score -= 1

        if summary.get("subagents_used", 0) == 0 and summary.get("avg_messages_per_session", 0) > 30:
            session_score -= 1

        tiers = summary.get("complexity_tiers", {})
        total_sessions = sum(tiers.values()) or 1
        cheap_pct = 100 * tiers.get("cheap", 0) / total_sessions
        if cheap_pct >= 50:
            session_score -= 2
        elif cheap_pct >= 30:
            session_score -= 1

        session_score = max(0, session_score)

    # Skill deductions
    if skill_results:
        total = skill_results.get("total", 0)
        dead = len(skill_results.get("dead_skills", []))
        dupes = len(skill_results.get("duplicate_groups", []))
        trigger_issues = len(skill_results.get("trigger_issues", []))
        model_fit = len(skill_results.get("model_fit_issues", []))

        if total > 0 and dead / total > 0.5:
            skill_score -= 3
        elif dead > 5:
            skill_score -= 2
        elif dead > 2:
            skill_score -= 1

        skill_score -= min(dupes, 2)

        if trigger_issues > 5:
            skill_score -= 2
        elif trigger_issues > 0:
            skill_score -= 1

        if model_fit > 3:
            skill_score -= 2
        elif model_fit > 0:
            skill_score -= 1

        skill_score = max(0, skill_score)

    return {
        "config_score": config_score,
        "session_score": session_score if session_results else None,
        "skill_score": skill_score if skill_results else None,
    }


def format_report(config: dict, sessions: dict | None, scores: dict,
                  skills: dict | None = None) -> str:
    lines = ["# Agent Practice Audit", ""]

    # Config
    lines.append(f"## Config Health: {scores['config_score']}/10")
    lines.append("")
    config_files = config.get("config_files", config.get("claude_md", []))
    for cm in config_files:
        status = "OK" if cm["tokens"] <= 3000 else "WARN"
        platform = cm.get("platform", "")
        tag = f" [{platform}]" if platform else ""
        lines.append(f"- `{cm['path']}`: {cm['tokens']} tokens, "
                      f"{cm['lines']} lines [{status}]{tag}")
    skills_list = config.get("skills", [])
    cursor_skills = sum(1 for s in skills_list if s.get("platform") == "cursor")
    claude_skills = sum(1 for s in skills_list if s.get("platform") == "claude")
    lines.append(f"- Skills: {len(skills_list)} user-owned "
                 f"({claude_skills} Claude, {cursor_skills} Cursor)")
    mcp = config.get("mcp_servers", config.get("mcp_servers", 0))
    if isinstance(mcp, dict):
        lines.append(f"- MCP servers: {mcp['count']}")
        for src in mcp.get("sources", []):
            lines.append(f"  - {src['path']}: {src['count']} servers [{src['platform']}]")
    else:
        lines.append(f"- MCP servers: {mcp}")
    for issue in config["issues"]:
        lines.append(f"- **Issue**: {issue}")
    lines.append("")

    # Sessions
    if sessions:
        s = sessions["summary"]
        lines.append(f"## Session Patterns: {scores['session_score']}/10")
        lines.append(f"  (analyzed {sessions['sessions_analyzed']} recent sessions)")
        lines.append("")
        lines.append(f"- Avg session length: {s['avg_messages_per_session']} messages")
        lines.append(f"- Plan mode usage: {s['plan_mode_usage']}")
        lines.append(f"- Multi-file sessions without plan: {s['multi_file_without_plan']}")
        lines.append(f"- Jumped to code (no explore/plan): {s.get('jumped_to_code', 0)}")
        lines.append(f"- Shell calls: {s['total_shell_calls']} total, "
                      f"{s['trivial_shell_pct']}% trivial")
        lines.append(f"- Subagents used: {s['subagents_used']}")
        lines.append(f"- Repeated corrections: {s['repeated_corrections']}")
        lines.append(f"- Kitchen-sink sessions (>50 msgs): {s['kitchen_sink_sessions']}")
        tiers = s.get("complexity_tiers", {})
        lines.append(f"- Model-level fit: {tiers.get('cheap',0)} cheap (Haiku ok) / "
                      f"{tiers.get('standard',0)} standard (Sonnet) / "
                      f"{tiers.get('frontier',0)} frontier (Opus)")
        for issue in sessions["issues"]:
            lines.append(f"- **Issue**: {issue}")
        lines.append("")

    # Skills
    if skills:
        lines.append(f"## Skill Health: {scores['skill_score']}/10")
        lines.append(f"  ({skills['total']} skills installed)")
        lines.append("")

        dead = skills.get("dead_skills", [])
        if dead:
            names = ", ".join(dead[:10])
            suffix = f" (+{len(dead) - 10} more)" if len(dead) > 10 else ""
            lines.append(f"- Dead skills (never triggered): {names}{suffix}")

        dupes = skills.get("duplicate_groups", [])
        if dupes:
            for g in dupes[:5]:
                lines.append(f"- Duplicate: **{g['name']}** in {len(g['locations'])} sources")

        trigger = skills.get("trigger_issues", [])
        if trigger:
            lines.append(f"- Trigger issues: {len(trigger)}")
            for t in trigger[:5]:
                lines.append(f"  - {t}")

        model_fit = skills.get("model_fit_issues", [])
        if model_fit:
            lines.append(f"- Model-fit issues: {len(model_fit)}")
            for m in model_fit[:5]:
                lines.append(f"  - {m}")

        # Top used skills
        used = sorted(
            [s for s in skills["skills"] if s["usage_count"] > 0],
            key=lambda x: x["usage_count"], reverse=True,
        )
        if used:
            lines.append(f"- Most used: " + ", ".join(
                f"{s['name']}({s['usage_count']})" for s in used[:5]
            ))

        for issue in skills["issues"]:
            lines.append(f"- **Issue**: {issue}")
        lines.append("")

    # Top issues
    all_issues = config["issues"] + (sessions["issues"] if sessions else [])
    if skills:
        all_issues += skills["issues"]
    if all_issues:
        lines.append("## Top Recommendations")
        lines.append("")
        for i, issue in enumerate(all_issues[:5], 1):
            lines.append(f"{i}. {issue}")
    else:
        lines.append("## No issues found — clean bill of health!")

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Agent practice audit")
    parser.add_argument("--sessions", type=int, default=10,
                        help="Number of recent sessions to analyze")
    parser.add_argument("--config-only", action="store_true",
                        help="Skip session and skill analysis")
    parser.add_argument("--sessions-only", action="store_true",
                        help="Skip config and skill analysis")
    parser.add_argument("--skills-only", action="store_true",
                        help="Only run skill audit")
    parser.add_argument("--transcripts", nargs="*",
                        help="Additional transcript directories")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON")
    args = parser.parse_args()

    config_results = None
    session_results = None
    skill_results = None
    empty_config = {"config_files": [], "skills": [], "mcp_servers": {"count": 0, "sources": []}, "issues": []}

    if not args.sessions_only and not args.skills_only:
        config_results = audit_config()

    if not args.config_only and not args.skills_only:
        session_results = audit_sessions(args.sessions, args.transcripts)

    if not args.config_only and not args.sessions_only:
        skill_results = audit_skills(args.transcripts)

    scores = score(config_results or empty_config, session_results, skill_results)

    if args.json:
        output = {
            "config": config_results,
            "sessions": session_results,
            "skills": skill_results,
            "scores": scores,
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_report(
            config_results or empty_config,
            session_results,
            scores,
            skill_results,
        ))


if __name__ == "__main__":
    main()
