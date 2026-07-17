# OpenPilot — Devpost submission kit

## Category

Developer Tools

## Tagline

From unfamiliar repository to confident first pull request.

## Project description

OpenPilot is a local-first open-source contribution navigator. New contributors often find a repository they care about, then stall: the codebase is unfamiliar, issue lists are noisy, and maintainers' expectations are implicit. OpenPilot turns that uncertainty into a practical sequence.

Paste a public GitHub repository URL and OpenPilot retrieves its metadata and open issues, applies explainable newcomer-oriented ranking, then guides the contributor through a focused plan, a maintainer-style readiness checklist, and a GitHub-ready pull-request draft. It works without an OpenAI API key or paid runtime dependency, so judges can run the complete workflow locally.

## What is new

- Live public GitHub repository and issue intake
- Explainable issue ranking that favors clearly scoped contribution opportunities
- Repository-aware local contribution guide
- Structured implementation plan and maintainer review checklist
- Pull-request draft generated from the selected repository and issue

## How Codex was used

Codex was the development partner for the core product: planning the local-first architecture, implementing the Python server and GitHub integration, designing the responsive dashboard, adding input validation and error states, and drafting setup/submission documentation. The project intentionally keeps the runtime model-free and labels local guidance honestly.

## Demo video outline (under 3 minutes)

1. **0:00–0:20 — Problem.** Show a public repository with an issue list. Explain why first-time contributors struggle to know where to begin.
2. **0:20–0:55 — Repository intake.** Paste a GitHub URL into OpenPilot. Show live repository details, topics, and ranked open issues.
3. **0:55–1:30 — Contribution guidance.** Click “Where do I start?”, “Generate detailed plan,” and “Run maintainer review.” Explain that this is a local-first workflow with no API key required.
4. **1:30–2:05 — PR draft.** Click “Build my PR”; show the issue-linked title, validation checklist, and PR body.
5. **2:05–2:40 — Codex story.** Show this Codex task/session and briefly explain that Codex built the server, UI, validation, and docs.
6. **2:40–3:00 — Impact.** Explain that OpenPilot lowers the first-contribution barrier while promoting small, reviewable, well-tested changes.

## Submission checklist

- [ ] Create a GitHub repository and push these files.
- [ ] Add the public repository URL to Devpost.
- [ ] Record/upload the public YouTube demo video.
- [ ] Paste this description and select **Developer Tools**.
- [ ] Add the required `/feedback` Codex session ID.
- [ ] Verify setup instructions from a clean terminal.
