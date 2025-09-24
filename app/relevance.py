import os, re
from typing import List, Dict, Tuple
from utils import openai_chat

# Quick heuristic filters
KEY_TERMS = [
    r"\bSSDF\b", r"\bSBOM\b", r"\bSLSA\b",
    r"\bCI/CD\b", r"\bCI[- ]?CD\b", r"\bpipeline(s)?\b",
    r"\bSAST\b", r"\bDAST\b", r"\bIaC\b", r"\bKubernetes\b", r"\bcontainer(s)?\b",
    r"\bcode review\b", r"\bsupply[- ]chain\b", r"\bdependency\b",
    r"\bCUI\b", r"\bPII\b",
    r"\bNIST SP 800-53\b|\b800-53\b", r"\b800-171\b", r"\b800-218\b",
    r"\bFedRAMP\b", r"\bprovenance\b", r"\bsigning\b", r"\bartifact\b",
]

PROMPT = """You are filtering regulatory text for **software/IT engineering relevance**.
Keep sections that affect software development orgs: SDLC/SSDF, CI/CD, SAST/DAST, SBOM, supply-chain, IaC, containers/Kubernetes, cloud-native, handling CUI/PII in software, and mappings to 800-53/800-171/SSDF.

Return JSON with:
- kept_sections: [ {title:..., text:...} ]
Discard general policy prose unless it clearly impacts software teams.
"""

def _heuristic_hit(md: str) -> bool:
    hay = md.lower()
    for pat in KEY_TERMS:
        if re.search(pat, md, flags=re.IGNORECASE):
            return True
    return False

def filter_relevant(extracted: List[Dict]) -> List[Dict]:
    kept = []
    for item in extracted:
        md = item["markdown"]
        if not _heuristic_hit(md):
            # still ask LLM briefly to avoid misses
            pass

        res = openai_chat(
            system=PROMPT,
            user=f"SOURCE:\n\n{md[:16000]}",  # truncate for safety
            json_mode=True,
        )
        sections = res.get("kept_sections", [])
        if not sections:
            continue

        kept.append({
            **item,
            "kept_sections": sections
        })
    return kept
