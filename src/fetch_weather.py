"""Download hourly weather (Open-Meteo archive) and CAMS PM2.5 (Open-Meteo air quality)
for the 5 NEA region label points. Raw JSON per source per region.

Usage: python src/fetch_weather.py 2026-09-01 2026-10-17

Caveats recorded with the data (see data/raw/weather/README.txt):
- The archive endpoint returns values up to the end of the requested range, including
  hours that have not happened yet. Those recent/future values come from forecast models,
  not reanalysis. Downstream code must not use weather values later than the forecast
  issue time as model inputs.
- CAMS PM2.5 here is a model value, used only as a comparison input, never as ground truth.
"""
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "weather"
HEADERS = {"User-Agent": "sg-haze-window/0.1 (+https://github.com/Shelikeit69/sg-haze-window)"}

# Same label points NEA publishes in regionMetadata
REGIONS = {
    "central": (1.35735, 103.82),
    "east": (1.35735, 103.94),
    "north": (1.41803, 103.82),
    "south": (1.29587, 103.82),
    "west": (1.35735, 103.70),
}

WEATHER = ("https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}"
           "&start_date={s}&end_date={e}&timezone=Asia%2FSingapore"
           "&hourly=wind_speed_10m,wind_direction_10m,precipitation,relative_humidity_2m,boundary_layer_height")
CAMS = ("https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}"
        "&start_date={s}&end_date={e}&timezone=Asia%2FSingapore&hourly=pm2_5")


def get(url: str, tries: int = 4) -> dict:
    req = urllib.request.Request(url, headers=HEADERS)
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except Exception as e:
            # 4xx other than 429 is a bad request: retrying will not help, fail with the reason.
            code = getattr(e, "code", None)
            if i == tries - 1 or (code is not None and 400 <= code < 500 and code != 429):
                if hasattr(e, "read"):
                    print(f"  {code} {e.read()[:200]!r}")
                raise
            wait = 30 * (i + 1) if code == 429 else 3 * (i + 1)  # Open-Meteo rate limit: back off
            print(f"  retry in {wait}s after {e}")
            time.sleep(wait)


def main(s: str, e: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    pulled = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for name, (lat, lon) in REGIONS.items():
        for src, tmpl in (("weather", WEATHER), ("cams", CAMS)):
            # The archive endpoint rejects end dates after today's UTC date (HTTP 400), even
            # with timezone=Asia/Singapore. Between 00:00 and 08:00 SGT the Singapore date is
            # one day ahead of UTC, so the cap must use the UTC date. Hours after the cap are
            # left missing and flagged downstream (wx_missing_at_issue), never filled.
            end = min(e, datetime.now(timezone.utc).date().isoformat()) if src == "weather" else e
            path = OUT / f"{src}_{name}_{s}_{end}.json"
            # Skip only ranges that are fully in the past. A range reaching today or later
            # (always true for CAMS) is downloaded again, otherwise the 22:15 run would reuse
            # the CAMS forecast saved by the 05:50 run on the same day (same file name).
            if path.exists() and end < datetime.now().date().isoformat():
                print(f"{src:7s} {name:7s} exists, skipped")
                continue
            data = get(tmpl.format(lat=lat, lon=lon, s=s, e=end))
            data["_pulled_at_utc"] = pulled
            path.write_text(json.dumps(data))
            h = data.get("hourly", {})
            print(f"{src:7s} {name:7s} hours={len(h.get('time', []))} keys={[k for k in h if k != 'time']}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
