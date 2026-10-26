{{picture:header}}

I design and run Kubernetes platforms. For almost seven years I was on the platform team at Exodus, a non-custodial crypto wallet and exchange. I led the move of 30+ services from GitLab to Argo CD. I took observability from commercial tools to our own Mimir, Loki and Tempo, and later to Grafana Cloud once the numbers made sense. The Cilium policies I rolled out stopped an SSRF callback during a real incident, which is still my favourite argument for default deny. In the last year I built the MCP servers and agent skills other teams ended up using.

[Portfolio](https://giovanni.dev.br) · [Resume](https://resume.giovanni.dev.br) · [LinkedIn](https://www.linkedin.com/in/giovanni-coutinho)

## Public work

### [Job Scout](https://github.com/giovannirco/job-scout)

A self-hosted job-search desk that finds listings, tracks applications and helps research roles. It keeps job-description history and gives AI assistants access through MCP, with drafts left for you to review.

<sub>{{meta:job-scout}}</sub>

### [Platen](https://github.com/giovannirco/platen)

Print and scan from a browser, scripts or an AI assistant, including PDFs your printer refuses to accept. One Go binary speaks the device protocols, renders PDFs and files scans in Paperless-ngx.

<sub>{{meta:platen}}</sub>

### [CPA Prometheus](https://github.com/giovannirco/cpa-prometheus-plugin)

Prometheus metrics for CLIProxyAPI traffic, token usage and provider quotas. It includes a Grafana dashboard and serves metrics through the proxy's authenticated management API.

<sub>{{meta:cpa-prometheus-plugin}}</sub>

### [Interview skills](https://github.com/giovannirco/interview-skills)

Turn interview recordings into local transcripts with timestamps and speaker names. The workflow includes speaker checks, preparation and post-interview reviews, with the audio kept on your machine.

<sub>{{meta:interview-skills}}</sub>

### [Orrery](https://github.com/giovannirco/giovanni-dev-br-public) · [Visit](https://orrery.giovanni.dev.br)

A Three.js portfolio where you fly between projects and read about what's behind them. It also shows homelab readings collected through sanitised public feeds.

<sub>{{meta:giovanni-dev-br-public}}</sub>

### [Peephole](https://github.com/giovannirco/peephole) · [Demo](https://peephole.bitops.com.br)

A small window into the homelab on an ESP32 desk display. A Rust hub collects data through plugins and renders the pages, keeping the display firmware simple.

<sub>{{meta:peephole}}</sub>

### Upstream contributions

- **ai-memory:** [context after compaction](https://github.com/akitaonrails/ai-memory/pull/1230) and [Grok handoffs](https://github.com/akitaonrails/ai-memory/pull/840).
- **CLIProxyAPI Management Center:** [Grok subscription quotas](https://github.com/router-for-me/Cli-Proxy-API-Management-Center/pull/451).
- **CLIProxyAPI Plugins Store:** [CPA Prometheus registration](https://github.com/router-for-me/CLIProxyAPI-Plugins-Store/pull/130).

{{picture:activity}}

<sub>Weekly totals from GitHub's contribution calendar. {{github_stamp}}.</sub>

## Products I'm building

[**Plano Adentro**](https://planoadentro.com.br) — Architects and designers share projects their clients can walk through in a browser.

[**Subsíndico**](https://subsindico.ia.br) — A workspace for running a condominium: documents, assemblies, maintenance and an assistant that answers with references to the building's own rules.

[**Tessera**](https://tessera.otservices.space) — Share access to authenticator codes with permissions, time limits and a record of each code issued.

**Navalha** — Scheduling for barbershops and other appointment-based businesses, with WhatsApp and an AI assistant. In testing.

[**Seguros MCP**](https://seguros-mcp.bitops.com.br) — Tools for an AI assistant to look up insurance policies, installments, claims and documents through the insurer's portal. Tokio Marine is in beta.

## Homelab

At home I run six Talos clusters on Proxmox with the same rules: GitOps for every change and default deny in every namespace. [Agentic homelab](https://github.com/giovannirco/agentic-homelab) documents how I build and run it with agents.

{{picture:fleet}}

{{picture:operations}}

<details>
<summary>Nodes, hosts and GPU readings</summary>

{{details}}

{{picture:hardware}}

</details>

<details>
<summary>Sample dates and data sources</summary>

Readings come from the [orrery's public feeds](https://orrery.giovanni.dev.br/api/insight/lab). The cards refresh every six hours. Each date belongs to the source sample where available; storage has a collection time and a separate backup-event time. A failed refresh keeps the previous dated reading.

{{sample_dates}}

</details>
