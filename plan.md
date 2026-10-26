# Profile engineering ledger

Approved 2026-10-26. The user selected the engineering ledger, projects first,
approved the project copy and delegated remaining choices and implementation.

## Design

Keep the Staff Platform Engineer introduction. Present Job Scout, Platen,
CPA Prometheus, Interview skills, Orrery and Peephole in that order, with two
sentences each and native links. Follow with selected merged contributions and
the five products: Plano Adentro, Subsíndico, Tessera, Navalha and Seguros MCP.
Place Agentic homelab beside the lab. Humanizer reviews all new public copy.

Use warm charcoal/paper, amber, IBM Plex Sans/Mono and thin ledger rules. Native
Markdown carries prose and links. Static SVGs carry the header, contribution
history, fleet and operations readings. Each has light/dark and desktop/mobile
compositions. Do not scale desktop text down into unreadable mobile labels.

Fetch the sanitised public orrery feeds and GitHub GraphQL directly. Persist only
the selected public aggregates with source and collection times. A failed feed
retains its previous sample, visibly marked as not refreshed. Unknown values
remain unknown. No private names, addresses, secrets or telemetry are published.

## Files and responsibilities

- `profile_data.py`: validate feed payloads, derive safe aggregates, fetch sources
  with timeouts, retain dated samples on source failure.
- `render.py`: draw SVGs, embed font subsets, update template metadata and publish
  only completely rendered output.
- `README.template.md`: approved prose, project/product links and picture sources.
- `config.json`: public identity, data origin and ordered repository names.
- `test_profile.py`, `tests/fixtures/`: deterministic data/render/failure tests.
- `.github/workflows/cards.yml`: checks, Python render, commit cards and README,
  six-hour schedule and unconditional scheduled-run self-enable.
- `cards/`: generated SVGs and safe source snapshots. Remove the PNG/GIF frames,
  `frames.py` and the desk-screen YAML once replacements are verified.

## Execution

- [ ] Add failing tests for readiness, missing/stale data, metric definitions,
  escaped SVG text, responsive sources, retained samples and template rendering.
- [ ] Implement validation and rendering; verify tests, Ruff and type checking.
- [ ] Check real public feeds and GraphQL; inspect desktop/mobile in both themes
  in a browser using GitHub-rendered Markdown.
- [ ] Review the diff as another engineer; fix material findings and rerun checks.
- [ ] Remove unnecessary code comments and old frame assets.
- [ ] Commit the working renderer/content/workflow together as
  `feat(profile): replace screen frames with a project-led engineering ledger`.
- [ ] Update homelab content records, journal and ai-memory with actual evidence.

## Verification

Use pytest fixtures with no external services for automated checks. Cover partial
cluster readiness, non-reporting hosts, null samples, invalid numbers, backup
result scope, zero denominators, failed fetches, GraphQL errors and retained dates.
Use live sources only for the final render and browser inspection. Keep snapshots
bounded and sanitized. Verify the six-hour cron, self-enable on failure, staged
output scope and no container dependency. No additional application deployment.
