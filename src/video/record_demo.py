"""Record the website part of the demo video (segment 04) with a headless browser.

Opens the public demo, lets live NEA and CAMS data load, then follows the narration:
pick a region, show the current reading and band, scroll to the chart with the
suggested hour and error band, scroll back to the "check the live reading" note.
Output: a 1920x1080 WebM in the folder given as the first argument.

Fonts: Google Fonts may be unreachable, so install Barlow Condensed, Public Sans and
JetBrains Mono locally first (the page names them, and Chromium uses local copies).
"""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "video_out")
# Same files as the public demo. Pass a local server URL if github.io is not reachable:
#   python -m http.server 8765 --directory web   ->   http://127.0.0.1:8765/
URL = sys.argv[2] if len(sys.argv) > 2 else "https://shelikeit69.github.io/sg-haze-window/web/"
ZOOM = 1.6  # the page is a 960 px column; enlarge it to fill a 1080p frame


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080},
                                  record_video_dir=str(OUT), record_video_size={"width": 1920, "height": 1080},
                                  color_scheme="light")
        page = ctx.new_page()
        t0 = time.monotonic()  # video starts about when the page is created
        page.route("https://fonts.googleapis.com/**", lambda r: r.abort())
        page.route("https://fonts.gstatic.com/**", lambda r: r.abort())
        page.goto(URL, wait_until="networkidle")
        # "Live." = live data loaded; "Live data did not load" = snapshot fallback (must not pass)
        page.wait_for_function("/^(Live\\.|Live data did not load)/.test(document.getElementById('status-text').textContent)", timeout=60000)
        if not page.inner_text("#status-text").startswith("Live."):
            raise SystemExit("Live data did not load; not recording a snapshot. Try again.")
        page.evaluate(f"document.body.style.zoom = '{ZOOM}'")
        page.evaluate("window.scrollTo(0, 0)")
        status = page.inner_text("#status-text")
        time.sleep(0.5)
        ready_at = time.monotonic() - t0  # everything before this is the loading screen
        time.sleep(1.5)

        page.click("#region-west"); time.sleep(1.8)     # 选一个区
        page.click("#region-east"); time.sleep(2.5)     # 当前读数和 NEA 等级
        chart_y = page.evaluate("document.getElementById('chart').getBoundingClientRect().top + window.scrollY")
        for i in range(1, 21):                          # 过去 12 小时与未来 24 小时
            page.evaluate(f"window.scrollTo(0, {chart_y * i / 20 - 120})"); time.sleep(0.04)
        time.sleep(7.0)                                 # 圆圈与阴影
        for i in range(20, -1, -1):                     # 回到提醒再看实时读数
            page.evaluate(f"window.scrollTo(0, {chart_y * i / 20})"); time.sleep(0.04)
        time.sleep(5.0)
        video_path = page.video.path()
        ctx.close()
        browser.close()
    raw = OUT / "04_website_raw.webm"
    Path(video_path).rename(raw)
    (OUT / "04_website_start.txt").write_text(f"{ready_at:.2f}\n")
    print("status line:", status)
    print(f"written {raw}; usable footage starts at {ready_at:.2f} s")


if __name__ == "__main__":
    main()
