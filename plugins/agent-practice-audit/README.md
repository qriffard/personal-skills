# agent-practice-audit

Audit your coding agent practices for accuracy and cost efficiency. Inspects
CLAUDE.md config files, skill inventory, MCP servers, and recent session
transcripts for anti-patterns. Produces a scored report with actionable
recommendations based on best practices for Cursor and Claude Code.

## Usage

Say "audit my practices", "check my agent hygiene", or "agent health check".

## What it checks

- **Config health**: CLAUDE.md bloat, skill sizes, MCP server count
- **Session patterns**: kitchen-sink sessions, plan mode usage, trivial command
  delegation, repeated corrections, subagent usage
