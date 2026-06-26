#!/usr/bin/env python3
"""Extract text from a PDF file to markdown.

Usage:
    python extract-pdf.py INPUT.pdf [OUTPUT.md]

If OUTPUT is omitted, writes to INPUT with .md extension.

Tries these backends in order:
  1. pymupdf4llm (best quality, markdown-aware)
  2. pymupdf / fitz (good quality)
  3. pdftotext CLI (poppler, widely available on macOS/Linux)
  4. Fallback: tells user to install one of the above
"""
import subprocess
import sys
from pathlib import Path


def try_pymupdf4llm(pdf_path: str) -> str | None:
    try:
        import pymupdf4llm
        return pymupdf4llm.to_markdown(pdf_path)
    except ImportError:
        return None


def try_pymupdf(pdf_path: str) -> str | None:
    try:
        import pymupdf
        doc = pymupdf.open(pdf_path)
        pages = []
        for i, page in enumerate(doc):
            text = page.get_text("text")
            if text.strip():
                pages.append(f"<!-- page {i + 1} -->\n{text}")
        return "\n\n---\n\n".join(pages)
    except ImportError:
        try:
            import fitz
            doc = fitz.open(pdf_path)
            pages = []
            for i, page in enumerate(doc):
                text = page.get_text("text")
                if text.strip():
                    pages.append(f"<!-- page {i + 1} -->\n{text}")
            return "\n\n---\n\n".join(pages)
        except ImportError:
            return None


def try_pdftotext(pdf_path: str) -> str | None:
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", pdf_path, "-"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    except FileNotFoundError:
        pass
    return None


def extract_pdf(pdf_path: str) -> str:
    for extractor in [try_pymupdf4llm, try_pymupdf, try_pdftotext]:
        text = extractor(pdf_path)
        if text:
            return text

    print(
        "No PDF extraction backend available.\n"
        "Install one of: pip install pymupdf4llm | pip install pymupdf | brew install poppler",
        file=sys.stderr,
    )
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} INPUT.pdf [OUTPUT.md]", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.with_suffix(".md")

    md = extract_pdf(str(input_path))

    name = input_path.stem
    header = f"# {name}\n\nSource: `{input_path.name}`\n\n---\n\n"
    full = header + md

    output_path.write_text(full)
    print(f"Extracted {len(full):,} chars → {output_path}")


if __name__ == "__main__":
    main()
