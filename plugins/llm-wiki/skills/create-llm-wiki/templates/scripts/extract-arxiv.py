#!/usr/bin/env python3
"""Extract an arXiv paper's LaTeX source and convert to markdown.

Usage:
    python extract-arxiv.py <arxiv-url-or-id> [OUTPUT.md] [--assets-dir DIR]

Examples:
    python extract-arxiv.py 2402.14207 raw/storm-paper.md --assets-dir raw/assets/storm-paper
    python extract-arxiv.py https://arxiv.org/abs/2402.14207 raw/storm-paper.md

Downloads the LaTeX source tarball from arXiv, finds the main .tex file,
converts it to markdown via pandoc (preserving LaTeX math as $...$ / $$...$$),
extracts figures into an assets directory, and rewrites image references to
point to the local copies.

Requires: pandoc
"""
import logging
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
from pathlib import Path

log = logging.getLogger("extract-arxiv")


def parse_arxiv_id(source: str) -> str:
    """Extract the arXiv ID from a URL or bare ID."""
    # https://arxiv.org/abs/2402.14207 or https://arxiv.org/pdf/2402.14207
    m = re.search(r"arxiv\.org/(?:abs|pdf|e-print)/([0-9]+\.[0-9]+(?:v\d+)?)", source)
    if m:
        return m.group(1)
    # bare ID like 2402.14207 or 2402.14207v2
    m = re.match(r"^([0-9]+\.[0-9]+(?:v\d+)?)$", source.strip())
    if m:
        return m.group(1)
    raise ValueError(f"Cannot parse arXiv ID from: {source}")


DOCX_EXTENSIONS = {".doc", ".docx", ".odt", ".rtf"}


def download_source(arxiv_id: str, dest_dir: Path) -> Path:
    """Download and extract the e-print tarball. Returns the extraction directory."""
    url = f"https://arxiv.org/e-print/{arxiv_id}"
    tarball = dest_dir / "source.tar.gz"

    log.info("Downloading e-print from %s", url)
    t0 = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": "llm-wiki-extract/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp, open(tarball, "wb") as f:
        data = resp.read()
        f.write(data)
    log.info("Downloaded %s bytes in %.1fs", f"{len(data):,}", time.time() - t0)

    extract_dir = dest_dir / "source"
    extract_dir.mkdir()

    # arXiv e-prints are usually gzipped tar, but sometimes just a single .tex
    try:
        with tarfile.open(tarball, "r:*") as tar:
            members = tar.getnames()
            log.info("Tarball contains %d files: %s", len(members), ", ".join(members[:10]))
            tar.extractall(path=extract_dir, filter="data")
            log.info("Extracted tarball to %s", extract_dir)
    except tarfile.ReadError:
        log.info("Not a tarball — detecting file type from magic bytes")
        # Not a tarball — could be a single gzipped .tex or a raw PDF/docx
        import gzip
        try:
            with gzip.open(tarball, "rb") as gz:
                content = gz.read()
            log.info("Decompressed gzip: %s bytes", f"{len(content):,}")
        except gzip.BadGzipFile:
            content = tarball.read_bytes()
            log.info("Raw file (not gzipped): %s bytes", f"{len(content):,}")

        # Detect file type from magic bytes
        if content[:5] == b"%PDF-":
            log.info("Detected PDF file")
            (extract_dir / "paper.pdf").write_bytes(content)
        elif content[:4] == b"PK\x03\x04":
            log.info("Detected DOCX/ZIP file")
            (extract_dir / "paper.docx").write_bytes(content)
        elif content[:4] in (b"\xd0\xcf\x11\xe0",):
            log.info("Detected DOC (OLE2) file")
            (extract_dir / "paper.doc").write_bytes(content)
        else:
            log.info("Assuming plain .tex file")
            (extract_dir / "main.tex").write_bytes(content)

    return extract_dir


def find_main_tex(extract_dir: Path) -> Path | None:
    """Find the main .tex file in the extracted source. Returns None if no .tex found."""
    tex_files = list(extract_dir.rglob("*.tex"))
    if not tex_files:
        return None
    if len(tex_files) == 1:
        return tex_files[0]

    # Heuristic: look for \documentclass — that's the main file
    for tex in tex_files:
        content = tex.read_text(errors="replace")
        if r"\documentclass" in content:
            return tex

    # Fallback: common names
    for name in ["main.tex", "paper.tex", "article.tex", "ms.tex"]:
        candidate = extract_dir / name
        if candidate.exists():
            return candidate

    # Last resort: largest .tex file
    return max(tex_files, key=lambda p: p.stat().st_size)


