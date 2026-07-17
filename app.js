const form = document.querySelector('#repo-form');
const status = document.querySelector('#status');
const stats = document.querySelector('#repo-stats');
const list = document.querySelector('#issue-list');
let repositoryContext = null;

function issueCard(issue, selected) {
  const labels = issue.labels.map(label => `<span class="chip">${label}</span>`).join(' ');
  return `<article class="issue ${selected ? 'selected' : ''}"><span class="score ${selected ? '' : 'muted'}">${issue.score}</span><div><h3>#${issue.number} ${issue.title}</h3><p>${issue.why}</p>${labels}</div><a class="arrow" href="${issue.url}" target="_blank" aria-label="Open GitHub issue">→</a></article>`;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const url = document.querySelector('#repo-url').value.trim();
  const button = form.querySelector('button');
  if ((url.match(/github\.com/gi) || []).length !== 1) {
    status.textContent = 'Paste one complete GitHub URL only, for example https://github.com/muqadasejaz/Plant-Detection-using-YOLOv8';
    return;
  }
  button.disabled = true; button.textContent = 'Mapping repository…';
  status.textContent = 'Reading public repository metadata and open issues.';
  try {
    const response = await fetch('/api/analyze', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Unable to analyze this repository.');
    const repo = data.repository;
    repositoryContext = data;
    stats.innerHTML = `<article><small>REPOSITORY</small><strong>${repo.name}</strong><span>${repo.language} · ${repo.defaultBranch}</span></article><article><small>OPEN ISSUES</small><strong>${data.issues.length} ranked</strong><span>From live GitHub data</span></article><article><small>COMMUNITY SIGNAL</small><strong>★ ${repo.stars.toLocaleString()}</strong><span>${repo.topics.join(' · ') || 'Open source project'}</span></article>`;
    list.innerHTML = data.issues.length ? data.issues.map((issue, index) => issueCard(issue, index === 0)).join('') : '<p>No open issues found. Try another repository.</p>';
    status.textContent = `Repository mapped: ${repo.description}`;
  } catch (error) { status.textContent = error.message; }
  finally { button.disabled = false; button.innerHTML = 'Analyze repository <span>→</span>'; }
});

async function runAssistant(action, message, output, button) {
  if (!repositoryContext) { status.textContent = 'Analyze a repository first so OpenPilot can ground its answer.'; return; }
  const original = button?.textContent;
  if (button) { button.disabled = true; button.textContent = 'Thinking…'; }
  output.classList.add('loading'); output.textContent = 'OpenPilot is reasoning over the repository context…';
  try {
    const response = await fetch('/api/assistant', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action, message, context: repositoryContext})});
    const raw = await response.text();
    let data;
    try { data = JSON.parse(raw); }
    catch { throw new Error('OpenPilot needs a server restart. In PowerShell, press Ctrl+C, then run python server.py again.'); }
    if (!response.ok) throw new Error(data.error || 'The AI request could not be completed.');
    output.classList.remove('loading'); output.classList.add('ai-output'); output.textContent = data.text;
    if (data.mode === 'local') status.textContent = 'Local-first mode: contribution guidance is generated without an API key.';
  } catch (error) { output.classList.remove('loading'); output.textContent = error.message; }
  finally { if (button) { button.disabled = false; button.textContent = original; } }
}

const mentorOutput = document.querySelector('.bot');
document.querySelectorAll('.suggestions button').forEach(button => button.addEventListener('click', () => runAssistant('mentor', button.textContent, mentorOutput, button)));
document.querySelector('#mentor-send').addEventListener('click', () => {
  const input = document.querySelector('#mentor-input');
  if (input.value.trim()) runAssistant('mentor', input.value.trim(), mentorOutput, document.querySelector('#mentor-send'));
});
document.querySelector('#mentor-input').addEventListener('keydown', event => { if (event.key === 'Enter') document.querySelector('#mentor-send').click(); });
document.querySelector('#plan-button').addEventListener('click', event => runAssistant('plan', 'Create a contribution plan for the top-ranked open issue.', document.querySelector('.plan-result'), event.currentTarget));
document.querySelector('#review-button').addEventListener('click', event => runAssistant('review', 'Simulate a maintainer review for a contributor addressing the top-ranked issue.', document.querySelector('.review-result'), event.currentTarget));
document.querySelector('#pr-button').addEventListener('click', event => {
  if (!repositoryContext) { status.textContent = 'Analyze a repository first to create a pull request draft.'; return; }
  const repo = repositoryContext.repository;
  const issue = repositoryContext.issues[0] || {};
  const draft = `# ${issue.title || 'Focused repository improvement'}\n\n## Summary\n- Addresses #${issue.number || 'issue'} in ${repo.name}.\n- Keeps the change intentionally small and aligned with the existing ${repo.language} workflow.\n\n## Motivation\nThis contribution resolves the reported need while preserving established project conventions.\n\n## Validation\n- [ ] Reproduce the original behavior\n- [ ] Run the documented project checks\n- [ ] Add or update a focused regression test\n\n## Checklist\n- [ ] Linked issue\n- [ ] No unrelated changes\n- [ ] Documentation updated if needed`;
  const output = document.querySelector('.pr-result');
  output.textContent = draft;
  status.textContent = 'GitHub-ready PR draft created locally. Review it, then paste it into your pull request.';
  event.currentTarget.textContent = 'PR draft ready';
});
