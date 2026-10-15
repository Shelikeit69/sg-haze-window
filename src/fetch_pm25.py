"""Download NEA hourly PM2.5 (5 regions) from data.gov.sg v2, one raw JSON per day.

Usage: python src/fetch_pm25.py 2026-09-01 2026-10-15
Raw files are kept as downloaded: data/raw/pm25/YYYY-MM-DD.json
A file is skipped only when its day is over AND it already holds all 24 hours.
Today, and any past day saved before it was complete (for example by the 05:50 daily
run), is downloaded again so later hours are filled in and predictions can be scored.
Days the source itself never completes are re-requested only when they fall inside
the requested range, and the result is whatever the source returns.

v2 is used because the v1 endpoint (?date=) omits the 00:00 reading of each day;
v1 downloads are kept in archive/raw_pm25_v1 for reference.
"""
import json
import sys
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

URL = "https://api-open.data.gov.sg/v2/real-time/api/pm25?date={d}"
OUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "pm25"


HEADERS = {"User-Agent": "sg-haze-window/0.1 (+https://github.com/Shelikeit69/sg-haze-window)"}


def fetch(d: date) -> dict:
    req = urllib.request.Request(URL.format(d=d.isoformat()), headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def complete(path: Path) -> bool:
    try:
        items = json.loads(path.read_text()).get("data", {}).get("items", [])
    except (ValueError, AttributeError):
        return False
    return len({it.get("timestamp") for it in items}) >= 24


def main(start: str, end: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d, last = date.fromisoformat(start), date.fromisoformat(end)
    while d <= last:
        path = OUT / f"{d.isoformat()}.json"
        if path.exists() and d < date.today() and complete(path):
            d += timedelta(days=1)
            continue
        for attempt in range(3):
            try:
                data = fetch(d)
                break
            except Exception as e:  # network hiccup: retry, then report
                if attempt == 2:
                    print(f"{d} FAILED: {e}")
                    data = None
                time.sleep(2)
        if data is not None:
            path.write_text(json.dumps(data, ensure_ascii=False))
            items = data.get("data", {}).get("items", [])
            more = data.get("data", {}).get("paginationToken")
            print(f"{d} items={len(items)} code={data.get('code')}" + (" PAGINATED-NOT-FETCHED" if more else ""))
        d += timedelta(days=1)
        time.sleep(0.5)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
