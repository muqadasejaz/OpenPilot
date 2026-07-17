"""OpenPilot local MVP server. No third-party dependencies required."""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from collections import Counter
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).parent


def load_env() -> None:
    """Load local development secrets without a third-party dependency."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def response_text(response: dict) -> str:
    if response.get("output_text"):
        return response["output_text"]
    parts = []
    for item in response.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"}:
                parts.append(content.get("text", ""))
    return "\n".join(parts)


def ask_openai(action: str, context: dict, user_message: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI is not configured. Add OPENAI_API_KEY to .env, then restart the server.")
    roles = {
        "mentor": "You are OpenPilot's patient open-source mentor. Give a direct, practical answer grounded only in the supplied repository context. Mention uncertainty when context is insufficient. Teach the user what to inspect next.",
        "plan": "You are OpenPilot's contribution planner. Produce a safe, small-scope plan for the selected issue using the repository context. Include goal, likely areas to inspect (clearly label assumptions), numbered steps, tests, risks, and estimated effort. Do not claim you inspected files that are not in context.",
        "review": "You are a careful open-source maintainer reviewing a proposed contribution. Return a concise review with headings APPROVED, REQUESTED CHANGES, and BEFORE YOU OPEN THE PR. Ground comments in the supplied context and avoid inventing code changes.",
    }
    if action not in roles:
        raise ValueError("Unknown OpenPilot action.")
    request_body = json.dumps({
        "model": os.getenv("OPENAI_MODEL", "gpt-5.6"),
        "instructions": roles[action],
        "input": json.dumps({"repository_context": context, "user_request": user_message}, ensure_ascii=False),
        "max_output_tokens": 700,
    }).encode("utf-8")
    request = Request("https://api.openai.com/v1/responses", data=request_body, headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "OpenPilot-MVP",
    }, method="POST")
    try:
        with urlopen(request, timeout=45) as response:
            text = response_text(json.load(response))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise ValueError(f"OpenAI request failed ({error.code}): {detail[:240]}") from error
    if not text:
        raise ValueError("The model returned no text. Please try again.")
    return text


def local_preview(action: str, context: dict, user_message: str) -> str:
    """Deterministic contribution guidance with no model or API key required."""
    repo = context.get("repository", {})
    issue = (context.get("issues") or [{}])[0]
    name = repo.get("name", "this repository")
    issue_title = issue.get("title", "the top-ranked issue")
    if action == "mentor":
        question = user_message.lower()
        if "architecture" in question:
            return (f"Repository map for {name}: the primary language is {repo.get('language', 'unknown')} and the default branch is "
                    f"{repo.get('defaultBranch', 'main')}. Start from the README, then find the package or notebook files that implement "
                    "the workflow described there. The next safe step is to trace one documented example end-to-end before changing code.")
        if "maintainer" in question or "expect" in question:
            return ("Maintainer checklist: keep the scope focused, explain the user-visible impact, follow the repository's existing style, "
                    "include a reproducible validation step, and link the related issue. Avoid drive-by formatting changes in the same PR.")
        return (f"A safe starting point is #{issue.get('number', '')} {issue_title} in {name}. Read the issue discussion, then inspect the README "
                f"and the files closest to its {repo.get('language', 'primary')} workflow. Before editing, find an existing example or test that "
                "shows the expected behavior. This guidance is generated locally from public repository metadata.")
    if action == "plan":
        return (f"LOCAL PREVIEW\n\nGoal\nAddress #{issue.get('number', '')}: {issue_title}.\n\n"
                "1. Read the issue and contribution guidance.\n2. Locate the smallest relevant module or notebook section.\n"
                "3. Make one focused change following existing conventions.\n4. Validate with the project’s documented command or a reproducible example.\n"
                "5. Document the behavior and link the issue in the PR.\n\nRisk: medium — source files have not been cloned or inspected yet.")
    return ("LOCAL PREVIEW\n\nAPPROVED\nThe intended scope is small and suitable for a first contribution.\n\n"
            "REQUESTED CHANGES\nAdd a reproducible validation step and keep unrelated formatting out of the patch.\n\n"
            "BEFORE YOU OPEN THE PR\nLink the issue, explain the user impact, and state exactly what you tested.")


def assistant_response(action: str, context: dict, user_message: str) -> dict:
    return {"text": local_preview(action, context, user_message), "mode": "local"}


def github_json(url: str):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "OpenPilot-MVP"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=15) as response:
        return json.load(response)


def repo_slug(repo_url: str) -> tuple[str, str]:
    if repo_url.lower().count("github.com") != 1:
        raise ValueError("Paste exactly one GitHub repository URL, for example https://github.com/owner/repository")
    match = re.search(r"github\.com[/:]([^/\s]+)/([^/#\s]+)", repo_url)
    if not match:
        raise ValueError("Enter a GitHub repository URL, for example https://github.com/owner/repository")
    owner, name = match.group(1), match.group(2).removesuffix(".git")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner) or not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
        raise ValueError("The repository URL looks incomplete. Use https://github.com/owner/repository")
    return owner, name


def rank_issue(issue: dict) -> dict:
    title = issue["title"].lower()
    labels = [label["name"] for label in issue.get("labels", [])]
    beginner = any(word in title or any(word in label.lower() for label in labels)
                   for word in ("good first", "beginner", "documentation", "typo", "help wanted"))
    score = 92 if beginner else 74 if len(labels) > 0 else 62
    difficulty = "Easy" if beginner else "Medium"
    return {"number": issue["number"], "title": issue["title"], "labels": labels[:3],
            "url": issue["html_url"], "score": score, "difficulty": difficulty,
            "why": "Clear newcomer-friendly scope and a low-risk contribution." if beginner else "Well-scoped issue with enough context to plan safely."}


def analyze(repo_url: str) -> dict:
    owner, name = repo_slug(repo_url)
    repo = github_json(f"https://api.github.com/repos/{owner}/{name}")
    issues = github_json(f"https://api.github.com/repos/{owner}/{name}/issues?state=open&per_page=20")
    issues = [issue for issue in issues if "pull_request" not in issue]
    language = repo.get("language") or "Unknown"
    topics = repo.get("topics", [])
    return {
        "repository": {"name": repo["full_name"], "description": repo.get("description") or "No description provided.",
                       "language": language, "stars": repo["stargazers_count"], "defaultBranch": repo["default_branch"],
                       "url": repo["html_url"], "topics": topics[:5]},
        "architecture": [
            {"name": "Entry point", "value": "Explore the README and package metadata first"},
            {"name": "Primary language", "value": language},
            {"name": "Contribution signal", "value": f"{repo.get('open_issues_count', 0)} open issues available"},
        ],
        "issues": sorted((rank_issue(issue) for issue in issues), key=lambda item: item["score"], reverse=True)[:6],
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_POST(self):
        if self.path not in {"/api/analyze", "/api/assistant"}:
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            result = analyze(payload.get("url", "")) if self.path == "/api/analyze" else assistant_response(
                payload.get("action", ""), payload.get("context", {}), payload.get("message", "")
            )
            body, status = json.dumps(result).encode(), 200
        except (ValueError, HTTPError, OSError) as error:
            body, status = json.dumps({"error": str(error)}).encode(), 400
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    load_env()
    print("OpenPilot running at http://localhost:8000")
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
