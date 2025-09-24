import os, subprocess, tempfile, shutil
from pathlib import Path
from typing import List
from github import Github
from dotenv import load_dotenv

load_dotenv()

def _git(*args, check=True):
    return subprocess.run(["git", *args], check=check, capture_output=True, text=True)

def publish_as_pr(branch: str, title: str, body: str, add_paths: List[str]) -> str:
    repo_slug = os.getenv("GITHUB_REPO")
    token = os.getenv("GITHUB_TOKEN")
    actor = os.getenv("GITHUB_ACTOR")
    if not (repo_slug and token and actor):
        raise RuntimeError("Missing GITHUB_REPO/GITHUB_TOKEN/GITHUB_ACTOR")

    # Configure git
    _git("config", "user.name", os.getenv("GIT_AUTHOR_NAME", actor))
    _git("config", "user.email", os.getenv("GIT_AUTHOR_EMAIL", f"{actor}@users.noreply.github.com"))

    # Ensure index has files
    for p in add_paths:
        Path(p).parent.mkdir(parents=True, exist_ok=True)
    _git("add", *add_paths)
    _git("checkout", "-b", branch)
    _git("commit", "-m", title)

    origin_url = f"https://{actor}:{token}@github.com/{repo_slug}.git"
    _git("push", "-u", origin_url, branch)

    gh = Github(token)
    repo = gh.get_repo(repo_slug)
    pr = repo.create_pull(title=title, body=body, head=branch, base="main")
    return pr.html_url