def detect_source_type(extract_dir: Path) -> str:
    """Detect what kind of source the e-print contains.

    Returns: 'latex', 'pdf', 'docx', or 'unknown'.
    """
    if list(extract_dir.rglob("*.tex")):
        return "latex"
    for ext in DOCX_EXTENSIONS:
        if list(extract_dir.rglob(f"*{ext}")):
            return "docx"
    if list(extract_dir.rglob("*.pdf")):
        return "pdf"
    return "unknown"


def fetch_metadata(arxiv_id: str) -> dict:
    """Fetch basic metadata from the arXiv API."""
    api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    log.info("Fetching metadata from %s", api_url)
    t0 = time.time()
    req = urllib.request.Request(api_url, headers={"User-Agent": "llm-wiki-extract/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            xml = resp.read().decode("utf-8")
        log.info("Metadata fetched in %.1fs (%s bytes)", time.time() - t0, f"{len(xml):,}")
    except Exception as e:
        log.warning("Metadata fetch failed: %s", e)
        return {}

    # Parse within the <entry> block to avoid picking up feed-level tags
    entry_match = re.search(r"<entry>(.*?)</entry>", xml, re.DOTALL)
    if not entry_match:
        return {"arxiv_id": arxiv_id, "url": f"https://arxiv.org/abs/{arxiv_id}"}
    entry = entry_match.group(1)

    title_match = re.search(r"<title[^>]*>(.*?)</title>", entry, re.DOTALL)
    title = re.sub(r"\s+", " ", title_match.group(1).strip()) if title_match else ""

    authors = re.findall(r"<author>\s*<name>(.*?)</name>", entry)

    pub_match = re.search(r"<published>(.*?)</published>", entry)
    published = pub_match.group(1)[:10] if pub_match else ""

    return {
        "title": title,
        "authors": authors,
        "published": published,
        "arxiv_id": arxiv_id,
        "url": f"https://arxiv.org/abs/{arxiv_id}",
    }


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf", ".eps", ".tiff", ".bmp"}


def extract_figures(extract_dir: Path, assets_dir: Path) -> dict[str, str]:
    """Copy figure files from the extracted source to assets_dir.

    Returns a mapping from original relative path (as referenced in LaTeX)
    to the new path relative to the wiki root (for use in markdown links).
    """
    log.info("Scanning for figures in %s", extract_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)
    path_map = {}

    for f in extract_dir.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        rel = f.relative_to(extract_dir)
        dest = assets_dir / rel.name
        if dest.exists() and dest.stat().st_size != f.stat().st_size:
            dest = assets_dir / f"{rel.stem}-{rel.parent.name}{rel.suffix}"

        shutil.copy2(f, dest)
        log.debug("  figure: %s → %s", rel, dest)

        rel_str = str(rel)
        stem_rel = str(rel.with_suffix(""))
        name = rel.name
        stem_name = rel.stem

        asset_path = str(dest)
        for key in {rel_str, stem_rel, name, stem_name}:
            path_map[key] = asset_path

    fig_count = len(set(path_map.values()))
    log.info("Copied %d figure(s) to %s", fig_count, assets_dir)
    return path_map


def rewrite_image_paths(md: str, path_map: dict[str, str]) -> str:
    """Rewrite markdown image references to point to local asset copies."""
    def replace_match(m):
        alt = m.group(1)
        orig_path = m.group(2)
        # Try exact match, then without leading ./
        clean = orig_path.lstrip("./")
        local = path_map.get(orig_path) or path_map.get(clean)
        if not local:
            # Try matching just the filename or stem
            from pathlib import PurePosixPath
            p = PurePosixPath(orig_path)
            local = path_map.get(p.name) or path_map.get(p.stem)
        if local:
            return f"![{alt}]({local})"
        return m.group(0)

    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace_match, md)


def _build_header(meta: dict) -> str:
    """Build a metadata header from arXiv metadata."""
    parts = []
    if meta.get("title"):
        parts.append(f"# {meta['title']}")
    if meta.get("authors"):
        parts.append(f"\n**Authors:** {', '.join(meta['authors'])}")
    if meta.get("published"):
        parts.append(f"**Published:** {meta['published']}")
    if meta.get("url"):
        parts.append(f"**arXiv:** {meta['url']}")
    parts.append("")
    parts.append("---")
    parts.append("")
    return "\n".join(parts)


def _resolve_inputs(content: str, parent: Path) -> str:
    """Recursively inline \\input{} and \\include{} files."""
    def replace_input(m):
        fname = m.group(1)
        if not fname.endswith(".tex"):
            fname += ".tex"
        p = parent / fname
        if p.exists():
            sub = p.read_text(errors="replace")
            return _resolve_inputs(sub, p.parent)
        return m.group(0)
    content = re.sub(r"\\input\{([^}]+)\}", replace_input, content)
    content = re.sub(r"\\include\{([^}]+)\}", replace_input, content)
    return content


def _extract_newcommands(content: str) -> dict[str, str]:
    """Extract \\newcommand definitions that expand to simple text."""
    macros = {}
    for m in re.finditer(
        r"\\(?:newcommand|renewcommand)\{\\(\w+)\}(?:\[\d+\])?\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}",
        content,
    ):
        name, body = m.group(1), m.group(2)
        clean = re.sub(r"\\[a-z]+\{([^}]*)\}", r"\1", body)
        clean = re.sub(r"\\xspace", "", clean)
        clean = re.sub(r"[{}]", "", clean).strip()
        if clean and len(clean) < 100:
            macros[name] = clean
    return macros


def convert_latex_to_markdown(tex_path: Path, meta: dict, path_map: dict[str, str] | None = None) -> str:
    """Convert LaTeX to markdown using pylatexenc (fast, no-hang)."""
    from pylatexenc.latex2text import LatexNodes2Text

    t0 = time.time()
    log.info("Reading %s", tex_path.name)
    content = tex_path.read_text(errors="replace")
    parent = tex_path.parent

    log.info("Extracting custom macros from preamble")
    macros = _extract_newcommands(content)

    log.info("Resolving \\input{}/\\include{} references")
    content = _resolve_inputs(content, parent)
    log.info("Resolved document: %s chars", f"{len(content):,}")

    macros.update(_extract_newcommands(content))
    log.info("Found %d custom macros: %s", len(macros), ", ".join(macros.keys()) if macros else "(none)")

    log.info("Stripping preamble")
    doc_m = re.search(r"\\begin\{document\}", content)
    if doc_m:
        content = content[doc_m.end():]
    end_m = re.search(r"\\end\{document\}", content)
    if end_m:
        content = content[:end_m.start()]
    log.info("Document body: %s chars", f"{len(content):,}")

    log.info("Expanding custom macros")
    for name, expansion in macros.items():
        content = re.sub(rf"\\{name}(?![a-zA-Z])", expansion.replace("\\", "\\\\"), content)

    log.info("Converting structural commands to markdown headings")
    content = re.sub(r"\\section\*?\{([^}]+)\}", r"\n## \1\n", content)
    content = re.sub(r"\\subsection\*?\{([^}]+)\}", r"\n### \1\n", content)
    content = re.sub(r"\\subsubsection\*?\{([^}]+)\}", r"\n#### \1\n", content)
    content = re.sub(r"\\paragraph\*?\{([^}]+)\}", r"\n**\1**\n", content)
    content = re.sub(r"\\maketitle", "", content)
    content = re.sub(r"\\begin\{abstract\}", "\n## Abstract\n", content)
    content = re.sub(r"\\end\{abstract\}", "\n", content)

    content = re.sub(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", r"![](\1)", content)
    content = re.sub(r"\\cite[pt]?\{([^}]+)\}", r"[cite:\1]", content)

    log.info("Running pylatexenc conversion")
    t1 = time.time()
    converter = LatexNodes2Text()
    body = converter.latex_to_text(content)
    log.info("pylatexenc done in %.1fs — produced %s chars", time.time() - t1, f"{len(body):,}")

    body = re.sub(r"\n{4,}", "\n\n\n", body)

    if path_map:
        log.info("Rewriting %d image path mappings", len(set(path_map.values())))
        body = rewrite_image_paths(body, path_map)

    result = _build_header(meta) + body
    log.info("Total conversion: %.1fs — final output %s chars", time.time() - t0, f"{len(result):,}")
    return result


def convert_doc_to_markdown(source_path: Path, meta: dict, assets_dir: Path | None = None) -> str:
    """Convert docx/odt/rtf to markdown via pandoc."""
    fmt_map = {".doc": "doc", ".docx": "docx", ".odt": "odt", ".rtf": "rtf"}
    fmt = fmt_map.get(source_path.suffix.lower())
    if not fmt:
        raise ValueError(f"Unsupported format: {source_path.suffix}")

    log.info("Converting %s via pandoc (format: %s)", source_path.name, fmt)
    t0 = time.time()

    pandoc_args = [
        "pandoc", str(source_path),
        "-f", fmt, "-t", "markdown",
        "--wrap=none", "--markdown-headings=atx",
    ]
    if assets_dir:
        pandoc_args.append(f"--extract-media={assets_dir}")

    result = subprocess.run(
        pandoc_args, capture_output=True, text=True, timeout=300,
        cwd=str(source_path.parent),
    )
    if result.returncode != 0:
        log.warning("pandoc exited %d: %s", result.returncode, result.stderr[:500])

    body = result.stdout
    if not body.strip():
        raise RuntimeError(f"pandoc produced empty output. stderr: {result.stderr[:500]}")

    log.info("pandoc done in %.1fs — produced %s chars", time.time() - t0, f"{len(body):,}")
    return _build_header(meta) + body


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract arXiv paper to markdown")
    parser.add_argument("source", help="arXiv URL or ID (e.g. 2402.14207)")
    parser.add_argument("output", nargs="?", help="Output .md path (default: derived from title)")
    parser.add_argument("--assets-dir", help="Directory to copy figures into (default: raw/assets/<slug>/)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    t_start = time.time()
    log.info("=== extract-arxiv starting ===")

    arxiv_id = parse_arxiv_id(args.source)
    log.info("Parsed arXiv ID: %s", arxiv_id)

    meta = fetch_metadata(arxiv_id)
    title = meta.get("title", arxiv_id)
    authors = meta.get("authors", [])
    log.info("Title: %s", title)
    log.info("Authors: %s", ", ".join(authors) if authors else "(unknown)")
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60]

    output_path = Path(args.output) if args.output else Path(f"{slug}.md")
    assets_dir = Path(args.assets_dir) if args.assets_dir else output_path.parent / "assets" / (output_path.stem)
    log.info("Output: %s", output_path)
    log.info("Assets: %s", assets_dir)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        extract_dir = download_source(arxiv_id, tmpdir)
        source_type = detect_source_type(extract_dir)
        log.info("Detected source type: %s", source_type)

        if source_type == "docx":
            doc_file = None
            for ext in DOCX_EXTENSIONS:
                found = list(extract_dir.rglob(f"*{ext}"))
                if found:
                    doc_file = found[0]
                    break
            log.info("No LaTeX source — found %s document", doc_file.suffix)
            md = convert_doc_to_markdown(doc_file, meta, assets_dir=assets_dir)

        elif source_type == "pdf":
            log.error("NO_LATEX_SOURCE: only a PDF available")
            print("NO_LATEX_SOURCE: This arXiv paper has no LaTeX source — only a PDF.", file=sys.stderr)
            print("To proceed, use extract-pdf.py instead.", file=sys.stderr)
            print("Note: PDF extraction may lose equation fidelity and costs more tokens.", file=sys.stderr)
            print("Ask the user if falling back to PDF extraction is OK.", file=sys.stderr)
            sys.exit(2)

        elif source_type == "unknown":
            all_files = [f.name for f in extract_dir.rglob("*") if f.is_file()]
            log.error("NO_LATEX_SOURCE: unrecognized format. Files: %s", ", ".join(all_files[:10]))
            print(f"NO_LATEX_SOURCE: Unrecognized source format. Files found: {', '.join(all_files[:10])}", file=sys.stderr)
            print("Ask the user how to proceed.", file=sys.stderr)
            sys.exit(2)

        else:
            main_tex = find_main_tex(extract_dir)
            log.info("Main .tex file: %s", main_tex.name)

            path_map = extract_figures(extract_dir, assets_dir)

            md = convert_latex_to_markdown(main_tex, meta, path_map)

    output_path.write_text(md)
    log.info("=== Done in %.1fs — %s chars → %s ===", time.time() - t_start, f"{len(md):,}", output_path)


if __name__ == "__main__":
    main()
