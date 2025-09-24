import os
import argparse
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from orchestrator import run_workflow

class RunRequest(BaseModel):
    topic: str = "NIST SP 800 updates"
    limit: int = 10
    dry_run: bool = False

app = FastAPI(title="NIST SP 800 Agent")

@app.get("/healthz")
def health():
    return {"status": "ok"}

@app.post("/run")
def run(req: RunRequest):
    result = run_workflow(topic=req.topic, limit=req.limit, dry_run=req.dry_run)
    return result

def cli():
    parser = argparse.ArgumentParser(description="NIST SP 800 Agentic Workflow")
    parser.add_argument("--topic", default="NIST SP 800 updates")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--serve", action="store_true", help="Run REST server instead of one-shot")
    args = parser.parse_args()

    if args.serve:
        port = int(os.getenv("PORT", "8000"))
        uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
    else:
        res = run_workflow(topic=args.topic, limit=args.limit, dry_run=args.dry_run)
        print(res)

if __name__ == "__main__":
    cli()
