import os, requests, io
from typing import List, Dict
from pathlib import Path
import trafilatura
import pdfplumber

from utils import safe_filename, ensure_dir, write_text

import trafilatura

def _extract_html_markdown(url: str) -> str:
    downloaded = trafilatura.fetch_url(url, no_ssl=True)
    if not downloaded:
        return ""

    try:
        # Newer trafilatura
        return trafilatura.extract(
            downloaded, output="markdown",
            include_links=True, include_images=False
        ) or ""
    except TypeError:
        # Older trafilatura: no `output` kw
        text = trafilatura.extract(downloaded) or ""
        # Optional: convert HTML→MD instead of plain text
        try:
            from markdownify import markdownify as mdify
            return mdify(downloaded) if downloaded else text
        except Exception:
            return text


def _extract_pdf_markdown(url: str) -> str:
    # naive: download and parse text by page, mark headers
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    with pdfplumber.open(io.BytesIO(r.content)) as pdf:
        parts = []
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            parts.append(f"\n\n## [Page {i}]\n\n{text}\n")
    return "\n".join(parts).strip()

def _looks_like_pdf(url: str) -> bool:
    return url.lower().endswith(".pdf")

def extract_all(sources: List[Dict], out_dir: Path) -> List[Dict]:
    ensure_dir(out_dir)
    items = []
    for s in sources:
        try:
            if _looks_like_pdf(s["url"]):
                md = _extract_pdf_markdown(s["url"])
            else:
                md = _extract_html_markdown(s["url"])
        except Exception as e:
            md = f"_Extraction failed: {e}_"

        if not md:
            continue

        # persist raw
        fn = safe_filename(f"{s['id']}-{s['title'][:80]}.md")
        write_text(out_dir / fn, md)

        items.append({
            **s,
            "markdown": md,
        })
    return items
