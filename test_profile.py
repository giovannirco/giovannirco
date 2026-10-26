import datetime as dt
import json
from pathlib import Path
from xml.etree import ElementTree

import pytest
from pydantic import ValidationError

from profile_data import Sample, cluster_states, collect, normalize, parse_github, ratio

NOW = dt.datetime(2026, 10, 26, 12, tzinfo=dt.timezone.utc)
STAMP = "2026-10-26T11:00:00Z"


@pytest.fixture
def nodes():
    return {
        "clusters": [{"id": "a", "name": "Public alias"}, {"id": "b"}],
        "nodes": [
            {"cluster": "a", "ready": True},
            {"cluster": "a", "ready": False},
        ],
        "updatedAt": STAMP,
    }


def test_cluster_readiness_requires_every_node_and_missing_is_unknown(nodes):
    assert cluster_states(normalize("nodes", nodes)) == ["degraded", "unknown"]


def test_cluster_with_unknown_node_cannot_be_ready(nodes):
    nodes["nodes"][1]["ready"] = None
    assert cluster_states(normalize("nodes", nodes)) == ["unknown", "unknown"]


def test_payload_only_keeps_selected_public_fields(nodes):
    nodes["secret"] = "never persist"
    nodes["nodes"][0]["address"] = "never persist"
    result = json.dumps(normalize("nodes", nodes), default=str)
    assert "never persist" not in result
    assert "Public alias" not in result


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf")])
def test_invalid_capacity_rejected(value):
    with pytest.raises(ValidationError):
        normalize("lab", {"clusters": value, "updatedAt": STAMP})


def test_nonreporting_host_has_no_trusted_usage():
    data = normalize("proxmox", {"hosts": [{"reporting": False, "cpu": 0.9, "up": True}], "updatedAt": STAMP})
    assert data["hosts"][0]["cpu"] is None
    assert data["hosts"][0]["up"] is None


def test_zero_denominator_and_missing_values_are_not_zero_percent():
    assert ratio(1, 0) is None
    assert ratio(None, 10) is None
    assert ratio(0, 10) == 0


def test_storage_does_not_invent_source_sample_time():
    result = normalize("storage", {"backupPassed": 29, "backupRuns": 29, "guests": 52, "newestBackup": STAMP})
    assert result["newestBackup"] == STAMP
    assert result.get("updatedAt") is None


def test_failed_source_retains_dated_sample_and_marks_it_stale():
    previous = {"lab": Sample(data={"pods": 5}, collected_at=STAMP)}

    def offline(name):
        raise OSError("offline")

    samples, failures = collect(["lab"], previous, offline, NOW)
    assert samples["lab"].data == {"pods": 5}
    assert samples["lab"].collected_at == STAMP
    assert samples["lab"].stale
    assert failures == ["lab"]


def test_one_failed_feed_does_not_discard_successful_feed():
    def fetch(name):
        if name == "nodes":
            raise OSError("offline")
        return {"pods": 42, "updatedAt": STAMP}

    samples, failures = collect(["lab", "nodes"], {}, fetch, NOW)
    assert samples["lab"].data["pods"] == 42
    assert "nodes" not in samples
    assert failures == ["nodes"]


def test_graphql_error_is_failure_not_empty_activity():
    with pytest.raises(ValueError, match="GraphQL"):
        parse_github({"errors": [{"message": "rate limited"}]}, ["platen"])


def test_graphql_preserves_week_dates_and_repository_metadata():
    payload = {
        "data": {
            "user": {
                "repositories": {
                    "nodes": [
                        {"name": "platen", "stargazerCount": 2, "pushedAt": STAMP, "primaryLanguage": {"name": "Go"}}
                    ],
                    "pageInfo": {"hasNextPage": False},
                },
                "contributionsCollection": {
                    "contributionCalendar": {
                        "totalContributions": 3,
                        "weeks": [
                            {
                                "firstDay": "2026-10-25",
                                "contributionDays": [{"date": "2026-10-26", "contributionCount": 3}],
                            }
                        ],
                    }
                },
            }
        }
    }
    result = parse_github(payload, ["platen"])
    assert result["weeks"] == [{"date": "2026-10-25", "count": 3}]
    assert result["repos"]["platen"]["language"] == "Go"
    with pytest.raises(ValueError, match="missing"):
        parse_github(payload, ["missing-repository"])


