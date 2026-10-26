"""Render the profile from public data: python render.py."""

import base64
import datetime as dt
import io
import json
import os
import pathlib
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from html import escape

from fontTools import subset
from fontTools.ttLib import TTFont

import blueprint
from profile_data import (
    GITHUB_QUERY,
    MODELS,
    Payload,
    Sample,
    cluster_states,
    collect,
    parse_github,
    ratio,
    request_json,
)
from streak import streak_alt

ROOT = pathlib.Path(__file__).parent
THEMES = {
    "dark": {"bg": "#14130f", "line": "#494438", "ink": "#ece6d8", "muted": "#b4ac9b", "accent": "#e8a33d"},
    "light": {"bg": "#f6f2e8", "line": "#cbc1ad", "ink": "#28251e", "muted": "#6a604f", "accent": "#a9690f"},
}
FONTS = {("sans", 400): "plex-sans-400", ("sans", 600): "plex-sans-600", ("mono", 400): "plex-mono-400"}


@lru_cache(maxsize=64)
def font_faces(chars: str, used: tuple[tuple[str, int], ...]) -> str:
    rules = []
    for family, weight in used:
        with TTFont(ROOT / "fonts" / f"{FONTS[(family, weight)]}.woff2") as font:
            options = subset.Options()
            options.flavor = "woff2"
            options.layout_features = ["kern", "liga", "tnum"]
            selection = subset.Subsetter(options)
            selection.populate(text=chars)
            selection.subset(font)
            buffer = io.BytesIO()
            font.flavor = "woff2"
            font.save(buffer)
        encoded = base64.b64encode(buffer.getvalue()).decode()
        rules.append(
            f"@font-face{{font-family:P{family};font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{encoded}) format('woff2')}}"
        )
    return "".join(rules)


class Svg:
    def __init__(self, width: int, height: int, title: str):
        self.width, self.height, self.title = width, height, title
        self.parts: list[str] = []
        self.text = ""
        self.used: set[tuple[str, int]] = set()
        self.styles = ""

    def t(
        self,
        x: float,
        y: float,
        text: str,
        size: int = 16,
        family: str = "sans",
        weight: int = 400,
        fill: str = "ink",
        anchor: str = "start",
    ) -> None:
        self.text += text + " "
        self.used.add((family, weight))
        self.parts.append(
            f'<text x="{x}" y="{y}" class="{family} c-{fill}" font-size="{size}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{escape(text)}</text>'
        )

    def rule(self, y: float, x: float = 28, end: float | None = None) -> None:
        self.parts.append(f'<path d="M{x} {y}H{end or self.width - x}" class="rule"/>')

    def rect(self, x: float, y: float, width: float, height: float, fill: str = "accent") -> None:
        self.parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" height="{height:.2f}" class="c-{fill}"/>')

    def render(self, theme: str) -> str:
        style = font_faces("".join(sorted(set(self.text))), tuple(sorted(self.used)))
        style += ".sans{font-family:Psans,system-ui,sans-serif}.mono{font-family:Pmono,monospace}"
        for mode in ("light", "dark") if theme == "auto" else (theme,):
            colors = THEMES[mode]
            palette = "".join(f".c-{name}{{fill:{value}}}" for name, value in colors.items())
            palette += "".join(f".s-{name}{{stroke:{value}}}" for name, value in colors.items())
            palette += f".rule{{stroke:{colors['line']};stroke-width:1}}"
            palette += f".spark{{stroke:{colors['accent']};stroke-width:2;fill:none}}"
            style += (
                "@media(prefers-color-scheme:dark){" + palette + "}" if theme == "auto" and mode == "dark" else palette
            )
        style += self.styles
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}" role="img" aria-label="{escape(self.title)}">'
            f"<title>{escape(self.title)}</title><style>{style}</style>"
            f'<rect width="{self.width}" height="{self.height}" rx="8" class="c-bg"/>'
            + "".join(self.parts)
            + "</svg>\n"
        )


