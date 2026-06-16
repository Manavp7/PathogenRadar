"""Capture dashboard screenshots with Playwright (headless Chromium + software WebGL).

Used for visual verification / PR evidence. Not part of the app runtime.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/shots")
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://localhost:5173"

VIEWS = ["Overview", "Kerala", "District", "Executive"]

LAUNCH_ARGS = [
    "--no-sandbox",
    "--enable-unsafe-swiftshader",
    "--use-gl=angle",
    "--use-angle=swiftshader",
    "--ignore-gpu-blocklist",
]


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=LAUNCH_ARGS)
        page = browser.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=2)
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_timeout(2500)  # let map + charts settle

        for view in VIEWS:
            try:
                page.click(f"nav button:has-text('{view}')")
            except Exception as exc:  # noqa: BLE001
                print(f"nav {view} failed: {exc}")
            page.wait_for_timeout(3000)
            path = OUT / f"{view.lower()}.png"
            page.screenshot(path=str(path), full_page=True)
            print(f"saved {path}")

        browser.close()


if __name__ == "__main__":
    t = time.time()
    main()
    print(f"done in {time.time() - t:.1f}s")
