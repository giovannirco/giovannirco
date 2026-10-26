# Maintaining the profile

Edit `README.template.md` for prose and links. `README.md` is generated. Keep the
project order in `config.json` and the template together. Product links point to
public landing pages; they do not imply public source or general availability.

Use Python 3.14 in a local virtual environment:

```sh
python3.14 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q
ruff check .
ruff format --check .
mypy render.py profile_data.py
GITHUB_TOKEN="$(gh auth token)" python render.py
```

The Action uses only its own `GITHUB_TOKEN`. Local authentication is optional for
lab-only refreshes; GitHub data then keeps its previous dated sample. Never commit
tokens or raw private telemetry.

`profile_data.py` validates the public orrery responses and keeps selected fields.
`cards/data.json` stores those samples, collection dates and refresh status. A
failed source keeps its previous sample and date. An initial missing source is
unavailable. If every source fails, the command exits with status 1 without
changing generated files. Template/render errors also stop publication. The
workflow commits only after a successful render.

Storage exposes a backup-event time, not a sample time. GPU usage and history are
fractions from 0 to 1. Kubernetes capacity is vCPU. Endpoint enforcement means
ingress, egress or both; backup-result counts do not establish guest coverage or
successful restores. Preserve these definitions when changing labels.

Cards are static SVGs with embedded IBM Plex subsets. Essential readings appear
in image alt text, with native tables for node and host details. Source dates and
the six-hour refresh cadence remain visible. A reader can still follow project
links with images disabled.

Each SVG contains both palettes. Its internal color-scheme media query inherits
the GitHub page's theme. The README's picture sources select only by width, at
600px. Do not combine width and color-scheme queries in those sources: GitHub's
`themed-picture` component rewrites theme queries and discards width conditions.
Desktop cards are 840px; mobile compositions are 336px. Five cards produce ten
assets, including the GPU history inside the expandable details.

The `cards` workflow tests and renders on relevant main-branch changes, manual
dispatch and `17 */6 * * *`. Pull requests run checks with read-only permissions.
A separate scheduled-run job re-enables the workflow even if checks or rendering
fail. No container or third-party card service is required.

Run the tests with fixtures before making a live-data render. Inspect both themes
at 840px README width and at mobile width on GitHub itself: its image handling can
differ from a local Markdown preview. Keep screenshots in the private run journal,
not among the generated public cards.
