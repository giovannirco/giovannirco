import datetime as dt
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from streak import adapt_streak, publish_streak, streak_alt

ROOT = Path(__file__).parent
NS = "{http://www.w3.org/2000/svg}"
NOW = dt.datetime(2026, 10, 26, 15, tzinfo=dt.timezone.utc)


@pytest.fixture
def upstream():
    return (ROOT / "fixtures/streak-upstream.svg").read_text()


@pytest.mark.parametrize("mobile,width", [(False, 840), (True, 336)])
def test_streak_preserves_statistics_dates_and_icon_with_both_themes(upstream, mobile, width):
    svg = adapt_streak(upstream, NOW, mobile)
    root = ET.fromstring(svg)
    assert root.attrib["width"] == str(width)
    assert int(root.attrib["height"]) <= 420
    title = root.attrib["aria-label"]
    assert "12,345 total contributions" in title
    assert "current daily streak" in title and "longest daily streak" in title
    assert "2017-12-15 - Present" in title
    assert "2026-10-26 15:00 UTC" in title
    assert root.find(f".//{NS}circle") is not None
    assert len(root.findall(f".//{NS}path")) >= 2
    assert "@media(prefers-color-scheme:dark)" in svg
    assert "#f6f2e8" in svg and "#14130f" in svg
    assert "data:font/woff2;base64," in svg
    assert "animation:" not in svg


def test_streak_mobile_reflows_panels_without_scaling_type(upstream):
    root = ET.fromstring(adapt_streak(upstream, NOW, True))
    assert "scale(" not in ET.tostring(root, encoding="unicode")
    labels = [" ".join(text.itertext()).strip() for text in root.findall(f".//{NS}text")]
    assert any("Total" in text and "Contributions" in text for text in labels)
    dates = root.findall(f".//{NS}text/{NS}tspan")
    assert any(span.text == "- Present" for span in dates)
    for text in root.findall(f".//{NS}text"):
        assert float(text.attrib["font-size"].removesuffix("px")) >= 12


@pytest.mark.parametrize(
    "payload",
    [
        "<html>upstream down</html>",
        '<svg xmlns="http://www.w3.org/2000/svg"><text>API rate limited</text></svg>',
        '<!DOCTYPE svg [<!ENTITY data "12">]><svg xmlns="http://www.w3.org/2000/svg"/>',
    ],
)
def test_invalid_streak_output_fails_before_replacing_cards(tmp_path, payload):
    source = tmp_path / "upstream.svg"
    source.write_text(payload)
    output = tmp_path / "cards"
    output.mkdir()
    (output / "streak.svg").write_text("previous desktop")
    (output / "streak-mobile.svg").write_text("previous mobile")
    with pytest.raises(ValueError):
        publish_streak(source, output, NOW)
    assert (output / "streak.svg").read_text() == "previous desktop"
    assert (output / "streak-mobile.svg").read_text() == "previous mobile"


@pytest.mark.parametrize(
    "injection",
    [
        "<script>alert(1)</script>",
        '<image href="https://example.com/track.png"/>',
        '<g onload="alert(1)"/>',
        '<g xml:base="https://example.com/"/>',
        '<g style="fill:url(https://example.com/track.svg)"/>',
    ],
)
def test_unsafe_upstream_svg_is_rejected(upstream, injection):
    with pytest.raises(ValueError):
        adapt_streak(upstream.replace("</svg>", injection + "</svg>"), NOW, False)


def test_unexpected_upstream_statistic_is_rejected(upstream):
    with pytest.raises(ValueError, match="statistic"):
        adapt_streak(upstream.replace("12,345", "unavailable"), NOW, False)


def test_streak_publication_provides_accessible_summary(upstream, tmp_path):
    source = tmp_path / "upstream.svg"
    source.write_text(upstream)
    publish_streak(source, tmp_path / "cards", NOW)
    alt = streak_alt(tmp_path / "cards/streak.svg")
    assert "12,345 total contributions" in alt
    assert "current daily streak" in alt
    assert "2026-10-26 15:00 UTC" in alt


def test_partial_history_error_log_prevents_publication(upstream, tmp_path):
    source = tmp_path / "upstream.svg"
    source.write_text(upstream)
    log = tmp_path / "php-errors.log"
    log.write_text("Failed to decode response for giovannirco's 2020 contributions after 2 attempts")
    with pytest.raises(ValueError, match="incomplete history"):
        publish_streak(source, tmp_path / "cards", NOW, log)
    assert not (tmp_path / "cards").exists()


def test_streak_workflow_pins_generator_and_publishes_only_after_success():
    workflow = (ROOT / ".github/workflows/cards.yml").read_text()
    assert "DenverCoder1/github-readme-streak-stats@adbd07609bb771d3510a15ee2f3b31d5fbe5201d" in workflow
    assert "disable_animations=true" in workflow
    assert "timezone=UTC" in workflow
    assert "continue-on-error" not in workflow
    assert workflow.index("python streak.py") < workflow.index("python render.py")
    assert "streak-stats.demolab.com" not in workflow
    assert "17 */6 * * *" in workflow
    assert "always() && github.event_name == 'schedule'" in workflow
