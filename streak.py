"""Adapt a pinned GitHub Readme Streak Stats SVG for the profile."""

import argparse
import copy
import datetime as dt
import re
from pathlib import Path
from xml.etree import ElementTree as ET

NS = "{http://www.w3.org/2000/svg}"
ET.register_namespace("", NS[1:-1])
COLORS = {"#f6f2e8": "bg", "#cbc1ad": "line", "#28251e": "ink", "#6a604f": "muted", "#a9690f": "accent"}
TAGS = {"svg", "defs", "clipPath", "rect", "mask", "ellipse", "g", "line", "path", "circle", "text", "tspan"}
DATE_RANGE = r"\d{4}-\d{2}-\d{2}(?: - (?:\d{4}-\d{2}-\d{2}|Present))?"


def read_upstream(source: str) -> tuple[ET.Element, list[ET.Element], str]:
    if len(source) > 100_000 or "<!" in source:
        raise ValueError("Streak SVG contains an unexpected declaration or exceeds the size limit")
    try:
        root = ET.fromstring(source)
    except ET.ParseError as error:
        raise ValueError("Streak output is not valid SVG") from error
    if root.tag != NS + "svg" or root.get("viewBox") != "0 0 840 195":
        raise ValueError("Streak SVG has an unexpected layout")
    for element in root.iter():
        if element.tag not in {NS + tag for tag in TAGS}:
            raise ValueError("Streak SVG contains an unsupported element")
        for name, value in element.attrib.items():
            if name.startswith("{") or name.lower().startswith("on") or "href" in name.lower():
                raise ValueError("Streak SVG contains an unsafe attribute")
            if "url(" in value and value not in {"url(#outer_rectangle)", "url(#mask_out_ring_behind_fire)"}:
                raise ValueError("Streak SVG contains an external reference")
        style = element.attrib.pop("style", "")
        if any(
            item.strip() not in {"", "isolation: isolate", "opacity: 1", "font-size: 28px"} for item in style.split(";")
        ):
            raise ValueError("Streak SVG must be generated with animations disabled")
        for attribute in ("fill", "stroke"):
            color = element.get(attribute)
            if color and color not in {*COLORS, "none", "white", "black"}:
                raise ValueError("Streak SVG does not use the expected palette")
    container = root.find(NS + "g")
    if container is None or len(container) != 5:
        raise ValueError("Streak SVG has an unexpected panel structure")
    panels = list(container)[2:]
    labels = ("Total Contributions", "Current Streak", "Longest Streak")
    summaries = []
    for panel, label in zip(panels, labels, strict=True):
        texts = panel.findall(f".//{NS}text")
        values = [" ".join("".join(text.itertext()).split()) for text in texts]
        if len(values) != 3 or label not in values:
            raise ValueError("Streak SVG statistic labels changed")
        count = next((value for value in values if re.fullmatch(r"(?:\d{1,3}(?:,\d{3})+|\d+)", value)), None)
        dates = next((value for value in values if re.fullmatch(DATE_RANGE, value)), None)
        if count is None or dates is None:
            raise ValueError("Streak SVG has an invalid statistic or date range")
        for date in dates.split(" - "):
            if date != "Present":
                dt.date.fromisoformat(date)
        if label == "Total Contributions":
            summaries.append(f"{count} total contributions ({dates})")
        else:
            summaries.append(f"{label.lower().replace('streak', 'daily streak')}: {count} days ({dates})")
    return root, panels, "; ".join(summaries)


def wrap_panel_text(panel: ET.Element) -> None:
    for text in panel.findall(f".//{NS}text"):
        value = " ".join("".join(text.itertext()).split())
        if value in {"Total Contributions", "Longest Streak"}:
            lines = value.split(" ")
            initial_offset = "-7"
        elif " - " in value:
            start, end = value.split(" - ")
            lines = [start, "- " + end]
            initial_offset = "0"
        else:
            continue
        for child in list(text):
            text.remove(child)
        text.text = None
        for index, line in enumerate(lines):
            ET.SubElement(text, NS + "tspan", {"x": "0", "dy": "16" if index else initial_offset}).text = line


def adapt_streak(source: str, now: dt.datetime, mobile: bool) -> str:
    from render import Svg

    root, panels, summary = read_upstream(source)
    stamp = "Collected " + now.astimezone(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    svg = Svg(336 if mobile else 840, 410 if mobile else 250, f"GitHub Streak Stats. {summary}. {stamp}.")
    svg.t(22 if mobile else 32, 30, "GITHUB / DAILY STREAKS", 12, "mono", fill="accent")
    mask = root.find(f".//{NS}mask")
    if mask is None:
        raise ValueError("Streak SVG ring mask is missing")
    definitions = ET.Element(NS + "defs")
    definitions.append(copy.deepcopy(mask))
    svg.parts.append(ET.tostring(definitions, encoding="unicode"))
    transforms = ((-56, 190), (-252, 28), (-448, 190)) if mobile else ((0, 38),) * 3
    for index, (panel, (x, y)) in enumerate(zip(panels, transforms, strict=True)):
        if mobile and index != 1:
            wrap_panel_text(panel)
        panel.set("transform", f"translate({x},{y})")
        for element in panel.iter():
            classes = []
            for attribute in ("fill", "stroke"):
                color = element.get(attribute)
                if color in COLORS:
                    classes.append(("c-" if attribute == "fill" else "s-") + COLORS[color])
                    del element.attrib[attribute]
            if element.tag == NS + "text":
                element.set("font-family", "Psans,system-ui,sans-serif")
                weight = 600 if element.get("font-weight") == "700" else 400
                element.set("font-weight", str(weight))
                svg.used.add(("sans", weight))
                svg.text += "".join(element.itertext())
            if classes:
                element.set("class", " ".join(classes))
        svg.parts.append(ET.tostring(panel, encoding="unicode"))
    if mobile:
        svg.rule(230, 22)
        svg.parts.append('<path d="M168 248V365" class="rule"/>')
    else:
        svg.parts.append('<path d="M280 66V208M560 66V208" class="rule"/>')
    svg.t(22 if mobile else 32, 390 if mobile else 233, stamp, 12, fill="muted")
    output = svg.render("auto")
    stroke_css = ".s-accent{stroke:#a9690f}@media(prefers-color-scheme:dark){.s-accent{stroke:#e8a33d}}"
    return output.replace("</style>", stroke_css + "</style>")


def streak_alt(path: Path) -> str:
    root = ET.fromstring(path.read_text())
    title = root.get("aria-label")
    if not title:
        raise ValueError("Streak card is missing its accessible summary")
    return title


def publish_streak(source: Path, destination: Path, now: dt.datetime, error_log: Path | None = None) -> None:
    if error_log is not None and error_log.exists() and error_log.read_text().strip():
        raise ValueError("Streak generator reported errors; refusing to publish possibly incomplete history")
    raw = source.read_text()
    raw = re.sub(r"<!--.*?-->", "", raw, flags=re.DOTALL)
    outputs = {"streak.svg": adapt_streak(raw, now, False), "streak-mobile.svg": adapt_streak(raw, now, True)}
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        temporary = destination / (name + ".tmp")
        temporary.write_text(content)
        temporary.replace(destination / name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "cards")
    parser.add_argument("--error-log", type=Path)
    arguments = parser.parse_args()
    publish_streak(arguments.source, arguments.output, dt.datetime.now(dt.timezone.utc), arguments.error_log)


if __name__ == "__main__":
    main()
