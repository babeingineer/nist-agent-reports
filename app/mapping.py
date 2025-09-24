import yaml, re
from typing import List, Dict, Any
from pathlib import Path
from utils import openai_chat

CONFIG_DIR = Path(__file__).parent / "config"

with open(CONFIG_DIR / "mappings.yaml", "r", encoding="utf-8") as f:
    RULES = yaml.safe_load(f)

PROMPT = """You map text to control frameworks.
Given a section, propose mappings with justification. Use only these frameworks:
- NIST 800-53 (e.g., SA-12, SA-15, CM-2, RA-5, SI-10)
- NIST 800-171 (e.g., 3.4.3, 3.14.1, 3.13.11)
- NIST 800-218 SSDF (e.g., PW.2, PW.4, PS.3, RV.1)

Return JSON: { mappings: [ {framework: "...", control: "...", reason: "..."} ] }
Keep concise, ensure the control identifiers actually exist.
"""

def _rule_matches(text: str) -> List[Dict[str, str]]:
    hits = []
    for rule in RULES.get("patterns", []):
        if re.search(rule["regex"], text, flags=re.IGNORECASE):
            for m in rule.get("maps_to", []):
                hits.append(m)
    return hits

def map_controls(filtered: List[Dict]) -> List[Dict]:
    mapped_items = []
    for item in filtered:
        new_sections = []
        for sec in item["kept_sections"]:
            text = sec.get("text", "")
            rule_hits = _rule_matches(text)

            llm = openai_chat(
                system=PROMPT,
                user=text[:6000],
                json_mode=True
            )
            llm_mappings = llm.get("mappings", [])
            combined = rule_hits + llm_mappings

            new_sections.append({
                **sec,
                "mappings": combined
            })

        mapped_items.append({
            **item,
            "kept_sections": new_sections
        })
    return mapped_items
