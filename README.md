# NIST SP 800 Agentic Workflow

Automates discovery, extraction, filtering, control mapping, summarization, and PR publishing for **NIST SP 800** updates.

## Features
- Search (SerpAPI) + NIST fallback
- HTML/PDF to Markdown (trafilatura, pdfplumber)
- Relevance filter (rules + LLM)
- Mapping to **800-53 / 800-171 / SSDF**
- One-page Markdown summary
- GitHub PR creation

## Quick Start

```bash
# Set secrets
export OPENAI_API_KEY=...
export SERPAPI_KEY=...            # optional but recommended
export GITHUB_TOKEN=...           # PAT or GitHub App token with repo:write
export GITHUB_REPO=org/repo
export GITHUB_ACTOR=your-gh-username
export GIT_AUTHOR_NAME="Your Name"
export GIT_AUTHOR_EMAIL="you@example.com"

# Local run (CLI)
pip install -r requirements.txt
python app/main.py --topic "NIST SP 800 updates" --limit 10

# REST server
python app/main.py --serve
# Then POST:
curl -X POST localhost:8000/run -H "content-type: application/json" \
  -d '{"topic":"NIST SP 800 updates","limit":10}'
````

## Docker

```bash
docker build -t nist-agent:latest .
docker run --rm -p 8000:8000 \
  -e OPENAI_API_KEY -e SERPAPI_KEY \
  -e GITHUB_TOKEN -e GITHUB_REPO -e GITHUB_ACTOR \
  -e GIT_AUTHOR_NAME -e GIT_AUTHOR_EMAIL \
  -v $(pwd):/app \
  nist-agent:latest
```

## Outputs

* `docs/summaries/YYYY-MM-DD-nist-sp800-summary.md`
* `sources/YYYY-MM-DD/srcXX-*.md`
* Automated PR against `main`.

## Notes

* Default model: `gpt-5-turbo` in `utils.openai_chat` — adjust to your available model.
* All claims in the summary are grounded by the extracted source sections.
* Edit `app/config/mappings.yaml` to refine control mappings; add terms in `ontology.yaml`.

## Security

* Do **not** commit secrets. Use env vars or a secrets manager.
* Prefer a GitHub App or a PAT with least privilege.

## Tests (suggested)

* Add fixtures for HTML/PDF pages and run extraction + relevance locally.
* Use a sandbox repo to validate PR flow.