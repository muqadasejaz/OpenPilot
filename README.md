# OpenPilot — Your AI Open Source Mentor

OpenPilot helps first-time and returning contributors understand a public GitHub repository, identify a good issue, make a focused contribution plan, and review the work through a maintainer lens.

## MVP included

- A polished contributor workflow dashboard
- Live public GitHub repository metadata and open-issue retrieval
- Explainable newcomer-oriented issue ranking
- Local-first contribution guidance, planning, maintainer review, and PR drafting
- Zero third-party Python dependencies for the first runnable slice

## Run locally

```powershell
python server.py
```

Open http://localhost:8000 and paste a public GitHub repository URL. No OpenAI API key, paid subscription, or model access is required. Optional: set `GITHUB_TOKEN` to reduce GitHub API rate-limit issues.

## Build Week narrative

OpenPilot is a local-first developer tool built with Codex. It turns public GitHub metadata into a focused contribution workflow: analyze a repository, identify an issue, generate a safe plan, run a maintainer-style checklist, and draft a pull request. The runtime deliberately requires no OpenAI API key, which makes the demo reproducible for judges.

Codex accelerated the implementation of the local HTTP service, GitHub intake, interface, issue-ranking logic, validation states, and submission documentation. The product does not claim that its local guidance is a live model response.

## Next milestones

1. Clone into a per-session sandbox and extract source-tree signals.
2. Allow issue selection and user skill preferences for more precise ranking.
3. Add a downloadable contribution plan and pull-request template.
4. Add optional, user-supplied model integrations behind an explicit setting.
