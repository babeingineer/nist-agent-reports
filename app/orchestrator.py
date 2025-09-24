import os
from datetime import datetime
from pathlib import Path

from discovery import discover_sources
from extraction import extract_all
from relevance import filter_relevant
from mapping import map_controls
from summarization import build_summary
from publishing import publish_as_pr
from utils import ensure_dir, write_text, run_id_str

ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", "./artifacts")).resolve()

def run_workflow(topic: str, limit: int = 10, dry_run: bool = False):
    rid = run_id_str()
    run_dir = ARTIFACTS_DIR / rid
    sources_dir = run_dir / "sources"
    docs_dir = Path("docs/summaries")
    ensure_dir(sources_dir)
    ensure_dir(docs_dir)

    # 1) Discover
    sources = discover_sources(topic=topic, limit=limit)
    # print(sources)

    # 2) Extract
    extracted = extract_all(sources, out_dir=sources_dir)
    # print(extracted)

    # 3) Relevance filter
    filtered = filter_relevant(extracted)
    print(filtered)

    # 4) Control mapping
    mapped = map_controls(filtered)
    

    # 5) Summarize (one page)
    date_iso = datetime.utcnow().date().isoformat()
    summary_md, summary_filename, meta = build_summary(mapped, date_iso)

    # Persist artifacts locally (for PR and audit)
    summary_path = Path("docs/summaries") / summary_filename
    write_text(summary_path, summary_md)

    # Also write raw per-source markdown
    for item in extracted:
        fn = f"{item['id']}.md"
        write_text(Path(f"sources/{date_iso}/{fn}"), item["markdown"])

    # 6) Publish PR
    pr_url = None
    if not dry_run:
        pr_url = publish_as_pr(
            branch=f"feat/nist-summary-{date_iso}-{rid}",
            title=f"NIST SP 800 Updates – {date_iso}",
            body=f"Automated summary for {date_iso}\n\nRun: `{rid}`",
            add_paths=[
                str(summary_path),
                *(str(p) for p in Path(f"sources/{date_iso}").glob("*.md"))
            ],
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
