import os
import json
import asyncio
from typing import Dict, Optional, Any, List

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


class MCPGitHubPublisher:
    """
    Publishes changes via the GitHub MCP server over HTTP.

    REQUIRED env:
      - GITHUB_REPO=owner/repo
      - MCP_GITHUB_URL=https://api.githubcopilot.com/mcp/
      - MCP_GITHUB_AUTH=bearer
      - MCP_GITHUB_TOKEN=<PAT or GitHub App installation token with repo write>

    Notes:
      * Remote-only (no local/stdio path).
      * The server must expose 'repos' and 'pull_requests' toolsets.
    """

    def __init__(self):
        # target repo
        self.repo_slug = os.getenv("GITHUB_REPO")
        if not self.repo_slug or "/" not in self.repo_slug:
            raise RuntimeError("GITHUB_REPO must be set as 'owner/repo'")
        self.owner, self.repo = self.repo_slug.split("/", 1)

        # MCP remote settings (all required)
        self.url = os.getenv("MCP_GITHUB_URL")
        self.auth_mode = os.getenv("MCP_GITHUB_AUTH", "bearer")
        self.auth_token = os.getenv("MCP_GITHUB_TOKEN")

        if not self.url:
            raise RuntimeError("MCP_GITHUB_URL must be set (e.g., https://api.githubcopilot.com/mcp/)")
        if self.auth_mode.lower() != "bearer":
            raise RuntimeError("Set MCP_GITHUB_AUTH=bearer for non-interactive server-to-server auth")
        if not self.auth_token:
            raise RuntimeError("MCP_GITHUB_TOKEN must be set to a GitHub token with repo write access")

        self.base = os.getenv("GITHUB_BASE", "main")

    def _make_transport(self) -> StreamableHttpTransport:
        # Authorization header for bearer token auth
        return StreamableHttpTransport(
            url=self.url,
            headers={"Authorization": f"Bearer {self.auth_token}"},
        )

    @staticmethod
    def _tool_name(tool_obj: Any) -> Optional[str]:
        """
        Extract a tool name from either a Pydantic Tool model or a plain dict.
        """
        # Pydantic model (has attribute access)
        name = getattr(tool_obj, "name", None)
        if isinstance(name, str) and name:
            return name
        # Dict-like
        if isinstance(tool_obj, dict):
            n = tool_obj.get("name")
            if isinstance(n, str) and n:
                return n
        # Fallback: try model_dump if available
        if hasattr(tool_obj, "model_dump"):
            try:
                n = tool_obj.model_dump().get("name")
                if isinstance(n, str) and n:
                    return n
            except Exception:
                pass
        return None

    @classmethod
    def _find_tool(cls, tools: List[Any], suffix: str) -> Optional[str]:
        """
        Match by suffix to be robust to namespacing (e.g., 'repos/create_branch').
        """
        for t in tools:
            n = cls._tool_name(t)
            if n and n.endswith(suffix):
                return n
        return None

    @classmethod
    def _debug_tool_names(cls, tools: List[Any]) -> str:
        names = []
        for t in tools:
            n = cls._tool_name(t)
            if n:
                names.append(n)
        return ", ".join(sorted(names)) if names else "(no tools reported)"

    @staticmethod
    async def _call(client: Client, tool_name: str, args: dict) -> Any:
        result = await client.call_tool(tool_name, args)
        if not result or not result.content:
            return None
        c = result.content[0]
        # Prefer JSON content when available
        t = getattr(c, "type", None)
        if t == "json":
            return getattr(c, "data", None)
        if t == "text":
            txt = getattr(c, "text", "")
            try:
                return json.loads(txt)
            except Exception:
                return txt
        # Some servers might return 'blob' or other types; just return repr
        return getattr(c, "text", None) or getattr(c, "data", None) or str(c)

    async def publish_as_pr(
        self,
        branch: str,
        title: str,
        body: str,
        files: Dict[str, str],
        commit_message: Optional[str] = None,
        base: Optional[str] = None,
    ) -> str:
        base = base or self.base
        commit_message = commit_message or title

        transport = self._make_transport()
        client = Client(transport)

        async with client:
            tools = await client.list_tools()

            create_branch_tool = self._find_tool(tools, "create_branch")
            upsert_file_tool  = self._find_tool(tools, "create_or_update_file")
            create_pr_tool    = self._find_tool(tools, "create_pull_request")

            if not (create_branch_tool and upsert_file_tool and create_pr_tool):
                available = self._debug_tool_names(tools)
                raise RuntimeError(
                    "Required GitHub MCP tools not found. "
                    "Needed: create_branch, create_or_update_file, create_pull_request. "
                    f"Available tools: {available}"
                )

            # 1) Create branch from base
            await self._call(client, create_branch_tool, {
                "owner": self.owner,
                "repo": self.repo,
                "branch": branch,
                "from_branch": base,
            })

            # 2) Create/update files on the branch
            for path, content in files.items():
                await self._call(client, upsert_file_tool, {
                    "owner": self.owner,
                    "repo": self.repo,
                    "branch": branch,
                    "path": path,
                    "content": content,
                    "message": commit_message,
                })

            # 3) Open PR
            pr = await self._call(client, create_pr_tool, {
                "owner": self.owner,
                "repo": self.repo,
                "title": title,
                "body": body,
                "base": base,
                "head": branch,
                "draft": False,
            })

            if isinstance(pr, dict):
                return pr.get("html_url") or pr.get("url") or json.dumps(pr, ensure_ascii=False)
            if isinstance(pr, str):
                return pr
            return str(pr)


def publish_as_pr_via_mcp(
    branch: str,
    title: str,
    body: str,
    files: Dict[str, str],
    commit_message: Optional[str] = None,
    base: Optional[str] = None,
) -> str:
    pub = MCPGitHubPublisher()
    return asyncio.run(pub.publish_as_pr(branch, title, body, files, commit_message, base))
