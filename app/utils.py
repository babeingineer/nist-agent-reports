import os, re, json, time, random, string
from pathlib import Path
from typing import Optional, Any, Dict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def write_text(path: Path, text: str, encoding="utf-8"):
    ensure_dir(path.parent)
    path.write_text(text, encoding=encoding)

def safe_filename(name: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9._-]+", "_", name)
    return name.strip("_") or "file"

def run_id_str() -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))

def openai_chat(system: str, user: str, json_mode: bool = False) -> Any:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    client = OpenAI(api_key=api_key)

    print("Awaiting GPT's response...")
    resp = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role":"system","content":system},
            {"role":"user","content":user}
        ],
        response_format={"type": "json_object"} if json_mode else None,
        temperature=1,
    )
    print("Received")
    content = resp.choices[0].message.content
    if json_mode:
        try:
            return json.loads(content)
        except Exception:
            return {}
    return content
