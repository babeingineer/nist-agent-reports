# NIST SP 800 Agentic Workflow

This project automates retrieval, filtering, summarization, and publication of updates from the **NIST SP 800 series**.
The workflow collects recent publications, extracts and filters content relevant to IT/software development, generates a summary mapped to NIST controls, and opens a **Pull Request** in a target GitHub repository using the **GitHub MCP server (remote HTTP)**.

---

## Requirements

* Python **3.11+**
* A GitHub repository you can push to
* A GitHub **token** with:

  * `repo` scope (if using a Personal Access Token), or
  * `contents:write` and `pull_requests:write` (if using a GitHub App installation token)
* An **OpenAI API key** for filtering/mapping/summarization

---

## Installation

Clone this repo and install dependencies:

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

#### Bash example

```bash
export OPENAI_API_KEY="sk-..."
export GITHUB_REPO="owner/repo"
export MCP_GITHUB_URL="https://api.githubcopilot.com/mcp/"
export MCP_GITHUB_AUTH="bearer"
export MCP_GITHUB_TOKEN="ghp_xxx..."
export GITHUB_BASE="main"
```

#### PowerShell example

```powershell
$env:OPENAI_API_KEY   = "sk-..."
$env:GITHUB_REPO      = "owner/repo"
$env:MCP_GITHUB_URL   = "https://api.githubcopilot.com/mcp/"
$env:MCP_GITHUB_AUTH  = "bearer"
$env:MCP_GITHUB_TOKEN = "ghp_xxx..."
$env:GITHUB_BASE      = "main"
```

---

### YAML Config Files

Located under `app/config/`:

* **`ontology.yaml`**
  Defines the domain concepts to track (e.g., software supply chain, CI/CD, PII handling).
  You can expand or modify these to adjust what the filter/mapper considers “relevant” content.

* **`mappings.yaml`**
  Defines how filtered findings map to NIST control families (800-53, 800-171, SSDF).
  You can edit this to align summaries with your organization’s compliance framework.

> **Tip:** If you extend `ontology.yaml` or `mappings.yaml`, rerun the workflow — the new definitions will automatically affect filtering and mapping.

---

## Usage

### One-shot (CLI)

```bash
python app/main.py --topic "NIST SP 800 updates" --limit 5
```

This will:

1. Discover up to 5 recent NIST SP 800 updates
2. Extract content to Markdown
3. Filter for software/IT relevance
4. Map to NIST controls (using `mappings.yaml`)
5. Generate a summary
6. Open a PR in `GITHUB_REPO` with:

   * `docs/summaries/YYYY-MM-DD-nist-summary.md`
   * `sources/YYYY-MM-DD/*.md`

### Run as REST API

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

## Output

* **Summaries:** `docs/summaries/YYYY-MM-DD-nist-summary.md`
* **Raw sources:** `sources/YYYY-MM-DD/*.md`
* A GitHub Pull Request with the above files added.