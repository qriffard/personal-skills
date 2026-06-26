#!/usr/bin/env python3
"""
Kobo → Personal LLM Wiki sync

Pulls highlights from the Kobo cloud API, enriches each book with Open Library
metadata (description, genres), and writes one raw markdown file per book into
~/wikis/personal/raw/ — ready for Claude to ingest into the wiki.

Credentials (required env vars):
    KOBO_EMAIL      — Kobo account email
    KOBO_PASSWORD   — Kobo account password

Usage:
    python kobo_to_wiki.py                      # sync books with highlights
    python kobo_to_wiki.py --refresh            # overwrite existing raw files
    python kobo_to_wiki.py --all                # include books with no highlights
    python kobo_to_wiki.py --wiki ~/wikis/personal  # override wiki path
"""

import os
import re
import sys
import json
import time
import argparse
import requests
from datetime import datetime
from pathlib import Path

KOBO_STORE_API = "https://storeapi.kobo.com"
OPEN_LIBRARY_API = "https://openlibrary.org"


# ── Kobo ──────────────────────────────────────────────────────────────────────

class KoboClient:
    CLIENT_KEY  = "MDhkMTQ3NjMtODA4Yy00ZjVmLWJjMDAtY2YxMjliN2NlMzE="
    APP_VERSION = "4.24.15116"

    def __init__(self, email: str, password: str):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": f"Kobo/{self.APP_VERSION}",
        })
        self._initialize()
        self._authenticate(email, password)

    def _initialize(self):
        r = self.session.get(f"{KOBO_STORE_API}/v1/initialization")
        r.raise_for_status()
        self.resources = r.json().get("Resources", {})

    def _authenticate(self, email: str, password: str):
        url = self.resources.get("UserAuthenticate", f"{KOBO_STORE_API}/v1/user/login")
        r = self.session.post(url, json={
            "AppVersion": self.APP_VERSION,
            "ClientKey": self.CLIENT_KEY,
            "LoginId": email,
            "Password": password,
            "UserKey": "",
        })
        r.raise_for_status()
        data = r.json()
        user_key = data.get("UserKey", "")
        if not user_key:
            raise RuntimeError(f"Kobo auth failed: {data}")
        self.session.headers["Authorization"] = f"Bearer {user_key}"
        print(f"✓ Kobo: logged in as {data.get('UserDisplayName', email)}")

    def get_library(self) -> list[dict]:
        url = self.resources.get("SyncCurrentAccount", f"{KOBO_STORE_API}/v1/library/sync")
        books: list[dict] = []
        sync_token = None
        while True:
            params = {"sync_token": sync_token} if sync_token else {}
            r = self.session.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            for key in ("NewEntitlement", "ChangedEntitlement", "Books"):
                for item in data.get(key, []):
                    book = item.get("BookEntitlement", item)
                    if book.get("BookMetadata") or book.get("Title"):
                        books.append(book)
            sync_token = data.get("SyncToken")
            if not sync_token or not data.get("HasMoreItems"):
                break
        print(f"✓ Kobo: found {len(books)} books")
        return books

    def get_highlights(self, volume_id: str) -> list[dict]:
        r = self.session.get(f"{KOBO_STORE_API}/v1/books/{volume_id}/annotations")
        if r.status_code == 404:
            return []
        r.raise_for_status()
        return r.json().get("Highlight", [])


def parse_book(entry: dict) -> dict:
    meta        = entry.get("BookMetadata", entry)
    reading     = entry.get("ReadingState", {})
    status_info = reading.get("StatusInfo", {})

    contributors = meta.get("ContributorRoles", [])
    author = ", ".join(
        c["Name"] for c in contributors if c.get("Role") == "Author"
    ) or meta.get("Author", "")

    isbn_raw = (meta.get("ISBN") or "").replace("-", "")
    isbn = isbn_raw if len(isbn_raw) == 13 and isbn_raw.isdigit() else None

    raw_status = status_info.get("Status", "")
    status = {"Finished": "Done", "Reading": "In progress", "InProgress": "In progress"}.get(raw_status, "Not started")

    def iso_date(s):
        if not s:
            return None
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date().isoformat()
        except Exception:
            return None

    last_mod = status_info.get("LastModified")
    pub = meta.get("PublicationDate") or ""

    return {
        "volume_id":    entry.get("VolumeId", ""),
        "title":        meta.get("Title", "").strip(),
        "author":       author,
        "isbn":         isbn,
        "status":       status,
        "year":         int(pub[:4]) if pub[:4].isdigit() else None,
        "date_started":  iso_date(last_mod) if raw_status in ("Reading", "InProgress") else None,
        "date_finished": iso_date(last_mod) if raw_status == "Finished" else None,
        "publisher":    meta.get("Publisher", ""),
        "language":     meta.get("Language", ""),
    }


# ── Open Library ──────────────────────────────────────────────────────────────

