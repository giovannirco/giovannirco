"""Animated diagrams for the profile's systems blueprint."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from render import Svg

STILL = (
    ".draw,.signal,.scan,.paper,.trace,.halo{animation:none;transform:none;stroke-dashoffset:0}"
    ".signal,.scan,.halo{display:none}"
)
ANIMATED_CARDS = {"header", "fleet", "activity", "scout", "platen", "cpa"}

MOTION = (
    """
.wire,.outline{stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}
.wire,.outline:not(.c-bg){fill:none}
.draw{stroke-dasharray:1;stroke-dashoffset:0;animation:draw 3s cubic-bezier(.16,1,.3,1) both}
.signal{fill:none;stroke-width:3;stroke-linecap:round;stroke-dasharray:.035 .965;opacity:0;
animation:signal 12s linear 2s infinite}
.phase{animation-delay:4s}.later{animation-delay:6s}
.scan{animation:scan 10s cubic-bezier(.16,1,.3,1) 1s infinite;opacity:0}
.paper{animation:paper 10s cubic-bezier(.16,1,.3,1) 1s infinite}
.trace{fill:none;stroke-width:1.5;stroke-dasharray:1;stroke-dashoffset:0;
animation:draw 3s cubic-bezier(.16,1,.3,1) both}
.halo{fill:none;stroke-width:1;transform-box:fill-box;transform-origin:center;
animation:halo 12s ease-out 3s infinite;opacity:0}
@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
@keyframes signal{0%{stroke-dashoffset:.04;opacity:0}4%{opacity:1}
38%{stroke-dashoffset:-1;opacity:1}42%,100%{stroke-dashoffset:-1;opacity:0}}
@keyframes scan{0%,48%,100%{transform:translateY(0);opacity:0}
8%{transform:translateY(0);opacity:1}36%{transform:translateY(28px);opacity:1}
44%{transform:translateY(28px);opacity:0}}
@keyframes paper{0%,55%,100%{transform:translateY(0)}12%{transform:translateY(-9px)}
38%{transform:translateY(5px)}}
@keyframes halo{0%,38%,100%{opacity:0;transform:scale(1)}
8%{opacity:.7;transform:scale(1)}32%{opacity:0;transform:scale(2)}}
"""
    + "@media(prefers-reduced-motion:reduce){"
    + STILL
    + "}"
)


def path(svg: Svg, route: str, classes: str = "wire s-line", extra: str = "") -> None:
    svg.parts.append(f'<path d="{route}" class="{classes}" {extra}/>')


def route(svg: Svg, points: str, phase: str = "") -> None:
    path(svg, points, "wire s-line draw", 'pathLength="1"')
    path(svg, points, "signal s-accent " + phase, 'pathLength="1" aria-hidden="true"')


def circle(svg: Svg, x: float, y: float, radius: float, classes: str) -> None:
    svg.parts.append(f'<circle cx="{x}" cy="{y}" r="{radius}" class="{classes}"/>')


def box(svg: Svg, x: float, y: float, width: float, height: float, classes: str = "outline s-line") -> None:
    svg.parts.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="3" class="{classes}"/>')


def header_drawing(svg: Svg, mobile: bool) -> None:
    svg.styles += MOTION
    left, top, width = (24, 171, 288) if mobile else (520, 37, 280)
    for grid_x in range(left, left + width + 1, 24):
        for y in range(top, top + 109, 24):
            circle(svg, grid_x, y, 0.7, "c-line")
    center = left + width / 2
    y = top + 55
    points = [(left + 12, y), (center, y - 38), (center, y + 38), (left + width - 12, y)]
    for index, (x, target_y) in enumerate(points):
        route(svg, f"M{center} {y}H{(center + x) / 2}V{target_y}H{x}", "phase" if index % 2 else "")
        box(svg, x - 9, target_y - 9, 18, 18, "outline s-accent")
        circle(svg, x, target_y, 2, "c-accent")
    box(svg, center - 17, y - 17, 34, 34, "c-bg s-accent outline")
    path(svg, f"M{center - 8} {y - 3}l5 4 -5 4M{center + 1} {y + 5}h7", "wire s-accent")
    circle(svg, center, y, 23, "halo s-accent")
    svg.t(left, top + 128, "BUILD", 11, "mono", fill="muted")
    svg.t(center, top + 128, "SHIP", 11, "mono", fill="muted", anchor="middle")
    svg.t(left + width, top + 128, "OPERATE", 11, "mono", fill="muted", anchor="end")


def document(svg: Svg, x: float, y: float) -> None:
    path(svg, f"M{x} {y}h22l8 8v32h-30zM{x + 22} {y}v8h8", "outline s-muted")
    path(svg, f"M{x + 7} {y + 17}h16M{x + 7} {y + 23}h16M{x + 7} {y + 29}h10", "wire s-line")


def project(svg: Svg, name: str, mobile: bool) -> None:
    svg.styles += MOTION
    centers = (66, 168, 270) if mobile else (132, 420, 708)
    y = 63
    for index in range(2):
        route(svg, f"M{centers[index] + 28} {y}H{centers[index + 1] - 28}", "phase" if index else "")
    left, center, right = centers
    labels: tuple[str, str, str]
    if name == "scout":
        document(svg, left - 19, y - 25)
        document(svg, left - 11, y - 17)
        path(svg, f"M{center - 23} {y - 20}h46l-17 22v16l-12 5V{y + 2}z", "outline s-accent")
        for offset in (-8, 0, 8):
            circle(svg, center + offset, y - 12, 1.5, "c-accent")
        box(svg, right - 23, y - 25, 46, 50, "outline s-muted")
        for offset in (-11, 2, 15):
            path(svg, f"M{right - 15} {y + offset}l3 3 5-6", "wire s-accent")
            path(svg, f"M{right} {y + offset}h15", "wire s-line")
        labels = ("Listings", "Research", "Your review")
    elif name == "platen":
        document(svg, left - 15, y - 20)
        svg.parts.append('<g class="paper">')
        box(svg, center - 15, y - 31, 30, 25, "c-bg s-muted outline")
        path(svg, f"M{center - 8} {y - 23}h16M{center - 8} {y - 17}h12", "wire s-line")
        svg.parts.append("</g>")
        box(svg, center - 27, y - 8, 54, 30, "c-bg s-accent outline")
        circle(svg, center + 18, y + 1, 2, "c-accent")
        box(svg, center - 15, y + 12, 30, 20, "c-bg s-muted outline")
        path(svg, f"M{center - 9} {y + 19}h18M{center - 9} {y + 25}h12", "wire s-line")
        box(svg, right - 23, y - 24, 46, 48, "outline s-muted")
        path(svg, f"M{right - 23} {y - 8}h46M{right - 6} {y + 4}h12", "wire s-line")
        path(svg, f"M{right - 19} {y - 18}h38", "wire s-accent scan")
        labels = ("PDF", "Print / scan", "Paperless")
    elif name == "cpa":
        for index, offset in enumerate((-17, 0, 17)):
            circle(svg, left - 15, y + offset, 3, "outline s-muted")
            path(svg, f"M{left - 7} {y + offset}h{18 + index * 4}", "wire s-muted")
        for index, height in enumerate((19, 38, 28)):
            x = center - 20 + index * 16
            box(svg, x, y + 20 - height, 9, height, "outline s-accent")
        path(svg, f"M{center - 25} {y + 25}h50", "wire s-line")
        box(svg, right - 27, y - 24, 54, 41, "outline s-muted")
        path(svg, f"M{right - 9} {y + 28}h18M{right} {y + 17}v11", "wire s-muted")
        path(svg, f"M{right - 20} {y + 7}l9-9 8 4 8-16 15 6", "trace s-accent", 'pathLength="1"')
        labels = ("Requests", "Metrics", "Grafana")
    else:
        raise ValueError(f"Unknown blueprint project: {name}")
    for x, label in zip(centers, labels, strict=True):
        svg.t(x, 117, label, 12 if mobile else 16, anchor="middle")
    if not mobile:
        svg.t(
            32, 151, {"scout": "JOB SCOUT", "platen": "PLATEN", "cpa": "CPA PROMETHEUS"}[name], 10, "mono", fill="muted"
        )
        svg.t(808, 151, "WORKFLOW", 10, "mono", fill="muted", anchor="end")


def clusters(svg: Svg, states: list[str], mobile: bool) -> int:
    svg.styles += MOTION
    if not states:
        svg.t(22 if mobile else 32, 80, "Cluster samples unavailable", 15, fill="muted")
        return 62
    columns = 3 if mobile else 6
    step, pad = (101, 22) if mobile else (132, 32)
    for index, state in enumerate(states):
        x, y = pad + index % columns * step, 62 + index // columns * 102
        svg.parts.append(f'<g data-cluster="{index + 1:02}" data-state="{state}">')
        svg.t(x, y + 6, f"CLUSTER {index + 1:02}", 10, "mono", fill="muted")
        for offset in (0, 11, 22):
            box(svg, x, y + 17 + offset, 44, 8, "outline s-line")
            circle(svg, x + 37, y + 21 + offset, 1.5, "c-accent" if state == "ready" else "c-muted")
        if state == "ready":
            circle(svg, x + 37, y + 32, 4, "halo s-accent")
        elif state == "degraded":
            path(svg, f"M{x + 54} {y + 23}v10M{x + 54} {y + 38}v1", "wire s-accent")
        else:
            path(svg, f"M{x + 50} {y + 32}h8", "wire s-muted")
        svg.t(x, y + 70, state, 12, fill="accent" if state == "degraded" else "muted")
        svg.parts.append("</g>")
        svg.title += f". Cluster {index + 1:02}: {state}"
    return ((len(states) + columns - 1) // columns) * 102 + 16