def number(value: float | int | None, suffix: str = "") -> str:
    return "unknown" if value is None else f"{value:,.0f}{suffix}"


def percent(value: float | None) -> str:
    return "unknown" if value is None else f"{value * 100:.0f}%"


def pair(first: int | None, second: int | None) -> str:
    if first is None or second is None:
        return "unknown"
    return f"{number(first)}/{number(second)}"


def timestamp(value: str | None) -> str:
    if not value:
        return "unknown"
    return dt.datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M UTC")


def sample_stamp(sample: Sample | None, now: dt.datetime) -> str:
    if sample is None:
        return "Sample unavailable"
    value = sample.data.get("updatedAt")
    if value is None:
        dates = [item["updatedAt"] for item in sample.data.get("gpus", []) if item.get("updatedAt")]
        value = min(dates) if dates else None
    origin = "Sampled" if value else "Collected"
    date = value or sample.collected_at
    age = now - dt.datetime.fromisoformat(date)
    status = " · not refreshed" if sample.stale else " · older sample" if age > dt.timedelta(hours=12) else ""
    return f"{origin} {timestamp(date)}{status}"


def data_for(samples: dict[str, Sample], name: str) -> Payload:
    return samples[name].data if name in samples else {}


@dataclass(frozen=True)
class Reading:
    label: str
    value: str
    detail: str
    source: str


def lab_rows(samples: dict[str, Sample], now: dt.datetime) -> list[Reading]:
    hosts = data_for(samples, "proxmox").get("hosts")
    network = data_for(samples, "network")
    storage = data_for(samples, "storage")
    unifi = data_for(samples, "unifi")
    gpus = data_for(samples, "gpu").get("gpus")
    host_count = (
        sum(item["up"] for item in hosts) if hosts and all(item.get("up") is not None for item in hosts) else None
    )
    gpu_count = sum(item.get("reporting") is True for item in gpus) if gpus else None
    memory = (
        sum(item["memoryTotal"] for item in gpus) / 2**30
        if gpus and all(item.get("memoryTotal") is not None for item in gpus)
        else None
    )
    return [
        Reading(
            "Compute",
            f"{pair(host_count, len(hosts) if hosts else None)} hosts up",
            "Proxmox · virtual machines and containers",
            "proxmox",
        ),
        Reading(
            "Network policy",
            f"{pair(network.get('enforcedEndpoints'), network.get('endpoints'))} endpoints",
            "Ingress or egress policy enforced",
            "network",
        ),
        Reading(
            "Backups",
            f"{pair(storage.get('backupPassed'), storage.get('backupRuns'))} recorded results OK",
            f"Latest result {timestamp(storage.get('newestBackup'))}",
            "storage",
        ),
        Reading(
            "Network",
            f"{pair(unifi.get('online'), unifi.get('devices'))} devices online",
            f"WAN latency {number(unifi.get('latencyMs'), ' ms')}",
            "unifi",
        ),
        Reading(
            "GPU",
            f"{number(gpu_count)} reporting · {number(memory, ' GiB')} VRAM",
            "Current readings and short history below",
            "gpu",
        ),
    ]


def header(config: Payload, mobile: bool) -> Svg:
    svg = Svg(336 if mobile else 840, 326 if mobile else 236, f"{config['name']}, {config['role']}")
    pad = 22 if mobile else 36
    svg.t(pad, 32, "giovannirco", 12, "mono", fill="accent")
    svg.t(pad, 76 if mobile else 99, config["name"], 27 if mobile else 42, weight=600)
    svg.t(pad, 109 if mobile else 135, "Staff Platform Engineer", 18 if mobile else 20, fill="muted")
    if mobile:
        svg.t(pad, 138, "Kubernetes · GitOps · observability", 14, fill="muted")
    else:
        svg.t(pad, 211, "Kubernetes / GitOps / observability", 14, "mono", fill="muted")
        svg.t(804, 211, "DESIGN → BUILD → RUN", 12, "mono", fill="accent", anchor="end")
    svg.rule(155 if mobile else 184, pad)
    blueprint.header_drawing(svg, mobile)
    return svg


