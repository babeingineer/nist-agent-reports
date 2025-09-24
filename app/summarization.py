from typing import List, Dict, Tuple
from datetime import datetime
from utils import openai_chat

PROMPT = """Create a one-page Markdown brief for software/IT orgs about NIST SP 800 updates.
Include:
- Latest updates (with dates/versions) as bullets.
- Plain-language takeaways for software teams.
- Action checklist grouped by themes (Build/CI, Dependencies/SBOM, IaC/Cloud, Data/CUI-PII, Testing/Assurance).
- Map each action to 800-53 / 800-171 / SSDF codes.
- Footnote citations to sources (title + URL + date).

Return only Markdown."""

def build_summary(mapped: List[Dict], date_iso: str) -> Tuple[str, str, Dict]:
    # Build simple source table for grounding
    source_notes = []
    for it in mapped:
        source_notes.append({
            "id": it["id"],
            "title": it["title"],
            "url": it["url"],
            "published": it.get("published",""),
        })

    # Flatten for the LLM
    digest = []
    for it in mapped:
        for s in it["kept_sections"]:
            digest.append({
                "source_id": it["id"],
                "title": it["title"],
                "url": it["url"],
                "section_title": s.get("title",""),
                "text": s.get("text","")[:3000],
                "mappings": s.get("mappings", []),
                "published": it.get("published","")
            })

    user_text = f"""DATE: {date_iso}

SOURCES:
{source_notes}

FILTERED CONTENT:
{digest}
"""

    md = openai_chat(system=PROMPT, user=user_text, json_mode=False)
    filename = f"{date_iso}-nist-sp800-summary.md"
    meta = {"sources": source_notes}
    return md, filename, meta
