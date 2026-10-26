<p>
<picture>
  <source media="(max-width: 600px)" srcset="cards/header-mobile.svg?v=8e15dea9a9cf">
  <img alt="Giovanni Coutinho, Staff Platform Engineer · Kubernetes, GitOps, observability" src="cards/header.svg?v=8e15dea9a9cf" width="840">
</picture>
</p>

I design and run Kubernetes platforms. For almost seven years I was on the platform team at Exodus, a non-custodial crypto wallet and exchange. I led the move of 30+ services from GitLab to Argo CD. I took observability from commercial tools to our own Mimir, Loki and Tempo, and later to Grafana Cloud once the numbers made sense. The Cilium policies I rolled out stopped an SSRF callback during a real incident, which is still my favourite argument for default deny. In the last year I built the MCP servers and agent skills other teams ended up using.

[Portfolio](https://giovanni.dev.br) · [Resume](https://resume.giovanni.dev.br) · [LinkedIn](https://www.linkedin.com/in/giovanni-coutinho)

## Public work

### [Job Scout](https://github.com/giovannirco/job-scout)

A self-hosted job-search desk that finds listings, tracks applications and helps research roles. It keeps job-description history and gives AI assistants access through MCP, with drafts left for you to review.

<sub>TypeScript · updated 2026-10-23 · 2 stars</sub>

<p>
<picture>
  <source media="(max-width: 600px)" srcset="cards/scout-mobile.svg?v=2fbeb9654ff2">
  <img alt="Job Scout workflow: listings, role research, then drafts for your review." src="cards/scout.svg?v=2fbeb9654ff2" width="840">
</picture>
</p>

### [Platen](https://github.com/giovannirco/platen)

Print and scan from a browser, scripts or an AI assistant, including PDFs your printer refuses to accept. One Go binary speaks the device protocols, renders PDFs and files scans in Paperless-ngx.

<sub>Go · updated 2026-10-03 · 2 stars</sub>

<p>
<picture>
  <source media="(max-width: 600px)" srcset="cards/platen-mobile.svg?v=54d51de1dfd5">
  <img alt="Platen workflow: PDF documents, print and scan, and filing in Paperless-ngx." src="cards/platen.svg?v=54d51de1dfd5" width="840">
</picture>
</p>

### [CPA Prometheus](https://github.com/giovannirco/cpa-prometheus-plugin)

Prometheus metrics for CLIProxyAPI traffic, token usage and provider quotas. It includes a Grafana dashboard and serves metrics through the proxy's authenticated management API.

<sub>Go · updated 2026-09-23 · 3 stars</sub>

<p>
<picture>
  <source media="(max-width: 600px)" srcset="cards/cpa-mobile.svg?v=a51fec5ee0a3">
  <img alt="CPA Prometheus workflow: requests become metrics for a Grafana dashboard." src="cards/cpa.svg?v=a51fec5ee0a3" width="840">
</picture>
</p>

### [Interview skills](https://github.com/giovannirco/interview-skills)

Turn interview recordings into local transcripts with timestamps and speaker names. The workflow includes speaker checks, preparation and post-interview reviews, with the audio kept on your machine.

<sub>Python · updated 2026-10-06</sub>

### [Orrery](https://github.com/giovannirco/giovanni-dev-br-public) · [Visit](https://orrery.giovanni.dev.br)

A Three.js portfolio where you fly between projects and read about what's behind them. It also shows homelab readings collected through sanitised public feeds.

<sub>JavaScript · updated 2026-10-24</sub>

### [Peephole](https://github.com/giovannirco/peephole) · [Demo](https://peephole.bitops.com.br)

A small window into the homelab on an ESP32 desk display. A Rust hub collects data through plugins and renders the pages, keeping the display firmware simple.

<sub>Rust · updated 2026-10-26</sub>

### Upstream contributions

- **ai-memory:** [context after compaction](https://github.com/akitaonrails/ai-memory/pull/1230) and [Grok handoffs](https://github.com/akitaonrails/ai-memory/pull/840).
- **CLIProxyAPI Management Center:** [Grok subscription quotas](https://github.com/router-for-me/Cli-Proxy-API-Management-Center/pull/451).
- **CLIProxyAPI Plugins Store:** [CPA Prometheus registration](https://github.com/router-for-me/CLIProxyAPI-Plugins-Store/pull/130).

<p>
<picture>
  <source media="(max-width: 600px)" srcset="cards/activity-mobile.svg?v=8d49d3e26265">
  <img alt="18,207 GitHub contributions over the past year, grouped by week" src="cards/activity.svg?v=8d49d3e26265" width="840">
</picture>
</p>

<sub>Weekly totals from GitHub's contribution calendar. Collected 2026-10-26 13:45 UTC.</sub>

<p>
<picture>
  <source media="(max-width: 600px)" srcset="cards/streak-mobile.svg?v=266b5fe8127f">
  <img alt="GitHub Streak Stats. 20,979 total contributions (2017-12-15 - Present); current daily streak: 98 days (2026-07-21 - 2026-10-26); longest daily streak: 98 days (2026-07-21 - 2026-10-26). Collected 2026-10-26 13:45 UTC." src="cards/streak.svg?v=266b5fe8127f" width="840">
</picture>
</p>

<sub>Daily streaks and all-time contributions, generated with [GitHub Readme Streak Stats](https://github.com/DenverCoder1/github-readme-streak-stats). Dates use UTC.</sub>

## Products I'm building

[**Plano Adentro**](https://planoadentro.com.br) — Architects and designers share projects their clients can walk through in a browser.

[**Subsíndico**](https://subsindico.ia.br) — A workspace for running a condominium: documents, assemblies, maintenance and an assistant that answers with references to the building's own rules.

[**Tessera**](https://tessera.otservices.space) — Share access to authenticator codes with permissions, time limits and a record of each code issued.

**Navalha** — Scheduling for barbershops and other appointment-based businesses, with WhatsApp and an AI assistant. In testing.

[**Seguros MCP**](https://seguros-mcp.bitops.com.br) — Tools for an AI assistant to look up insurance policies, installments, claims and documents through the insurer's portal. Tokio Marine is in beta.

## Homelab

At home I run six Talos clusters on Proxmox with the same rules: GitOps for every change and default deny in every namespace. [Agentic homelab](https://github.com/giovannirco/agentic-homelab) documents how I build and run it with agents.

<p>
<picture>
  <source media="(max-width: 600px)" srcset="cards/fleet-mobile.svg?v=6c410c8c30a4">
  <img alt="Homelab capacity and readiness. 6/6 clusters ready; 11/11 nodes ready; 484 pods; 78 Kubernetes vCPU; 150 namespaces. Cluster 01: ready. Cluster 02: ready. Cluster 03: ready. Cluster 04: ready. Cluster 05: ready. Cluster 06: ready" src="cards/fleet.svg?v=6c410c8c30a4" width="840">
</picture>
</p>

<p>
<picture>
  <source media="(max-width: 600px)" srcset="cards/operations-mobile.svg?v=8e4221ad79e8">
  <img alt="Compute: 3/3 hosts up. Proxmox · virtual machines and containers; Network policy: 287/293 endpoints. Ingress or egress policy enforced; Backups: 29/29 recorded results OK. Latest result 2026-10-26 07:46 UTC; Network: 13/13 devices online. WAN latency 10 ms; GPU: 2 reporting · 48 GiB VRAM. Current readings and short history below" src="cards/operations.svg?v=8e4221ad79e8" width="840">
</picture>
</p>

<details>
<summary>Nodes, hosts and GPU readings</summary>

| Node | Ready | CPU | Memory | Pods |
| :--- | :--- | ---: | ---: | ---: |
| node-01 | yes | 26% | 74% | 63 |
| node-02 | yes | 42% | 67% | 48 |
| node-03 | yes | 17% | 48% | 34 |
| node-04 | yes | 14% | 39% | 36 |
| node-05 | yes | 18% | 45% | 42 |
| node-06 | yes | 24% | 68% | 16 |
| node-07 | yes | 5% | 34% | 33 |
| node-08 | yes | 16% | 81% | 62 |
| node-09 | yes | 23% | 87% | 29 |
| node-10 | yes | 21% | 69% | 52 |
| node-11 | yes | 31% | 63% | 65 |

Sampled 2026-10-26 13:45 UTC

| Host | CPU | Memory | VMs up | Containers up |
| :--- | ---: | ---: | ---: | ---: |
| Compute-A | 11% | 92% | 2/3 | 2/2 |
| Compute-B | 21% | 73% | 4/9 | 9/10 |
| Compute-C | 32% | 81% | 15/15 | 8/13 |

Sampled 2026-10-26 13:45 UTC

Cilium: 2,562 flows/s; 0.8 drops/s. Endpoint enforcement counts ingress, egress or both; it does not measure default-deny coverage.

Sampled 2026-10-26 13:45 UTC

WAN: 0.81 MB/s down, 16.73 MB/s up. Wi-Fi access points: 6/6; switches: 6/6; gateways: 1/1 online.

Sampled 2026-10-26 13:45 UTC

Disk checks: 6/6 passing. Backup results are the latest recorded job results, not proof that every guest is covered or restores work.

<p>
<picture>
  <source media="(max-width: 600px)" srcset="cards/hardware-mobile.svg?v=9fa7f8eaee20">
  <img alt="GPU / SHORT HISTORY GPU-1 0% use · 37 °C · 9 W VRAM 1% of 24 GiB 14 min · 0–100% scale Sampled 2026-10-26 13:44 UTC GPU-2 0% use · 39 °C · 25 W VRAM 1% of 24 GiB 14 min · 0–100% scale Sampled 2026-10-26 13:44 UTC . Sampled 2026-10-26 13:44 UTC" src="cards/hardware.svg?v=9fa7f8eaee20" width="840">
</picture>
</p>

</details>

<details>
<summary>Sample dates and data sources</summary>

Readings come from the [orrery's public feeds](https://orrery.giovanni.dev.br/api/insight/lab). The cards refresh every six hours. Each date belongs to the source sample where available; storage has a collection time and a separate backup-event time. A failed refresh keeps the previous dated reading.

- lab: Sampled 2026-10-26 13:45 UTC
- nodes: Sampled 2026-10-26 13:45 UTC
- proxmox: Sampled 2026-10-26 13:45 UTC
- storage: Collected 2026-10-26 13:45 UTC
- network: Sampled 2026-10-26 13:45 UTC
- unifi: Sampled 2026-10-26 13:45 UTC
- gpu: Sampled 2026-10-26 13:44 UTC
- github: Collected 2026-10-26 13:45 UTC

</details>
