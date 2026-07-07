#!/usr/bin/env python3
"""Extract a podcast episode to a timestamped transcript in markdown.

Usage:
    python extract-podcast.py URL [OUTPUT.md] [--model NAME] [--lang CODE] [--keep-audio]

URL can be:
  - An Apple Podcasts episode link (podcasts.apple.com/.../id<N>?i=<EPISODE_ID>)
  - A direct podcast RSS/Atom feed URL (picks the most recent <item>)
  - A direct audio file URL (.mp3/.m4a/.wav/...)

Resolution order:
  1. If the feed publishes an official transcript (Podcasting 2.0
     <podcast:transcript> tag, text/plain or text/vtt or text/srt), download
     and use it directly — no transcription needed.
  2. Otherwise, download the audio and transcribe locally with whisper.cpp
     (`whisper-cli`). Requires `brew install ffmpeg whisper-cpp`. The ggml
     model is auto-downloaded once to ~/.cache/whisper-cpp/ (~1.5GB for the
     default large-v3-turbo) and reused on every later call.

Spotify-only episodes aren't supported (no public audio URL) — find the same
episode on Apple Podcasts or the show's RSS feed instead.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

WHISPER_CACHE = Path.home() / ".cache" / "whisper-cpp"
MODEL_URLS = {
    "tiny": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin",
    "base": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin",
    "small": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
    "medium": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin",
    "large-v3": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin",
    "large-v3-turbo": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin",
}
NS = {"podcast": "https://podcastindex.org/namespace/1.0"}


def fetch_url(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "llm-wiki-podcast-extract/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def slugify(text: str, max_len: int = 60) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:max_len]


def resolve_apple_podcasts(url: str) -> dict:
    """Resolve an Apple Podcasts episode URL via the iTunes Lookup API."""
    collection_match = re.search(r"/id(\d+)", url)
    episode_match = re.search(r"[?&]i=(\d+)", url)
    if not collection_match:
        raise ValueError(f"Couldn't find a podcast id in URL: {url}")
    collection_id = collection_match.group(1)
    if not episode_match:
        raise ValueError(
            "This looks like a podcast (show) link, not a specific episode. "
            "Open the episode itself so the URL has an `?i=<id>` parameter."
        )
    episode_id = int(episode_match.group(1))

    for limit in (20, 50, 200):
        data = json.loads(fetch_url(
            f"https://itunes.apple.com/lookup?id={collection_id}&entity=podcastEpisode&limit={limit}"
        ))
        for item in data.get("results", []):
            if item.get("trackId") == episode_id:
                return {
                    "title": item["trackName"],
                    "podcast": item.get("collectionName", "Unknown"),
                    "date": (item.get("releaseDate") or "")[:10],
                    "duration_s": (item.get("trackTimeMillis") or 0) // 1000,
                    "audio_url": item.get("episodeUrl"),
                    "description": item.get("shortDescription") or item.get("description", ""),
                    "feed_url": item.get("feedUrl"),
                    "episode_guid": item.get("episodeGuid"),
                    "episode_page": url,
                }
        if len(data.get("results", [])) < limit:
            break
    raise ValueError(
        f"Episode id {episode_id} not found in the last {limit} episodes of this "
        "podcast's feed — it may be too old for Apple's API window. Find the "
        "direct RSS enclosure or mp3 URL instead and pass that."
    )


def find_official_transcript(feed_url: str, episode_guid: str) -> tuple[str, str] | None:
    """Look for a Podcasting 2.0 <podcast:transcript> tag on the matching <item>."""
    try:
        root = ET.fromstring(fetch_url(feed_url))
    except Exception:
        return None
    for item in root.iter("item"):
        guid_el = item.find("guid")
        if guid_el is None or (guid_el.text or "").strip() != episode_guid:
            continue
        for transcript in item.findall("podcast:transcript", NS):
            ttype = transcript.get("type", "")
            turl = transcript.get("url")
            if turl and ("text" in ttype or "vtt" in ttype or "srt" in ttype):
                return turl, ttype
    return None


def resolve_rss_feed(url: str) -> dict:
    """Pick the most recent <item> from a direct RSS feed URL."""
    root = ET.fromstring(fetch_url(url))
    item = next(root.iter("item"), None)
    if item is None:
        raise ValueError(f"No <item> found in feed: {url}")
    enclosure = item.find("enclosure")
    channel_title = root.findtext(".//channel/title") or "Unknown podcast"
    guid_el = item.find("guid")
    return {
        "title": item.findtext("title") or "Unknown episode",
        "podcast": channel_title,
        "date": item.findtext("pubDate") or "",
        "duration_s": 0,
        "audio_url": enclosure.get("url") if enclosure is not None else None,
        "description": item.findtext("description") or "",
        "feed_url": url,
        "episode_guid": (guid_el.text or "").strip() if guid_el is not None else None,
        "episode_page": item.findtext("link") or url,
    }


def resolve_source(url: str) -> dict:
    if "open.spotify.com" in url:
        raise ValueError(
            "Spotify episode pages don't expose a public audio URL. Find the "
            "same episode on Apple Podcasts, or the show's RSS feed, and use "
            "that link instead."
        )
    if "podcasts.apple.com" in url:
        return resolve_apple_podcasts(url)
    if url.endswith((".xml", ".rss")) or "/feed" in url:
        return resolve_rss_feed(url)
    if re.search(r"\.(mp3|m4a|wav|aac|ogg)(\?|$)", url):
        return {
            "title": Path(url.split("?")[0]).stem,
            "podcast": "Unknown",
            "date": "",
            "duration_s": 0,
            "audio_url": url,
            "description": "",
            "feed_url": None,
            "episode_guid": None,
            "episode_page": url,
        }
    raise ValueError(
        f"Unrecognized podcast URL: {url}\n"
        "Supported: Apple Podcasts episode links, direct RSS feed URLs, or "
        "direct audio file URLs."
    )


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "llm-wiki-podcast-extract/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as f:
        shutil.copyfileobj(resp, f)


def ensure_model(model: str) -> Path:
    if model not in MODEL_URLS:
        raise ValueError(f"Unknown model '{model}'. Choose from: {', '.join(MODEL_URLS)}")
    model_path = WHISPER_CACHE / f"ggml-{model}.bin"
    if not model_path.exists():
        print(f"Downloading whisper model '{model}' (one-time, ~1.5GB for large models)...", file=sys.stderr)
        WHISPER_CACHE.mkdir(parents=True, exist_ok=True)
        download(MODEL_URLS[model], model_path)
    return model_path


def parse_srt(srt_path: Path) -> list[tuple[str, str]]:
    content = srt_path.read_text(errors="replace")
    blocks = re.split(r"\n\n+", content.strip())
    entries = []
    for block in blocks:
        lines = block.strip().split("\n")
        timestamp = None
        text_lines = []
        for line in lines:
            ts_match = re.match(r"(\d{2}:\d{2}:\d{2}),\d{3}\s*-->", line)
            if ts_match:
                timestamp = ts_match.group(1)
            elif line.strip() and not re.match(r"^\d+$", line.strip()):
                text_lines.append(line.strip())
        text = " ".join(text_lines)
        if text:
            entries.append((timestamp or "", text))
    return entries


def transcribe(audio_path: Path, model: str, lang: str, keep_audio: bool) -> list[tuple[str, str]]:
    for tool in ("ffmpeg", "whisper-cli"):
        if shutil.which(tool) is None:
            raise RuntimeError(
                f"'{tool}' not found. Install with: brew install ffmpeg whisper-cpp"
            )

    model_path = ensure_model(model)
    wav_path = audio_path.with_suffix(".wav")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(audio_path), "-ar", "16000", "-ac", "1",
         "-c:a", "pcm_s16le", str(wav_path)],
        check=True, capture_output=True,
    )

    srt_base = audio_path.with_suffix("")
    subprocess.run(
        ["whisper-cli", "-m", str(model_path), "-f", str(wav_path),
         "-l", lang, "-osrt", "-of", str(srt_base)],
        check=True, capture_output=True, text=True,
    )

    entries = parse_srt(srt_base.with_suffix(".srt"))

    if not keep_audio:
        audio_path.unlink(missing_ok=True)
        wav_path.unlink(missing_ok=True)
        srt_base.with_suffix(".srt").unlink(missing_ok=True)

    return entries


def format_output(meta: dict, entries: list[tuple[str, str]], transcript_source: str) -> str:
    parts = [f"# {meta['title']}", ""]
    parts.append(f"- **Podcast**: {meta['podcast']}")
    if meta.get("date"):
        parts.append(f"- **Date**: {meta['date']}")
    if meta.get("duration_s"):
        parts.append(f"- **Duration**: {meta['duration_s'] // 60}m{meta['duration_s'] % 60:02d}s")
    parts.append(f"- **URL**: {meta['episode_page']}")
    parts.append(f"- **Transcript source**: {transcript_source}")
    if meta.get("description"):
        parts.append("")
        parts.append(meta["description"].strip())
    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append("## Transcript")
    parts.append("")
    for ts, text in entries:
        parts.append(f"**[{ts}]** {text}" if ts else text)
    return "\n".join(parts)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("url")
    p.add_argument("output", nargs="?")
    p.add_argument("--model", default="large-v3-turbo", choices=list(MODEL_URLS))
    p.add_argument("--lang", default="auto", help="whisper language code, e.g. fr, en (default: auto-detect)")
    p.add_argument("--keep-audio", action="store_true", help="keep the downloaded mp3/wav instead of deleting")
    args = p.parse_args()

    meta = resolve_source(args.url)
    if not meta.get("audio_url"):
        print("Resolved metadata but found no audio URL — cannot proceed.", file=sys.stderr)
        sys.exit(2)

    output_path = Path(args.output) if args.output else Path(f"{slugify(meta['title'])}.md")

    transcript_source = "official (podcast:transcript)"
    entries = None
    if meta.get("feed_url") and meta.get("episode_guid"):
        found = find_official_transcript(meta["feed_url"], meta["episode_guid"])
        if found:
            turl, ttype = found
            raw = fetch_url(turl).decode("utf-8", errors="replace")
            if "vtt" in ttype or "srt" in ttype:
                tmp = output_path.with_suffix(".tmp_transcript")
                tmp.write_text(raw)
                entries = parse_srt(tmp) if "srt" in ttype else [("", line) for line in raw.splitlines() if line.strip()]
                tmp.unlink(missing_ok=True)
            else:
                entries = [("", raw)]

    if entries is None:
        transcript_source = f"whisper.cpp ({args.model})"
        audio_path = output_path.with_name(f"{output_path.stem}-audio").with_suffix(
            Path(meta["audio_url"].split("?")[0]).suffix or ".mp3"
        )
        print(f"Downloading audio from {meta['audio_url']}...", file=sys.stderr)
        download(meta["audio_url"], audio_path)
        print("Transcribing with whisper.cpp (this can take several minutes)...", file=sys.stderr)
        entries = transcribe(audio_path, args.model, args.lang, args.keep_audio)

    md = format_output(meta, entries, transcript_source)
    output_path.write_text(md)
    print(f"Extracted {len(entries)} segments → {output_path} ({transcript_source})")


if __name__ == "__main__":
    main()
