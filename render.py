"""Render the header card in cards/ (one LED per cluster, lit from the homelab's public API).

Run: python render.py
The other cards are Peephole frames: see frames.py and .github/workflows/cards.yml.
"""

import base64
import datetime as dt
import io
import json
import os
import pathlib
import sys
import urllib.request
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = pathlib.Path(__file__).parent
CARDS = ROOT / "cards"
CONFIG = json.loads((ROOT / "config.json").read_text())
LAB = CONFIG["lab_api"].rstrip("/")

THEMES = {
    "dark": {"bg": "#0b0e14", "plate": "#151a23", "line": "#232a36", "ink": "#e6e9ef",
             "muted": "#8a93a5", "accent": "#4ea1ff", "led": "#3ddc84", "off": "#2a3140", "glow": "0.6"},
    "light": {"bg": "#f4f6fa", "plate": "#e8ecf3", "line": "#d3d9e4", "ink": "#0b0e14",
              "muted": "#5b6577", "accent": "#2f7fe0", "led": "#1fa864", "off": "#c9d0dc", "glow": "0"},
}


def get_json(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "giovannirco-profile", **(headers or {})})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def lab(path):
    return get_json(f"{LAB}/api/insight/{path}")


# fonts: subset IBM Plex to the glyphs each card uses, embed as base64 woff2

FONTS = {("sans", 400): "plex-sans-400", ("sans", 500): "plex-sans-500", ("sans", 600): "plex-sans-600",
         ("mono", 400): "plex-mono-400", ("mono", 500): "plex-mono-500"}


def font_faces(text, used):
    chars = "".join(sorted(set(text + " .,:/·×%-+0123456789")))
    rules = []
    for family, weight in sorted(used):
        font = TTFont(ROOT / "fonts" / f"{FONTS[(family, weight)]}.woff2")
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "liga", "tnum"]
        sub = subset.Subsetter(opts)
        sub.populate(text=chars)
        sub.subset(font)
        buf = io.BytesIO()
        font.flavor = "woff2"
        font.save(buf)
        data = base64.b64encode(buf.getvalue()).decode()
        name = "P" + family.capitalize()
        rules.append(f"@font-face{{font-family:{name};font-weight:{weight};"
                     f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    return "".join(rules)


class Svg:
    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.parts, self.text, self.used = [], "", set()

    def t(self, x, y, s, size=14, family="sans", weight=400, fill="ink", anchor="start", extra=""):
        self.text += s
        self.used.add((family, weight))
        self.parts.append(f'<text x="{x}" y="{y}" class="{family} c-{fill}" font-size="{size}" '
                          f'font-weight="{weight}" text-anchor="{anchor}"{extra}>{escape(s)}</text>')

    def raw(self, s):
        self.parts.append(s)

    def render(self, theme, css=""):
        c = THEMES[theme]
        colors = "".join(f".c-{k}{{fill:{v}}}" for k, v in c.items() if k != "glow")
        style = (font_faces(self.text, self.used) +
                 ".sans{font-family:PSans,system-ui,sans-serif}.mono{font-family:PMono,ui-monospace,monospace;"
                 "font-variant-numeric:tabular-nums}" + colors +
                 f".s-line{{stroke:{c['line']}}}.s-accent{{stroke:{c['accent']}}}" + css.replace("GLOW", c["glow"]))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{escape(self.title)}">'
                f"<title>{escape(self.title)}</title><style>{style}</style>"
                f'<rect width="{self.w}" height="{self.h}" rx="6" fill="{c["bg"]}"/>'
                + "".join(self.parts) + "</svg>")


def write(name, svg, css=""):
    for theme in THEMES:
        (CARDS / f"{name}-{theme}.svg").write_text(svg.render(theme, css))


def stamp():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def human(n):
    return f"{n:,}"


# header: name, role, one LED per cluster (lit when its nodes are ready)

def header():
    nodes = lab("nodes")
    ready = {}
    for n in nodes["nodes"]:
        ready[n["cluster"]] = ready.get(n["cluster"], False) or n["ready"]
    leds = [ready.get(c["id"], False) for c in nodes["clusters"]]
    leds += [False] * (CONFIG["clusters"] - len(leds))

    s = Svg(840, 168, f"{CONFIG['name']}, {CONFIG['role']}")
    for i, on in enumerate(leds[:CONFIG["clusters"]]):
        x = 40 + i * 22
        cls = "led on" if on else "led"
        s.raw(f'<circle cx="{x}" cy="44" r="5" class="{cls} {"c-led" if on else "c-off"}" '
              f'style="animation-delay:{i * 0.18:.2f}s"/>')
    s.t(40 + len(leds[:CONFIG["clusters"]]) * 22 + 6, 49, f"{sum(leds)}/{CONFIG['clusters']} clusters up",
        12, "mono", 400, "muted")
    s.t(38, 104, CONFIG["name"], 40, "sans", 600, "ink", extra=' letter-spacing="-1"')
    s.t(40, 136, CONFIG["role"], 18, "sans", 400, "muted")
    s.raw('<line x1="40" y1="152" x2="800" y2="152" class="s-accent" stroke-width="1" opacity="0.6"/>')
    css = (".led.on{filter:drop-shadow(0 0 4px rgba(61,220,132,GLOW));animation:boot 2.4s steps(1,end) 1 both}"
           "@keyframes boot{0%{opacity:.15}20%{opacity:1}30%{opacity:.3}45%{opacity:1}55%{opacity:.4}70%,100%{opacity:1}}"
           "@media (prefers-reduced-motion:reduce){.led{animation:none}}")
    write("header", s, css)


def main():
    CARDS.mkdir(exist_ok=True)
    failed = []
    for job in (header,):
        try:
            job()
        except Exception as e:  # keep the previous card
            failed.append(f"{job.__name__}: {e}")
    for f in failed:
        print(f, file=sys.stderr)
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