def project_card(name: str, mobile: bool) -> Svg:
    descriptions = {
        "scout": "Job Scout workflow: listings, role research, then drafts for your review.",
        "platen": "Platen workflow: PDF documents, print and scan, and filing in Paperless-ngx.",
        "cpa": "CPA Prometheus workflow: requests become metrics for a Grafana dashboard.",
    }
    svg = Svg(336 if mobile else 840, 140 if mobile else 168, descriptions[name])
    blueprint.project(svg, name, mobile)
    return svg


def fleet(samples: dict[str, Sample], now: dt.datetime, mobile: bool) -> Svg:
    lab, nodes = data_for(samples, "lab"), data_for(samples, "nodes")
    states = cluster_states(nodes) if nodes else []
    readings = nodes.get("nodes", [])
    ready = (
        sum(node["ready"] for node in readings)
        if readings and all(node.get("ready") is not None for node in readings)
        else None
    )
    metrics = [
        (
            pair(states.count("ready"), len(states)) if states and "unknown" not in states else "unknown",
            "clusters ready",
        ),
        (pair(ready, len(nodes["nodes"]) if nodes else None), "nodes ready"),
        (number(lab.get("pods")), "pods"),
        (number(lab.get("cores")), "Kubernetes vCPU"),
        (number(lab.get("namespaces")), "namespaces"),
    ]
    svg = Svg(
        336 if mobile else 840,
        416 if mobile else 244,
        "Homelab capacity and readiness. " + "; ".join(f"{value} {label}" for value, label in metrics),
    )
    pad = 22 if mobile else 32
    svg.t(pad, 36, "FLEET / TALOS ON PROXMOX", 12, "mono", fill="accent")
    offset = blueprint.clusters(svg, states, mobile)
    svg.height += offset
    for index, (value, label) in enumerate(metrics):
        x = pad + (index % 2) * 157 if mobile else pad + index * 158
        y = offset + (91 + (index // 2) * 85 if mobile else 99)
        svg.t(x, y, value, 30 if mobile else 34, weight=600)
        svg.t(x, y + 25, label, 13 if mobile else 14, fill="muted")
    svg.rule(offset + (307 if mobile else 147), pad)
    svg.t(pad, offset + (333 if mobile else 174), "Ready = every node ready", 14, fill="muted")
    for index, source in enumerate(("nodes", "lab")):
        stamp = sample_stamp(samples.get(source), now)
        if mobile:
            stamp = stamp.replace(" · not refreshed", "").replace(" · older sample", "")
        svg.t(
            pad,
            offset + (360 if mobile else 201) + index * 20,
            f"{source.title()}: {stamp}",
            11 if mobile else 12,
            "mono",
            fill="muted",
        )
    if mobile and any(samples.get(key) and samples[key].stale for key in ("nodes", "lab")):
        svg.t(314, offset + 280, "NOT REFRESHED", 11, "mono", fill="accent", anchor="end")
    return svg


def operations(samples: dict[str, Sample], now: dt.datetime, mobile: bool) -> Svg:
    rows = lab_rows(samples, now)
    height = 90 + len(rows) * (136 if mobile else 108)
    svg = Svg(336 if mobile else 840, height, "; ".join(f"{row.label}: {row.value}. {row.detail}" for row in rows))
    pad = 22 if mobile else 32
    svg.t(pad, 36, "OPERATIONS / PUBLIC READINGS", 12, "mono", fill="accent")
    for index, row in enumerate(rows):
        y = 72 + index * (136 if mobile else 108)
        svg.rule(y - 18, pad)
        svg.t(pad, y + 6, row.label, 14, "mono", fill="accent")
        svg.t(pad if mobile else 214, y + (32 if mobile else 6), row.value, 17 if mobile else 21, weight=600)
        svg.t(pad if mobile else 214, y + (55 if mobile else 31), row.detail, 12 if mobile else 15, fill="muted")
        stamp, _, status = sample_stamp(samples.get(row.source), now).partition(" · ")
        svg.t(pad if mobile else 214, y + (79 if mobile else 55), stamp, 11 if mobile else 12, "mono", fill="muted")
        if status:
            svg.t(pad if mobile else 214, y + (99 if mobile else 75), status.upper(), 11, "mono", fill="accent")
    svg.t(pad, height - 20, "Refresh every six hours · dates are UTC", 12, fill="muted")
    return svg


def activity(samples: dict[str, Sample], now: dt.datetime, mobile: bool) -> Svg:
    data = data_for(samples, "github")
    svg = Svg(
        336 if mobile else 840,
        254 if mobile else 228,
        f"{number(data.get('total'))} GitHub contributions over the past year, grouped by week",
    )
    pad, width = (22, 292) if mobile else (32, 776)
    svg.t(pad, 34, "GITHUB / PAST YEAR", 12, "mono", fill="accent")
    svg.t(pad, 73, number(data.get("total")), 30, weight=600)
    svg.t(150 if mobile else 210, 71, "contributions", 15, fill="muted")
    weeks = data.get("weeks", [])
    if weeks:
        svg.styles += blueprint.MOTION
        maximum = max(1, max(week["count"] for week in weeks))
        step = width / len(weeks)
        points: list[str] = []
        for index, week in enumerate(weeks):
            height = 65 * week["count"] / maximum
            points.append(f"{'L' if points else 'M'}{pad + index * step + max(1, step - 2) / 2:.1f} {157 - height:.1f}")
            svg.rect(
                pad + index * step,
                157 - max(1, height),
                max(1, step - 2),
                max(1, height),
                "line",
            )
        blueprint.path(svg, " ".join(points), "trace s-accent", 'pathLength="1" data-history="weekly"')
        svg.t(pad, 181, weeks[0]["date"][:7], 12, "mono", fill="muted")
        svg.t(pad + width, 181, weeks[-1]["date"][:7], 12, "mono", fill="muted", anchor="end")
    else:
        svg.t(pad, 130, "Contribution history unavailable", 15, fill="muted")
    stamp, _, status = sample_stamp(samples.get("github"), now).partition(" · ")
    svg.t(pad, 210, stamp, 11 if mobile else 12, "mono", fill="muted")
    if status:
        svg.t(
            pad if mobile else 808,
            233 if mobile else 210,
            status.upper(),
            11,
            "mono",
            fill="accent",
            anchor="start" if mobile else "end",
        )
    return svg


def hardware(samples: dict[str, Sample], now: dt.datetime, mobile: bool) -> Svg:
    gpus = data_for(samples, "gpu").get("gpus", [])
    svg = Svg(
        336 if mobile else 840,
        82 + len(gpus) * (212 if mobile else 150),
        "GPU readings with the source's short utilization history",
    )
    pad = 22 if mobile else 32
    svg.t(pad, 35, "GPU / SHORT HISTORY", 12, "mono", fill="accent")
    for index, gpu in enumerate(gpus):
        y = 70 + index * (212 if mobile else 150)
        svg.rule(y - 18, pad)
        svg.t(pad, y + 6, f"GPU-{index + 1}", 16, "mono")
        svg.t(
            pad,
            y + 34,
            f"{percent(gpu.get('usage'))} use · {number(gpu.get('temperature'), ' °C')} · "
            f"{number(gpu.get('power'), ' W')}",
            15,
        )
        svg.t(
            pad,
            y + 60,
            "VRAM "
            + percent(ratio(gpu.get("memoryUsed"), gpu.get("memoryTotal")))
            + " of "
            + number(gpu["memoryTotal"] / 2**30 if gpu.get("memoryTotal") else None, " GiB"),
            14,
            fill="muted",
        )
        x, top, width = (pad, y + 78, 292) if mobile else (474, y - 5, 334)
        svg.rule(top + 47, x, x + width)
        history = gpu.get("history", [])
        if len(history) > 1:
            start, end = history[0][0], history[-1][0]
            points: list[str] = []
            for stamp, value in history:
                if value is None:
                    if points:
                        svg.parts.append(f'<path d="{" ".join(points)}" class="spark"/>')
                    points = []
                    continue
                position = x + width * (stamp - start) / max(1, end - start)
                points.append(f"{'L' if points else 'M'}{position:.1f} {top + 45 - value * 40:.1f}")
            if points:
                svg.parts.append(f'<path d="{" ".join(points)}" class="spark"/>')
            duration = round((end - start) / 60)
            svg.t(x, top + 67, f"{duration} min · 0–100% scale", 12, fill="muted")
        else:
            svg.t(x, top + 28, "History unavailable", 14, fill="muted")
        svg.t(
            pad,
            y + (172 if mobile else 114),
            "Sampled " + timestamp(gpu.get("updatedAt")),
            11 if mobile else 12,
            "mono",
            fill="muted",
        )
    if not gpus:
        svg.t(pad, 65, "GPU readings unavailable", 15, fill="muted")
    svg.title = svg.text + ". " + sample_stamp(samples.get("gpu"), now)
    return svg


def picture(name: str, alt: str) -> str:
    return (
        f"<p>\n<picture>\n"
        f'  <source media="(max-width: 600px)" srcset="cards/{name}-mobile.svg">\n'
        f'  <img alt="{escape(alt)}" src="cards/{name}.svg" width="840">\n</picture>\n</p>'
    )


def detail_tables(samples: dict[str, Sample], now: dt.datetime) -> str:
    lines = ["| Node | Ready | CPU | Memory | Pods |", "| :--- | :--- | ---: | ---: | ---: |"]
    for index, node in enumerate(data_for(samples, "nodes").get("nodes", [])):
        ready = {True: "yes", False: "no", None: "unknown"}[node.get("ready")]
        lines.append(
            f"| node-{index + 1:02} | {ready} | {percent(node.get('cpu'))} | "
            f"{percent(ratio(node.get('memoryUsed'), node.get('memoryTotal')))} | {number(node.get('pods'))} |"
        )
    lines += [
        "",
        sample_stamp(samples.get("nodes"), now),
        "",
        "| Host | CPU | Memory | VMs up | Containers up |",
        "| :--- | ---: | ---: | ---: | ---: |",
    ]
    for index, host in enumerate(data_for(samples, "proxmox").get("hosts", [])):
        lines.append(
            f"| Compute-{chr(65 + index)} | {percent(host.get('cpu'))} | "
            f"{percent(ratio(host.get('memoryUsed'), host.get('memoryTotal')))} | "
            f"{pair(host.get('vmsRunning'), host.get('vmsTotal'))} | "
            f"{pair(host.get('containersRunning'), host.get('containersTotal'))} |"
        )
    lines += ["", sample_stamp(samples.get("proxmox"), now), ""]
    network, unifi = data_for(samples, "network"), data_for(samples, "unifi")
    drops = network.get("dropsPerSecond")
    lines.append(
        f"Cilium: {number(network.get('flowsPerSecond'))} flows/s; "
        f"{drops if drops is not None else 'unknown'} drops/s. "
        "Endpoint enforcement counts ingress, egress or both; it does not measure default-deny coverage."
    )
    lines += ["", sample_stamp(samples.get("network"), now), ""]
    rates = [
        "unknown" if unifi.get(key) is None else f"{unifi[key] / 1_000_000:.2f} MB/s"
        for key in ("downloadBytes", "uploadBytes")
    ]
    lines.append(
        f"WAN: {rates[0]} down, {rates[1]} up. "
        f"Wi-Fi access points: {pair(unifi.get('apsOnline'), unifi.get('aps'))}; "
        f"switches: {pair(unifi.get('switchesOnline'), unifi.get('switches'))}; "
        f"gateways: {pair(unifi.get('gatewaysOnline'), unifi.get('gateways'))} online."
    )
    lines += ["", sample_stamp(samples.get("unifi"), now), ""]
    storage = data_for(samples, "storage")
    lines.append(
        f"Disk checks: {pair(storage.get('disksPassing'), storage.get('disks'))} passing. "
        "Backup results are the latest recorded job results, not proof that every guest is covered or restores work."
    )
    return "\n".join(lines)


def build_outputs(samples: dict[str, Sample], config: Payload, now: dt.datetime) -> dict[str, str]:
    outputs: dict[str, str] = {}
    pictures: dict[str, str] = {}
    for mobile in (False, True):
        cards = {
            "header": header(config, mobile),
            "fleet": fleet(samples, now, mobile),
            "operations": operations(samples, now, mobile),
            "activity": activity(samples, now, mobile),
            "hardware": hardware(samples, now, mobile),
            **{name: project_card(name, mobile) for name in ("scout", "platen", "cpa")},
        }
        for name, svg in cards.items():
            suffix = "-mobile" if mobile else ""
            outputs[f"cards/{name}{suffix}.svg"] = svg.render("auto")
            pictures[name] = picture(name, svg.title)
    readme = (ROOT / "README.template.md").read_text()
    streak = ROOT / "cards/streak.svg"
    pictures["streak"] = picture(
        "streak",
        streak_alt(streak)
        if streak.exists()
        else "GitHub total contributions, current daily streak and longest daily streak",
    )
    for name, value in pictures.items():
        readme = readme.replace("{{picture:" + name + "}}", value)
    github = data_for(samples, "github")
    for name in config["featured"]:
        repo = github.get("repos", {}).get(name)
        metadata = "Activity unavailable"
        if repo:
            metadata = (
                f"{escape(repo.get('language') or 'Language unreported')} · updated "
                + timestamp(repo.get("pushed_at"))[:10]
            )
            if repo.get("stars"):
                metadata += f" · {number(repo['stars'])} stars"
        readme = readme.replace("{{meta:" + name + "}}", metadata)
    stamps = "\n".join(f"- {name}: {sample_stamp(sample, now)}" for name, sample in samples.items())
    readme = readme.replace("{{sample_dates}}", stamps or "Samples unavailable.")
    readme = readme.replace("{{details}}", detail_tables(samples, now))
    readme = readme.replace("{{github_stamp}}", sample_stamp(samples.get("github"), now))
    if re.search(r"\{\{[^}]+\}\}", readme):
        raise ValueError("unresolved README template token")
    outputs["README.md"] = readme
    outputs["cards/data.json"] = (
        json.dumps({name: sample.model_dump() for name, sample in samples.items()}, indent=2) + "\n"
    )
    return outputs


def main() -> int:
    config = json.loads((ROOT / "config.json").read_text())
    snapshot = ROOT / "cards/data.json"
    previous = (
        {name: Sample.model_validate(value) for name, value in json.loads(snapshot.read_text()).items()}
        if snapshot.exists()
        else {}
    )
    now = dt.datetime.now(dt.timezone.utc)

    def fetch(name: str) -> Payload:
        if name != "github":
            return request_json(f"{config['lab_api']}/api/insight/{name}")
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN is required for GitHub data")
        return parse_github(
            request_json(
                "https://api.github.com/graphql",
                token,
                {"query": GITHUB_QUERY, "variables": {"login": config["login"]}},
            ),
            config["featured"],
        )

    names = [*MODELS, "github"]
    samples, failures = collect(names, previous, fetch, now)
    for name in failures:
        print(f"{name}: refresh failed; previous dated sample retained if available", file=sys.stderr)
    if len(failures) == len(names):
        print("All sources failed; no files changed", file=sys.stderr)
        return 1
    outputs = build_outputs(samples, config, now)
    for path, content in outputs.items():
        destination = ROOT / path
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(content)
        temporary.replace(destination)
    print(f"Rendered {len(outputs) - 2} SVGs; {len(names) - len(failures)}/{len(names)} sources refreshed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
