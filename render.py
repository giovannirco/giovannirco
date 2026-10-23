"""Render the profile cards in cards/ from GitHub and the homelab's public API.

Run: python render.py   (GITHUB_TOKEN in the environment)
A source that fails keeps the card it rendered last time.
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
    "dark": {"bg": "#14130f", "plate": "#1c1a15", "line": "#3a3529", "ink": "#ece6d8",
             "muted": "#a49d8d", "accent": "#e8a33d", "off": "#3b3629", "glow": "0.55"},
    "light": {"bg": "#f6f2e8", "plate": "#ece6d8", "line": "#d6cebd", "ink": "#1d1b16",
              "muted": "#6a6355", "accent": "#a9690f", "off": "#d6cebd", "glow": "0"},
}


def get_json(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "giovannirco-profile", **(headers or {})})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def lab(path):
    return get_json(f"{LAB}/api/insight/{path}")


def github(query, variables):
    token = os.environ["GITHUB_TOKEN"]
    body = json.dumps({"query": query, "variables": variables}).encode()
    out = get_json("https://api.github.com/graphql", body, {"Authorization": f"bearer {token}"})
    if out.get("errors"):
        raise RuntimeError(out["errors"])
    return out["data"]


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
        s.raw(f'<circle cx="{x}" cy="44" r="5" class="{cls} {"c-accent" if on else "c-off"}" '
              f'style="animation-delay:{i * 0.18:.2f}s"/>')
    s.t(40 + len(leds[:CONFIG["clusters"]]) * 22 + 6, 49, f"{sum(leds)}/{CONFIG['clusters']} clusters up",
        12, "mono", 400, "muted")
    s.t(38, 104, CONFIG["name"], 40, "sans", 600, "ink", extra=' letter-spacing="-1"')
    s.t(40, 136, CONFIG["role"], 18, "sans", 400, "muted")
    s.raw('<line x1="40" y1="152" x2="800" y2="152" class="s-accent" stroke-width="1" opacity="0.6"/>')
    css = (".led.on{filter:drop-shadow(0 0 4px rgba(232,163,61,GLOW));animation:boot 2.4s steps(1,end) 1 both}"
           "@keyframes boot{0%{opacity:.15}20%{opacity:1}30%{opacity:.3}45%{opacity:1}55%{opacity:.4}70%,100%{opacity:1}}"
           "@media (prefers-reduced-motion:reduce){.led{animation:none}}")
    write("header", s, css)


# rack ledger: the homelab, live

def ledger():
    labd, prox, store, net, unifi, gpu = (lab(p) for p in ("lab", "proxmox", "storage", "network", "unifi", "gpu"))
    hosts = [h for h in prox["hosts"] if h.get("reporting")]
    gpus = [g for g in gpu["gpus"] if g.get("reporting")]
    vram = sum(g["memoryTotal"] for g in gpus) / 2**30
    rows = [
        ("Kubernetes", f"{labd['clusters']} clusters · {labd['nodes']} nodes · {human(labd['pods'])} pods",
         "Talos, managed through Omni, GitOps with Flux and Argo CD"),
        ("Compute", f"{len(hosts)} Proxmox hosts · {sum(h['cores'] for h in hosts)} cores · {store['guests']} guests",
         f"backups {store['backupPassed']}/{store['backupRuns']} passed, disks {store['disksPassing']}/{store['disks']} healthy"),
        ("Network policy", f"{net['enforcedEndpoints']}/{net['endpoints']} endpoints enforced",
         f"Cilium, default deny in every namespace, {human(round(net['flowsPerSecond']))} flows/s"),
        ("Network", f"{unifi['online']}/{unifi['devices']} UniFi devices online",
         "VLANs per cluster, BGP to the gateway, Cloudflare tunnel at the edge"),
        ("GPU", f"{len(gpus)} × RTX 3090 · {vram:.0f} GB VRAM",
         "local image, LLM and music models"),
    ]
    s = Svg(840, 64 + len(rows) * 46 + 18, "Homelab, live")
    s.t(40, 40, "Homelab, live", 15, "sans", 500, "ink")
    s.t(800, 40, f"sampled {stamp()}", 12, "mono", 400, "muted", "end")
    y = 58
    s.raw(f'<line x1="40" y1="{y}" x2="800" y2="{y}" class="s-line"/>')
    for k, v, sub in rows:
        s.t(40, y + 27, k, 13, "sans", 400, "muted")
        s.t(200, y + 21, v, 14, "mono", 500, "ink")
        s.t(200, y + 38, sub, 12, "sans", 400, "muted")
        y += 46
        s.raw(f'<line x1="40" y1="{y}" x2="800" y2="{y}" class="s-line"/>')
    write("homelab", s)


# github: repositories by stars, a year of contributions

Q = """query($login:String!){user(login:$login){
  repositories(first:100, ownerAffiliations:OWNER, privacy:PUBLIC, isFork:false, orderBy:{field:STARGAZERS,direction:DESC}){
    totalCount nodes{name stargazerCount pushedAt primaryLanguage{name}}}
  contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount}}}}
}}"""


def repos():
    u = github(Q, {"login": CONFIG["login"]})["user"]
    nodes = u["repositories"]["nodes"]
    stars = sum(r["stargazerCount"] for r in nodes)
    top = [r for r in nodes if r["name"] in CONFIG["featured"]]
    order = list(CONFIG["featured"])
    top.sort(key=lambda r: order.index(r["name"]))
    cal = u["contributionsCollection"]["contributionCalendar"]
    weeks = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in cal["weeks"]]

    s = Svg(840, 74 + len(top) * 30 + 128, "Public work on GitHub")
    s.t(40, 40, "Public work", 15, "sans", 500, "ink")
    s.t(800, 40, f"{u['repositories']['totalCount']} repositories · {stars} stars", 12, "mono", 400, "muted", "end")
    y = 58
    s.raw(f'<line x1="40" y1="{y}" x2="800" y2="{y}" class="s-line"/>')
    for r in top:
        lang = (r["primaryLanguage"] or {}).get("name", "")
        s.t(40, y + 20, r["name"], 14, "mono", 500, "ink")
        s.t(258, y + 20, CONFIG["featured"][r["name"]], 13, "sans", 400, "muted")
        if r["stargazerCount"]:
            s.t(612, y + 20, f"★ {r['stargazerCount']}", 12, "mono", 400, "accent", "end")
        s.t(712, y + 20, lang, 12, "mono", 400, "muted", "end")
        pushed = dt.datetime.fromisoformat(r["pushedAt"].replace("Z", "+00:00")).strftime("%b %Y")
        s.t(800, y + 20, pushed, 12, "mono", 400, "muted", "end")
        y += 30
        s.raw(f'<line x1="40" y1="{y}" x2="800" y2="{y}" class="s-line"/>')
    y += 30
    s.t(40, y, f"{human(cal['totalContributions'])} contributions in the last year", 13, "sans", 400, "muted")
    top_w = max(weeks) or 1
    bw = 760 / len(weeks)
    base = y + 72
    for i, n in enumerate(weeks):
        h = max(2, round(58 * n / top_w)) if n else 2
        cls = "c-accent" if n else "c-off"
        s.raw(f'<rect x="{40 + i * bw:.1f}" y="{base - h}" width="{bw - 3:.1f}" height="{h}" class="{cls}"/>')
    write("github", s)


def main():
    CARDS.mkdir(exist_ok=True)
    failed = []
    for job in (header, ledger, repos):
        try:
            job()
        except Exception as e:  # keep the previous card
            failed.append(f"{job.__name__}: {e}")
    for f in failed:
        print(f, file=sys.stderr)
    if len(failed) == 3:
        sys.exit(1)


if __name__ == "__main__":
    main()