def fetch_open_library(book: dict) -> dict:
    """Returns {description, subjects, cover_url} from Open Library (best-effort)."""
    result = {"description": "", "subjects": [], "cover_url": ""}

    try:
        # Try ISBN first (most precise)
        if book["isbn"]:
            url = f"{OPEN_LIBRARY_API}/api/books?bibkeys=ISBN:{book['isbn']}&format=json&jscmd=data"
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            entry = data.get(f"ISBN:{book['isbn']}", {})
            if entry:
                _extract_ol_entry(entry, result)
                if result["description"]:
                    return result

        # Fallback: title + author search
        time.sleep(0.3)  # be polite to Open Library
        params = {"title": book["title"], "limit": 1, "fields": "key,title,subject,cover_i,first_sentence,description"}
        if book["author"]:
            params["author"] = book["author"].split(",")[0].strip()
        r = requests.get(f"{OPEN_LIBRARY_API}/search.json", params=params, timeout=10)
        r.raise_for_status()
        docs = r.json().get("docs", [])
        if docs:
            doc = docs[0]
            result["subjects"] = doc.get("subject", [])[:8]
            cover_id = doc.get("cover_i")
            if cover_id:
                result["cover_url"] = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
            # Fetch works page for description
            work_key = doc.get("key", "")
            if work_key:
                time.sleep(0.3)
                wr = requests.get(f"{OPEN_LIBRARY_API}{work_key}.json", timeout=10)
                if wr.ok:
                    work = wr.json()
                    desc = work.get("description", "")
                    if isinstance(desc, dict):
                        desc = desc.get("value", "")
                    result["description"] = desc.strip()

    except Exception as e:
        print(f"  (Open Library lookup failed: {e})")

    return result


def _extract_ol_entry(entry: dict, result: dict):
    desc = entry.get("description", "")
    if isinstance(desc, dict):
        desc = desc.get("value", "")
    result["description"] = (desc or "").strip()
    result["subjects"] = [s["name"] for s in entry.get("subjects", [])][:8]
    covers = entry.get("cover", {})
    result["cover_url"] = covers.get("medium", covers.get("small", ""))


# ── Slug ──────────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:60].rstrip("-")


# ── Writer ────────────────────────────────────────────────────────────────────

def format_date(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        return datetime.fromisoformat(iso).strftime("%b %d, %Y")
    except Exception:
        return iso


def write_raw_file(book: dict, highlights: list[dict], ol: dict, raw_dir: Path, today: str) -> Path:
    slug = f"kobo-{slugify(book['title'])}"
    out = raw_dir / f"{slug}.md"

    lines = ["---"]
    lines.append(f"title: {book['title']}")
    if book["author"]:
        lines.append(f"author: {book['author']}")
    if book["year"]:
        lines.append(f"year: {book['year']}")
    if book["isbn"]:
        lines.append(f"isbn: {book['isbn']}")
    if book["publisher"]:
        lines.append(f"publisher: {book['publisher']}")
    lines.append(f"kobo_status: {book['status']}")
    if book["date_started"]:
        lines.append(f"date_started: {book['date_started']}")
    if book["date_finished"]:
        lines.append(f"date_finished: {book['date_finished']}")
    if ol["subjects"]:
        lines.append(f"subjects: [{', '.join(ol['subjects'])}]")
    lines.append(f"source: kobo")
    lines.append(f"captured: {today}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {book['title']}")
    lines.append("")

    if ol["description"]:
        lines.append("## Summary")
        lines.append("")
        lines.append(ol["description"])
        lines.append("")

    highlight_texts = [h for h in highlights if (h.get("Text") or "").strip()]
    lines.append(f"## Highlights ({len(highlight_texts)})")
    lines.append("")

    for h in highlight_texts:
        text = h["Text"].strip()
        lines.append(f"> {text}")
        lines.append("")
        date_str = h.get("BookmarkDate", "")
        if date_str:
            try:
                pretty = datetime.fromisoformat(date_str.replace("Z", "+00:00")).strftime("%b %d, %Y")
                lines.append(f"*{pretty}*")
                lines.append("")
            except Exception:
                pass

    out.write_text("\n".join(lines), encoding="utf-8")
    return out


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Sync Kobo highlights to personal LLM wiki raw/")
    parser.add_argument("--refresh", action="store_true", help="Overwrite existing raw files")
    parser.add_argument("--all", dest="include_all", action="store_true", help="Include books with no highlights")
    parser.add_argument("--wiki", default="~/wikis/personal", help="Path to the personal wiki (default: ~/wikis/personal)")
    args = parser.parse_args()

    email    = os.environ.get("KOBO_EMAIL")
    password = os.environ.get("KOBO_PASSWORD")
    if not email or not password:
        sys.exit(
            "Missing credentials.\n"
            "Set KOBO_EMAIL and KOBO_PASSWORD, or run:\n"
            "  source ~/claude-code/everything_tracker/.env"
        )

    wiki_path = Path(args.wiki).expanduser()
    raw_dir   = wiki_path / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().date().isoformat()
    kobo  = KoboClient(email, password)
    books = kobo.get_library()

    written = []
    skipped = []

    for i, raw in enumerate(books, 1):
        book = parse_book(raw)
        if not book["title"]:
            continue

        highlights = []
        if book["volume_id"]:
            highlights = kobo.get_highlights(book["volume_id"])

        if not highlights and not args.include_all:
            continue

        slug     = f"kobo-{slugify(book['title'])}"
        out_path = raw_dir / f"{slug}.md"

        if out_path.exists() and not args.refresh:
            skipped.append(book["title"])
            print(f"  skip  {book['title']} (already in raw/; use --refresh to overwrite)")
            continue

        print(f"[{i}/{len(books)}] {book['title']} ({len(highlights)} highlights) — fetching metadata…")
        ol = fetch_open_library(book)

        path = write_raw_file(book, highlights, ol, raw_dir, today)
        written.append((book["title"], path.name, len(highlights)))
        print(f"  → wrote {path.name}")

    print(f"\n✓ Done — {len(written)} written, {len(skipped)} skipped")
    if written:
        print("\nNew files to ingest:")
        for title, fname, n in written:
            print(f"  raw/{fname}  ({n} highlights)  ← {title}")
    if skipped:
        print(f"\nAlready present (pass --refresh to overwrite): {len(skipped)} files")


if __name__ == "__main__":
    main()
