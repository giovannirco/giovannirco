"""Fetch the profile frames from a running Peephole hub and write cards/<page>.png plus cards/screen.gif.

Run: python frames.py http://127.0.0.1:8080   (after the hub polled every plugin)
"""

import io
import json
import pathlib
import sys
import time
import urllib.request

from PIL import Image

ROOT = pathlib.Path(__file__).parent
CARDS = ROOT / "cards"
SCALE = 3
SIZE = (320 * SCALE, 170 * SCALE)
PAGES = ["homelab", "nodes", "network", "gpu", "storage", "work"]
GIF_PAGES = ["homelab", "nodes", "network", "gpu", "work"]


def get(url, timeout=20):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "giovannirco-profile"}), timeout=timeout) as r:
        return r.read()


def wait_for_plugins(hub, deadline_s=120):
    end = time.time() + deadline_s
    while True:
        plugins = json.loads(get(f"{hub}/api/plugins"))
        pending = [p["name"] for p in plugins if p["polled_at"] is None]
        failing = [f"{p['name']}: {p.get('error')}" for p in plugins if p["polled_at"] is not None and not p["ok"]]
        if not pending:
            return failing
        if time.time() > end:
            raise SystemExit(f"plugins never polled: {pending}")
        time.sleep(2)


def main():
    hub = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8080"
    failing = wait_for_plugins(hub)
    for f in failing:
        print(f"warning: {f}", file=sys.stderr)
    CARDS.mkdir(exist_ok=True)
    frames = {}
    for page in PAGES:
        png = get(f"{hub}/pages/{page}.png?w={SIZE[0]}&h={SIZE[1]}")
        (CARDS / f"{page}.png").write_bytes(png)
        frames[page] = Image.open(io.BytesIO(png)).convert("RGB")
    gif = [frames[p].quantize(colors=128, method=Image.Quantize.MEDIANCUT) for p in GIF_PAGES]
    gif[0].save(CARDS / "screen.gif", save_all=True, append_images=gif[1:], duration=4000, loop=0, optimize=True)
    print(f"{len(frames)} frames, gif {(CARDS / 'screen.gif').stat().st_size // 1024} KB")
    if len(failing) == len(json.loads(get(f"{hub}/api/plugins"))):
        sys.exit(1)


if __name__ == "__main__":
    main()
