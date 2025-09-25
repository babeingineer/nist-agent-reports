# app/orchestrator.py
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

from discovery import discover_sources
from extraction import extract_all
from relevance import filter_relevant
from mapping import map_controls
from summarization import build_summary
from publishing import publish_as_pr_via_mcp
from utils import ensure_dir, write_text, run_id_str
from dotenv import load_dotenv
load_dotenv()

ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", "./artifacts")).resolve()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def run_workflow(topic: str, limit: int = 10, dry_run: bool = False):
    rid = run_id_str()
    run_dir = ARTIFACTS_DIR / rid
    sources_dir = run_dir / "sources"
    ensure_dir(sources_dir)

    # 1) Discover
    sources = discover_sources(topic=topic, limit=limit)

    # 2) Extract
    extracted = extract_all(sources, out_dir=sources_dir)

    # 3) Relevance filter
    filtered = filter_relevant(extracted)

    # 4) Control mapping
    mapped = map_controls(filtered)

    # 5) Summarize (one page)
    date_iso = datetime.utcnow().date().isoformat()
    summary_md, summary_filename, meta = build_summary(mapped, date_iso)

    # Persist artifacts to local working tree (so you can inspect / CI capture)
    summary_path = Path("docs/summaries") / summary_filename
    write_text(summary_path, summary_md)

    # Also persist raw per-source markdown (organized by date)
    raw_dir = Path(f"sources/{date_iso}")
    ensure_dir(raw_dir)
    for item in extracted:
        fn = f"{item['id']}.md"
        write_text(raw_dir / fn, item["markdown"])

    # 6) Prepare files for MCP PR (path->content)
    files_for_pr: Dict[str, str] = {
        str(summary_path): _read_text(summary_path),
    }
    for p in raw_dir.glob("*.md"):
        files_for_pr[str(p)] = _read_text(p)

    pr_url = None
    if not dry_run:
        branch_name = f"feat/nist-summary-{date_iso}-{rid}"
        pr_body = f"Automated summary for {date_iso}\n\nRun: `{rid}`"
        pr_url = publish_as_pr_via_mcp(
            branch=branch_name,
            title=f"NIST SP 800 Updates – {date_iso}",
            body=pr_body,
            files=files_for_pr,
            commit_message=f"chore: ingest NIST summary for {date_iso}",
            base=os.getenv("GITHUB_BASE", "main"),
        )

    return {
        "run_id": rid,
        "topic": topic,
        "found": len(sources),
        "extracted": len(extracted),
        "kept": len(mapped),
        "summary_file": str(summary_path),
        "pr_url": pr_url,
        "meta": meta,
    }
