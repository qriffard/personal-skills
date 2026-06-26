#!/usr/bin/env python3
"""Extract a YouTube transcript to clean markdown.

Usage:
    python extract-youtube.py URL [OUTPUT.md]
    python extract-youtube.py INPUT.vtt [OUTPUT.md]

If given a URL, uses yt-dlp to download subtitles first.
If given an existing .vtt/.srt file, converts it directly.
If OUTPUT is omitted, derives the filename from the video title or input file.

Requires: yt-dlp (for URL mode)
"""
import re
import subprocess
import sys
from pathlib import Path


def fetch_subtitles(url: str, output_dir: Path) -> tuple[Path, dict]:
    """Download subtitles + metadata via yt-dlp. Returns (vtt_path, metadata)."""
    info_result = subprocess.run(
        ["yt-dlp", "--print", "%(title)s\n%(channel)s\n%(upload_date)s\n%(duration)s\n%(id)s",
         "--no-download", url],
        capture_output=True, text=True, timeout=30,
    )
    lines = info_result.stdout.strip().split("\n")
    meta = {
        "title": lines[0] if len(lines) > 0 else "Unknown",
        "channel": lines[1] if len(lines) > 1 else "Unknown",
        "date": lines[2] if len(lines) > 2 else "Unknown",
        "duration": lines[3] if len(lines) > 3 else "Unknown",
        "video_id": lines[4] if len(lines) > 4 else "Unknown",
    }

    slug = re.sub(r"[^a-z0-9]+", "-", meta["title"].lower()).strip("-")[:60]
    out_template = str(output_dir / slug)

    subprocess.run(
        ["yt-dlp",
         "--write-auto-subs", "--write-subs",
         "--sub-lang", "en",
         "--sub-format", "vtt",
         "--skip-download",
         "-o", out_template + ".%(ext)s",
         url],
        capture_output=True, text=True, timeout=60,
    )

    for ext in [".en.vtt", ".vtt"]:
        candidate = Path(out_template + ext)
        if candidate.exists():
            return candidate, meta

    for vtt in output_dir.glob(f"{slug}*.vtt"):
        return vtt, meta

    raise FileNotFoundError(f"yt-dlp did not produce a subtitle file for: {url}")


def parse_vtt(vtt_path: Path) -> list[tuple[str, str]]:
    """Parse VTT into list of (timestamp, text) pairs, deduplicating."""
    content = vtt_path.read_text(errors="replace")
    content = re.sub(r"^WEBVTT.*?\n\n", "", content, flags=re.DOTALL)
    content = re.sub(r"<[^>]+>", "", content)

    blocks = re.split(r"\n\n+", content.strip())
    seen = set()
    entries = []

    for block in blocks:
        lines = block.strip().split("\n")
        timestamp = None
        text_lines = []

        for line in lines:
            ts_match = re.match(r"(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->", line)
            if ts_match:
                timestamp = ts_match.group(1)
                h, m, s = timestamp.split(":")
                timestamp = f"{int(h):02d}:{m}:{s[:2]}"
            elif line.strip() and not re.match(r"^\d+$", line.strip()):
                text_lines.append(line.strip())

        text = " ".join(text_lines)
        if text and text not in seen:
            seen.add(text)
            entries.append((timestamp or "", text))

    return entries


def format_transcript(entries: list[tuple[str, str]], meta: dict | None = None) -> str:
    parts = []

    if meta:
        parts.append(f"# {meta['title']}")
        parts.append("")
        parts.append(f"- **Channel**: {meta['channel']}")
        parts.append(f"- **Date**: {meta['date']}")
        parts.append(f"- **Duration**: {meta['duration']}s")
        if meta.get("video_id"):
            parts.append(f"- **URL**: https://www.youtube.com/watch?v={meta['video_id']}")
        parts.append("")
        parts.append("---")
        parts.append("")

    parts.append("## Transcript")
    parts.append("")

    for ts, text in entries:
        if ts:
            parts.append(f"**[{ts}]** {text}")
        else:
            parts.append(text)

    return "\n".join(parts)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <URL|FILE.vtt> [OUTPUT.md]", file=sys.stderr)
        sys.exit(1)

    source = sys.argv[1]
    is_url = source.startswith("http://") or source.startswith("https://")

    if is_url:
        output_dir = Path(sys.argv[2]).parent if len(sys.argv) > 2 else Path(".")
        vtt_path, meta = fetch_subtitles(source, output_dir)
        entries = parse_vtt(vtt_path)
        md = format_transcript(entries, meta)

        if len(sys.argv) > 2:
            output_path = Path(sys.argv[2])
        else:
            slug = re.sub(r"[^a-z0-9]+", "-", meta["title"].lower()).strip("-")[:60]
            output_path = output_dir / f"{slug}.md"
    else:
        vtt_path = Path(source)
        entries = parse_vtt(vtt_path)
        md = format_transcript(entries)
        output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else vtt_path.with_suffix(".md")

    output_path.write_text(md)
    print(f"Extracted {len(entries)} segments → {output_path}")


if __name__ == "__main__":
    main()