def test_svg_escapes_text_and_accessible_title():
    from render import Svg

    svg = Svg(336, 100, 'Title " & <test>')
    svg.t(20, 30, "<script>& text")
    output = svg.render("light")
    document = ElementTree.fromstring(output)
    assert document.attrib["aria-label"] == 'Title " & <test>'
    assert "<script>" not in output
    assert "data:font/woff2;base64," in output


def test_mobile_cards_have_own_layout_and_inherit_both_themes():
    from render import build_outputs

    root = Path(__file__).parent
    outputs = build_outputs({}, json.loads((root / "config.json").read_text()), NOW)
    for name in ("header", "activity", "fleet", "operations"):
        mobile = ElementTree.fromstring(outputs[f"cards/{name}-mobile.svg"])
        desktop = ElementTree.fromstring(outputs[f"cards/{name}.svg"])
        assert mobile.attrib["width"] == "336"
        assert desktop.attrib["width"] == "840"
        assert f"cards/{name}-mobile.svg" in outputs["README.md"]
        for path in (f"cards/{name}.svg", f"cards/{name}-mobile.svg"):
            assert "@media(prefers-color-scheme:dark)" in outputs[path]
            assert "#14130f" in outputs[path] and "#f6f2e8" in outputs[path]
    assert "prefers-color-scheme" not in outputs["README.md"]
    assert "{{" not in outputs["README.md"]
    assert "unavailable" in outputs["README.md"].lower()


def test_stale_sample_keeps_original_date_in_accessible_readme():
    from render import build_outputs

    root = Path(__file__).parent
    samples = {"lab": Sample(data={"pods": 42}, collected_at=STAMP, stale=True)}
    output = build_outputs(samples, json.loads((root / "config.json").read_text()), NOW)
    assert "not refreshed" in output["README.md"].lower()
    assert "2026-10-26 11:00 UTC" in output["README.md"]


def test_backup_wording_does_not_claim_coverage_or_restore_testing():
    from render import lab_rows

    samples = {
        "storage": Sample(
            data=normalize("storage", {"backupPassed": 29, "backupRuns": 29, "guests": 52, "newestBackup": STAMP}),
            collected_at=STAMP,
        )
    }
    rows = lab_rows(samples, NOW)
    text = " ".join(str(row) for row in rows)
    assert "29/29" in text
    assert "recorded results" in text
    assert "52/52" not in text


def test_workflow_keeps_schedule_and_runs_self_enable_on_failure():
    workflow = (Path(__file__).parent / ".github/workflows/cards.yml").read_text()
    assert "17 */6 * * *" in workflow
    assert "always() && github.event_name == 'schedule'" in workflow
    assert "docker" not in workflow
    assert "pytest" in workflow


def test_gpu_fraction_is_rendered_as_percentage_and_scaled_history():
    from render import hardware

    samples = {
        "gpu": Sample(
            data=normalize(
                "gpu", {"gpus": [{"reporting": True, "usage": 0.8, "history": [[1, 0], [61, 0.8]], "updatedAt": STAMP}]}
            ),
            collected_at=STAMP,
        )
    }
    svg = hardware(samples, NOW, True)
    assert "80% use" in svg.text
    assert "L314.0 161.0" in "".join(svg.parts)
    assert "80%" in svg.title
    with pytest.raises(ValidationError):
        normalize("gpu", {"gpus": [{"reporting": True, "usage": 80}]})


