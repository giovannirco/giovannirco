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
history, fleet, operations readings and GPU history. Each has desktop/mobile
compositions and both palettes inside the SVG. Width-only picture sources avoid
GitHub rewriting combined theme/width queries. Do not scale desktop text down
into unreadable mobile labels.

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
- `test_profile.py`: deterministic data/render/failure tests and fixtures.
- `.github/workflows/cards.yml`: checks, Python render, commit cards and README,
  six-hour schedule and unconditional scheduled-run self-enable.
- `cards/`: generated SVGs and safe source snapshots. Remove the PNG/GIF frames,
  `frames.py` and the desk-screen YAML once replacements are verified.

## Execution

- [x] Add failing tests for readiness, missing/stale data, metric definitions,
  escaped SVG text, responsive sources, retained samples and template rendering.
- [x] Implement validation and rendering; verify tests, Ruff and type checking.
- [x] Check real public feeds and GraphQL; inspect desktop/mobile in both themes
  in a browser using GitHub-rendered Markdown.
- [x] Review the diff as another engineer; fix material findings and rerun checks.
- [x] Remove unnecessary code comments and old frame assets.
- [x] Commit the working renderer/content/workflow together as
  `feat(profile): replace screen frames with a project-led engineering ledger`.
- [x] Update homelab content records, journal and ai-memory with actual evidence.

## Verification

Use pytest fixtures with no external services for automated checks. Cover partial
cluster readiness, non-reporting hosts, null samples, invalid numbers, backup
result scope, zero denominators, failed fetches, GraphQL errors and retained dates.
Use live sources only for the final render and browser inspection. Keep snapshots
bounded and sanitized. Verify the six-hour cron, self-enable on failure, staged
output scope and no container dependency. No additional application deployment.

Delivered as `5a2c89e`; Action [40326230440](https://github.com/giovannirco/giovannirco/actions/runs/40326230440)
passed all 25 tests, Ruff and mypy, rendered ten SVGs from eight sources and
committed the refresh as `221403d`. Browser checks confirmed 840px desktop images
and 308px mobile display, both themes, without horizontal overflow. Independent
review passed after corrections for unknown readiness, GPU units, accessibility
and missing-value text bounds. Related editorial records and journal were
committed separately; `MAINTAINING.md` describes the ongoing workflow.

## Animated systems blueprint

Approved 2026-10-26 after the ledger delivery. Gio selected direction A and
added DenverCoder1/github-readme-streak-stats. Preserve the project order and
copy. Add a drawing sequence around the immediately visible identity, three
project schematics, sampled cluster states and a contribution trace. Motion is
illustrative, not a claim of streaming telemetry. Reduced motion shows the
completed composition. Keep both themes and separate mobile layouts.

Use the upstream Streak Stats Action pinned to a commit to generate locally with
the workflow token. Match the warm palette, ensure mobile legibility and keep
streak dates distinct from the rolling-year chart. Do not use a hosted endpoint.

- `blueprint.py`: SVG drawing primitives, motion CSS and project schematics.
- `render.py`: integrate header, fleet, activity and project drawings.
- `test_blueprint.py`: accessible content, responsive bounds, sampled state and
  reduced-motion contracts; browser checks verify actual animation.
- Streak integration and tests: validate upstream output before publication;
  adapt themes and width if necessary without changing upstream statistics.
- Workflow: generate streak before the existing atomic publication step, retain
  the six-hour schedule and independent self-enable job.
- README template: insert three project illustrations and the streak card.

- [x] Inspect the renderer, upstream Action and baseline (25 tests passing).
- [x] Write failing tests, then implement the blueprint and streak integration.
- [x] Run pytest, Ruff and mypy; render with public data.
- [x] Verify motion and reduced motion, both themes and mobile on GitHub.
- [x] Review spec and actual diff independently; fix material findings and test.
- [ ] Commit as `feat(profile): animate the systems blueprint and add streak stats`.
- [ ] Publish, verify the Action and update editorial records, journal and memory.

The implementation uses subagent-driven development for the independent streak
integration and review. All new prose receives the humanizer pass. Tests use
fixtures; the final render and browser checks use live public data. Remove
unnecessary comments and review only the final diff before publishing.

Pre-publication verification: 49 tests passed, Ruff check/format passed and mypy
passed for all four source files. All eight data sources refreshed. The pinned
upstream PHP generator completed in 2.9 seconds; an injected historical-fetch
error correctly blocked adaptation. Independent review passed after correcting
outline fills that made the terminal and printer surfaces transparent. Browser
checks confirmed animated image frames change, reduced-motion frames settle to
an identical static composition, and the completed paths remain visible.
Desktop images display at 840px; mobile images at 308px from 336px compositions,
without horizontal overflow. Both themes follow GitHub despite the opposite OS
preference.
