import datetime as dt
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
from fontTools.ttLib import TTFont

from profile_data import Sample, normalize
from render import FONTS, activity, build_outputs, fleet, header

NOW = dt.datetime(2026, 10, 26, 12, tzinfo=dt.timezone.utc)
STAMP = "2026-10-26T11:00:00Z"
ROOT = Path(__file__).parent
NS = {"s": "http://www.w3.org/2000/svg"}


@pytest.fixture(scope="module")
def outputs():
    return build_outputs({}, json.loads((ROOT / "config.json").read_text()), NOW)


@pytest.mark.parametrize("name,meaning", [("scout", "review"), ("platen", "scan"), ("cpa", "metrics")])
def test_project_schematics_are_accessible_responsive_and_linked(outputs, name, meaning):
    for suffix, width in (("", "840"), ("-mobile", "336")):
        path = f"cards/{name}{suffix}.svg"
        root = ET.fromstring(outputs[path])
        assert root.attrib["width"] == width
        assert meaning in root.attrib["aria-label"].lower()
        assert path in outputs["README.md"]
        assert not root.findall(".//s:script", NS)
        assert not root.findall(".//s:image", NS)
        assert "https://" not in outputs[path]
        assert "prefers-reduced-motion:reduce" in outputs[path]
        assert "animation:none" in outputs[path]
        assert "prefers-color-scheme:dark" in outputs[path]


def test_header_identity_is_visible_outside_animation_groups():
    card = header(json.loads((ROOT / "config.json").read_text()), False)
    root = ET.fromstring(card.render("auto"))
    assert any("Giovanni" in (node.text or "") for node in root.findall("s:text", NS))
    assert root.findall(".//s:path[@pathLength='1']", NS)
    assert "prefers-reduced-motion:reduce" in root.find("s:style", NS).text


def test_readme_includes_local_streak_picture_and_upstream_credit(outputs):
    assert 'src="cards/streak.svg?v=' in outputs["README.md"]
    assert 'srcset="cards/streak-mobile.svg?v=' in outputs["README.md"]
    assert "https://github.com/DenverCoder1/github-readme-streak-stats" in outputs["README.md"]
    assert "streak-stats.demolab.com" not in outputs["README.md"]


def test_image_versions_change_with_content_and_are_stable_between_builds(outputs):
    config = json.loads((ROOT / "config.json").read_text())
    same = build_outputs({}, config, NOW)
    changed = build_outputs({"github": Sample(data={"total": 42}, collected_at=STAMP)}, config, NOW)
    pattern = r"cards/activity.svg\?v=([a-f0-9]+)"
    original = re.search(pattern, outputs["README.md"])
    assert original is not None
    assert original.group(1) == re.search(pattern, same["README.md"]).group(1)
    assert original.group(1) != re.search(pattern, changed["README.md"]).group(1)
    assert re.search(r"cards/activity-mobile.svg\?v=[a-f0-9]+", outputs["README.md"])


def test_cluster_diagram_labels_degraded_unknown_and_ready_without_private_names():
    data = normalize(
        "nodes",
        {
            "clusters": [{"id": "private-a"}, {"id": "private-b"}, {"id": "private-c"}],
            "nodes": [{"cluster": "private-a", "ready": False}, {"cluster": "private-c", "ready": True}],
            "updatedAt": STAMP,
        },
    )
    card = fleet({"nodes": Sample(data=data, collected_at=STAMP)}, NOW, True)
    root = ET.fromstring(card.render("auto"))
    groups = root.findall(".//s:g[@data-cluster]", NS)
    assert [group.attrib["data-state"] for group in groups] == ["degraded", "unknown", "ready"]
    assert "Cluster 01: degraded" in card.title
    assert "Cluster 02: unknown" in card.title
    assert "Cluster 03: ready" in card.title
    assert "private-" not in ET.tostring(root, encoding="unicode")
    for group in groups:
        assert group.attrib["data-state"] in " ".join(group.itertext())


def test_missing_clusters_do_not_draw_invented_machines():
    root = ET.fromstring(fleet({}, NOW, True).render("auto"))
    assert not root.findall(".//s:g[@data-cluster]", NS)
    assert "Cluster samples unavailable" in " ".join(root.itertext())


def test_contribution_trace_uses_actual_weekly_counts():
    samples = {
        "github": Sample(
            data={"total": 10, "weeks": [{"date": "2026-10-11", "count": 0}, {"date": "2026-10-18", "count": 10}]},
            collected_at=STAMP,
        )
    }
    root = ET.fromstring(activity(samples, NOW, True).render("auto"))
    trace = root.find("s:path[@data-history='weekly']", NS)
    assert trace is not None
    assert trace.attrib["d"] == "M94.0 157.0 L240.0 92.0"
    assert "10 GitHub contributions" in root.attrib["aria-label"]


def test_blueprint_mobile_text_fits_without_scaling_down(outputs):
    for name in ("header", "scout", "platen", "cpa", "fleet"):
        root = ET.fromstring(outputs[f"cards/{name}-mobile.svg"])
        for node in root.findall(".//s:text", NS):
            family = node.attrib["class"].split()[0]
            with TTFont(ROOT / "fonts" / (FONTS[family, int(node.attrib["font-weight"])] + ".woff2")) as font:
                cmap = font.getBestCmap()
                width = sum(font["hmtx"][cmap[ord(char)]][0] for char in node.text or "")
                width *= float(node.attrib["font-size"]) / font["head"].unitsPerEm
            x = float(node.attrib["x"])
            if node.attrib["text-anchor"] == "end":
                x -= width
            if node.attrib["text-anchor"] == "middle":
                x -= width / 2
            assert 10 <= x and x + width <= 326, (name, node.text, x, width)