def test_unknown_readiness_is_not_reported_as_zero(nodes):
    from render import fleet, lab_rows

    nodes["nodes"][0]["ready"] = None
    nodes["nodes"][1]["ready"] = None
    samples = {
        "nodes": Sample(data=normalize("nodes", nodes), collected_at=STAMP),
        "proxmox": Sample(
            data=normalize("proxmox", {"hosts": [{"reporting": False}], "updatedAt": STAMP}), collected_at=STAMP
        ),
    }
    assert "0/2" not in fleet(samples, NOW, True).text
    assert "0/1" not in str(lab_rows(samples, NOW))


def test_missing_card_text_fits_mobile_canvas():
    from fontTools.ttLib import TTFont

    from render import FONTS, fleet, operations

    for card in (fleet({}, NOW, True), operations({}, NOW, True)):
        document = ElementTree.fromstring(card.render("dark"))
        for text in document.findall("{http://www.w3.org/2000/svg}text"):
            family = text.attrib["class"].split()[0]
            with TTFont(
                Path(__file__).parent / "fonts" / (FONTS[family, int(text.attrib["font-weight"])] + ".woff2")
            ) as font:
                cmap = font.getBestCmap()
                width = sum(font["hmtx"][cmap[ord(char)]][0] for char in text.text or "")
                width *= float(text.attrib["font-size"]) / font["head"].unitsPerEm
            x = float(text.attrib["x"])
            if text.attrib["text-anchor"] == "end":
                x -= width
            assert x >= 10 and x + width <= 326, text.text


def test_activity_alt_contains_contribution_count():
    from render import activity

    card = activity({"github": Sample(data={"total": 1234}, collected_at=STAMP)}, NOW, False)
    assert "1,234" in card.title


@pytest.fixture
def renderer_workspace(tmp_path, monkeypatch):
    import render

    root = Path(__file__).parent
    for name in ("config.json", "README.template.md"):
        (tmp_path / name).write_text((root / name).read_text())
    (tmp_path / "fonts").symlink_to(root / "fonts", target_is_directory=True)
    (tmp_path / "cards").mkdir()
    (tmp_path / "README.md").write_text("previous profile")
    monkeypatch.setattr(render, "ROOT", tmp_path)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    return tmp_path


def test_total_outage_preserves_published_files(renderer_workspace, monkeypatch):
    import render

    def offline(*args):
        raise OSError("offline")

    monkeypatch.setattr(render, "request_json", offline)
    assert render.main() == 1
    assert (renderer_workspace / "README.md").read_text() == "previous profile"
    assert not list((renderer_workspace / "cards").iterdir())


def test_partial_outage_publishes_healthy_data_and_dated_retained_data(renderer_workspace, monkeypatch):
    import render

    previous = {"github": Sample(data={"total": 7, "repos": {}, "weeks": []}, collected_at=STAMP).model_dump()}
    (renderer_workspace / "cards/data.json").write_text(json.dumps(previous))

    def lab_only(url, *args):
        if url.endswith("/lab"):
            return {"pods": 42, "updatedAt": STAMP}
        raise OSError("offline")

    monkeypatch.setattr(render, "request_json", lab_only)
    assert render.main() == 0
    snapshot = json.loads((renderer_workspace / "cards/data.json").read_text())
    assert snapshot["github"]["stale"]
    assert snapshot["github"]["collected_at"] == STAMP
    assert snapshot["lab"]["data"]["pods"] == 42
    assert len(list((renderer_workspace / "cards").glob("*.svg"))) == 28


def test_template_failure_does_not_publish_partial_output(renderer_workspace, monkeypatch):
    import render

    (renderer_workspace / "README.template.md").write_text("{{misspelled-token}}")
    monkeypatch.setattr(render, "request_json", lambda *args: {"pods": 42, "updatedAt": STAMP})
    with pytest.raises(ValueError, match="unresolved"):
        render.main()
    assert (renderer_workspace / "README.md").read_text() == "previous profile"
    assert not list((renderer_workspace / "cards").iterdir())
