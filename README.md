# NIST SP 800 Agentic Workflow

This project automates retrieval, filtering, summarization, and publication of updates from the **NIST SP 800 series**.
The workflow collects recent publications, extracts and filters content relevant to IT/software development, generates a summary mapped to NIST controls, and opens a **Pull Request** in a target GitHub repository using the **GitHub MCP server (remote HTTP)**.

---

## Requirements

* Python **3.11+** (if running locally)
* A GitHub repository you can push to
* A GitHub **token** with:

  * `repo` scope (if using a Personal Access Token), or
  * `contents:write` and `pull_requests:write` (if using a GitHub App installation token)
* An **OpenAI API key** for filtering/mapping/summarization
* (Optional) **Docker** if you want to run in a container

---

## Installation (local Python)

```bash
git clone https://github.com/babeingineer/nist-agent-reports.git
cd nist-agent-reports
pip install -r requirements.txt
```

---

## Configuration

### Environment Variables

#### Required

| Variable           | Description                               | Example                              |
| ------------------ | ----------------------------------------- | ------------------------------------ |
| `OPENAI_API_KEY`   | OpenAI API key                            | `sk-...`                             |
| `GITHUB_REPO`      | Target GitHub repo in `owner/repo` format | `acme-inc/nist-reports`              |
| `MCP_GITHUB_URL`   | MCP endpoint URL                          | `https://api.githubcopilot.com/mcp/` |
| `MCP_GITHUB_AUTH`  | Must be `bearer`                          | `bearer`                             |
| `MCP_GITHUB_TOKEN` | GitHub PAT or App installation token      | `ghp_xxx...`                         |

#### Optional

| Variable      | Default | Description         |
| ------------- | ------- | ------------------- |
| `GITHUB_BASE` | `main`  | Base branch for PRs |

---

### YAML Config Files

Located under `app/config/`:

* **`ontology.yaml`** — domain concepts to track (e.g., CI/CD, SBOM, supply chain).
* **`mappings.yaml`** — maps filtered findings to NIST control families (800-53, 800-171, SSDF).

You can edit these to customize what the workflow considers relevant and how it maps to compliance frameworks.

---

## Usage (local)

### CLI

```bash
python app/main.py --topic "NIST SP 800 updates" --limit 5
```

### REST API

```bash
python app/main.py --serve
```

Call it:

```bash
curl -X POST http://localhost:8000/run \
  -H 'content-type: application/json' \
  -d '{"topic":"NIST SP 800 updates","limit":5}'
```

---

## Usage with Docker

### Build the image

```bash
docker build -t nist-agent .
```

### Run once (CLI mode)

```bash
docker run --rm \
  -e OPENAI_API_KEY=sk-... \
  -e GITHUB_REPO=owner/repo \
  -e MCP_GITHUB_URL=https://api.githubcopilot.com/mcp/ \
  -e MCP_GITHUB_AUTH=bearer \
  -e MCP_GITHUB_TOKEN=ghp_xxx... \
  nist-agent \
  python app/main.py --topic "NIST SP 800 updates" --limit 5
```

### Run as API server

```bash
docker run --rm -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e GITHUB_REPO=owner/repo \
  -e MCP_GITHUB_URL=https://api.githubcopilot.com/mcp/ \
  -e MCP_GITHUB_AUTH=bearer \
  -e MCP_GITHUB_TOKEN=ghp_xxx... \
  nist-agent \
  python app/main.py --serve
```

Then call:

```bash
curl -X POST http://localhost:8000/run \
  -H 'content-type: application/json' \
  -d '{"topic":"NIST SP 800 updates","limit":5}'
```

---

## Output

* **Summaries:** `docs/summaries/YYYY-MM-DD-nist-summary.md`
* **Raw sources:** `sources/YYYY-MM-DD/*.md`
* A GitHub Pull Request with the above files added.