#!/usr/bin/env python3
"""Extract a compact heading outline from a markdown file.

Usage:
    python outline.py INPUT.md

Prints headings with line numbers to stdout, suitable for deciding which
sections to read during wiki ingest. Output is compact (typically <200 tokens).

Example output:
    L1    # Document Title
    L12   ## Overview
    L45   ## Architecture
    L45   ### Data Layer
    L78   ## Appendix
"""
import re
import sys
from pathlib import Path

TAB_SEPARATOR = re.compile(r"^={10,}$")
LIKELY_SECTION_TITLE = re.compile(
    r"^(?:\d+[\.\)]\s+)?"           # optional numbering like "1. " or "2) "
    r"[A-Z][A-Za-z0-9 &/:\-–—]{2,60}"  # capitalized phrase, max 60 chars
    r"$"
)
MULTI_SPACE = re.compile(r"  +")


def extract_outline(filepath: Path) -> list[tuple[int, str]]:
    lines = filepath.read_text(errors="replace").splitlines()
    headings = []
    has_md_headings = False

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("#") and " " in stripped:
            headings.append((i, stripped))
            has_md_headings = True
        elif TAB_SEPARATOR.match(stripped):
            headings.append((i, stripped[:40]))
        elif stripped.startswith("TAB:"):
            headings.append((i, stripped))

    if len(headings) > 3:
        return headings

    # Fallback for plain-text files (e.g. pdftotext output): detect lines that
    # look like section titles -- short, capitalized, surrounded by blank lines.
    headings = []
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or len(stripped) > 80 or len(stripped) < 3:
            continue
        prev_blank = (i <= 1) or not lines[i - 2].strip()
        next_blank = (i >= len(lines)) or not lines[i].strip()
        if MULTI_SPACE.search(stripped):
            continue
        if prev_blank and next_blank and LIKELY_SECTION_TITLE.match(stripped):
            headings.append((i, f"## {stripped}"))

    return headings


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} INPUT.md", file=sys.stderr)
        sys.exit(1)

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    headings = extract_outline(filepath)
    total_lines = sum(1 for _ in filepath.read_text(errors="replace").splitlines())

    print(f"Outline of {filepath.name} ({total_lines} lines):\n")
    for lineno, heading in headings:
        print(f"  L{lineno:<6} {heading}")

    print(f"\n{len(headings)} headings found.")


if __name__ == "__main__":
    main()
