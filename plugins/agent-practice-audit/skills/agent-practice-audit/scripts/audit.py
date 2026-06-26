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
from collections import Counter
from pathlib import Path


HOME = Path.home()

TRIVIAL_COMMANDS = re.compile(
    r"^(ls|pwd|echo|cat |head |tail |wc |file |which |whoami|hostname|date|"
    r"git status|git log|git diff|git branch|git remote|"
    r"npm --version|node --version|python3? --version)"
)

TRANSCRIPT_DIRS = [
    HOME / ".cursor" / "projects",
    HOME / ".claude" / "projects",
]


def estimate_tokens(text: str) -> int:
    return len(text) // 4


def audit_config() -> dict:
    results = {
        "claude_md": [],
        "skills": [],
        "mcp_servers": 0,
        "issues": [],
    }

    # Global CLAUDE.md
    global_claude = HOME / ".claude" / "CLAUDE.md"
    if global_claude.exists():
        text = global_claude.read_text(errors="replace")
        tokens = estimate_tokens(text)
        lines = len(text.splitlines())
        results["claude_md"].append({
            "path": str(global_claude),
            "tokens": tokens,
            "lines": lines,
        })
        if tokens > 3000:
            results["issues"].append(
                f"~/.claude/CLAUDE.md is {tokens} tokens — consider trimming "
                f"(loads every turn, never evicted)"
            )

    # Project-level CLAUDE.md files
    for projects_dir in [HOME / ".cursor" / "projects", HOME / ".claude" / "projects"]:
        if projects_dir.exists():
            for claude_md in projects_dir.rglob("CLAUDE.md"):
                if "agent-transcripts" in str(claude_md):
                    continue
                text = claude_md.read_text(errors="replace")
                tokens = estimate_tokens(text)
                results["claude_md"].append({
                    "path": str(claude_md),
                    "tokens": tokens,
                    "lines": len(text.splitlines()),
                })
                if tokens > 3000:
                    results["issues"].append(
                        f"{claude_md} is {tokens} tokens — review for bloat"
                    )

    # Skill inventory
    for skills_dir in [
        HOME / ".cursor" / "skills",
        HOME / ".claude" / "skills",
    ]:
        if not skills_dir.exists():
            continue
        for skill_md in skills_dir.rglob("SKILL.md"):
            text = skill_md.read_text(errors="replace")
            lines = len(text.splitlines())
            results["skills"].append({
                "path": str(skill_md),
                "lines": lines,
            })
            if lines > 500:
                results["issues"].append(
                    f"{skill_md.parent.name} SKILL.md is {lines} lines "
                    f"(recommended <500)"
                )

    # MCP server count
    for settings_path in [
        HOME / ".claude" / "settings.json",
        HOME / ".claude" / "settings.local.json",
        HOME / ".cursor" / "settings.json",
    ]:
        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text())
                servers = settings.get("mcpServers", {})
                results["mcp_servers"] += len(servers)
            except (json.JSONDecodeError, KeyError):
                pass

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
        "plan_mode_used": False,
        "subagents_used": 0,
        "repeated_corrections": 0,
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

                    if tool_name == "Shell":
                        result["shell_calls"] += 1
                        cmd = tool_input.get("command", "")
                        if TRIVIAL_COMMANDS.match(cmd):
                            result["trivial_shell_calls"] += 1

                    elif tool_name in ("Write", "StrReplace", "EditNotebook"):
                        result["files_edited"] += 1

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
            "shell_calls": analysis["shell_calls"],
            "trivial_shell": analysis["trivial_shell_calls"],
            "subagents": analysis["subagents_used"],
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

    results["summary"] = {
        "avg_messages_per_session": round(total_messages / len(all_sessions), 1),
        "total_shell_calls": total_shell,
        "trivial_shell_pct": round(100 * total_trivial / total_shell, 1) if total_shell else 0,
        "plan_mode_usage": f"{plan_used}/{len(all_sessions)} sessions",
        "multi_file_without_plan": f"{multi_file_no_plan}/{multi_file_sessions} multi-file sessions",
        "subagents_used": total_subagents,
        "repeated_corrections": total_corrections,
        "kitchen_sink_sessions": kitchen_sink,
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

    return results


def score(config_results: dict, session_results: dict | None) -> dict:
    config_score = 10
    session_score = 10

    # Config deductions
    for cm in config_results["claude_md"]:
        if cm["tokens"] > 5000:
            config_score -= 3
        elif cm["tokens"] > 3000:
            config_score -= 1

    oversized_skills = sum(1 for s in config_results["skills"] if s["lines"] > 500)
    config_score -= min(oversized_skills, 3)

    if config_results["mcp_servers"] > 10:
        config_score -= 2
    elif config_results["mcp_servers"] > 5:
        config_score -= 1

    config_score = max(0, config_score)

    # Session deductions
    if session_results:
        summary = session_results.get("summary", {})

        if summary.get("kitchen_sink_sessions", 0) > 0:
            session_score -= 2

        multi_no_plan = summary.get("multi_file_without_plan", "0/0")
        if multi_no_plan.startswith("0/") is False and not multi_no_plan.startswith("0/"):
            try:
                n = int(multi_no_plan.split("/")[0])
                if n > 0:
                    session_score -= min(n * 2, 4)
            except ValueError:
                pass

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

        session_score = max(0, session_score)

    return {
        "config_score": config_score,
        "session_score": session_score if session_results else None,
    }


def format_report(config: dict, sessions: dict | None, scores: dict) -> str:
    lines = ["# Agent Practice Audit", ""]

    # Config
    lines.append(f"## Config Health: {scores['config_score']}/10")
    lines.append("")
    for cm in config["claude_md"]:
        status = "OK" if cm["tokens"] <= 3000 else "WARN"
        lines.append(f"- `{cm['path']}`: {cm['tokens']} tokens, {cm['lines']} lines [{status}]")
    lines.append(f"- Skills: {len(config['skills'])} total")
    oversized = [s for s in config["skills"] if s["lines"] > 500]
    if oversized:
        for s in oversized:
            lines.append(f"  - WARN: `{s['path']}` is {s['lines']} lines")
    lines.append(f"- MCP servers: {config['mcp_servers']}")
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
        lines.append(f"- Shell calls: {s['total_shell_calls']} total, "
                      f"{s['trivial_shell_pct']}% trivial")
        lines.append(f"- Subagents used: {s['subagents_used']}")
        lines.append(f"- Repeated corrections: {s['repeated_corrections']}")
        lines.append(f"- Kitchen-sink sessions (>50 msgs): {s['kitchen_sink_sessions']}")
        for issue in sessions["issues"]:
            lines.append(f"- **Issue**: {issue}")
        lines.append("")

    # Top issues
    all_issues = config["issues"] + (sessions["issues"] if sessions else [])
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
    parser.add_argument("--config-only", action="store_true")
    parser.add_argument("--sessions-only", action="store_true")
    parser.add_argument("--transcripts", nargs="*",
                        help="Additional transcript directories")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON")
    args = parser.parse_args()

    config_results = None
    session_results = None

    if not args.sessions_only:
        config_results = audit_config()

    if not args.config_only:
        session_results = audit_sessions(args.sessions, args.transcripts)

    scores = score(
        config_results or {"claude_md": [], "skills": [], "mcp_servers": 0, "issues": []},
        session_results,
    )

    if args.json:
        output = {
            "config": config_results,
            "sessions": session_results,
            "scores": scores,
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_report(
            config_results or {"claude_md": [], "skills": [], "mcp_servers": 0, "issues": []},
            session_results,
            scores,
        ))


if __name__ == "__main__":
    main()
