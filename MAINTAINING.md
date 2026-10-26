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
mypy render.py profile_data.py blueprint.py streak.py
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

Cards are SVGs with embedded IBM Plex subsets. `blueprint.py` draws the header
and project workflows, sampled cluster states and the weekly contribution trace.
Text and readings remain visible while paths draw and signals move. Motion is
illustrative; the lab is sampled every six hours. Reduced motion disables the
animations and shows the completed drawing. Essential readings appear in image
alt text, with native tables for node and host details. A reader can still follow
project links with images disabled.

Each SVG contains both palettes. Its internal color-scheme media query inherits
the GitHub page's theme. The README's picture sources select only by width, at
600px. Do not combine width and color-scheme queries in those sources: GitHub's
`themed-picture` component rewrites theme queries and discards width conditions.
Desktop cards are 840px; mobile compositions are 336px. Eight Python-rendered
cards produce sixteen assets, including three project diagrams and the GPU
history inside the expandable details. Two more assets contain streak statistics.
Picture URLs include a digest of both compositions so GitHub's image cache does
not keep an older card after its content changes.

The pinned upstream Streak Stats Action generates its SVG locally with PHP 8.3
and the workflow's own token. `streak.py` preserves the statistics and ring/flame,
adapts the type and themes, and rearranges the mobile panels. Daily streaks use
UTC and the total spans the account's history; the other chart covers the past
year. The adapter rejects unexpected SVG structure, error cards and generator
errors before publication. The PHP error-log check also catches upstream's
silently skipped historical years. An upstream failure blocks the whole refresh;
the previously committed cards and their collection dates stay visible.

Local `render.py` keeps existing streak assets and their collection date. To
refresh them, run the upstream `bin/generate-card.php` at the revision and with
the options in the workflow, then run `python streak.py /path/to/upstream.svg`
before `python render.py`. See `THIRD_PARTY.md` for source and license details.

The `cards` workflow tests and renders on relevant main-branch changes, manual
dispatch and `17 */6 * * *`. Pull requests run checks with read-only permissions.
A separate scheduled-run job re-enables the workflow even if checks or rendering
fail. PHP/Composer add an upstream dependency; no container or hosted card service
is required. The render job has an eight-minute timeout.

Run the tests with fixtures before making a live-data render. Inspect both themes
at 840px README width and at mobile width on GitHub itself: its image handling can
differ from a local Markdown preview. Keep screenshots in the private run journal,
not among the generated public cards.
