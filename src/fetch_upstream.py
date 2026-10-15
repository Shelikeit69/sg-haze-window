"""Download upstream signals (raw files, never edited).

1. NASA FIRMS VIIRS fire detections over Sumatra + Kalimantan + Peninsular Malaysia
   (area 95E-120E, 6S-6N), both VIIRS satellites, 5-day chunks.
2. OpenAQ hourly PM2.5 for upstream low-cost sensors (AirGradient / Clarity):
   Palembang (South Sumatra), Malacca, Johor (Eco Botanic).

Keys are read from the environment (FIRMS_MAP_KEY, OPENAQ_API_KEY) and never written
to the repository. Store them in a file outside the repo and export before running:
    set -a; . ~/.config/sg-haze/env; set +a
Usage: python src/fetch_upstream.py 2026-09-01 2026-10-15
"""
import json
import os
import sys
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "upstream"
UA = {"User-Agent": "sg-haze-window/0.1 (+https://github.com/Shelikeit69/sg-haze-window)"}
AREA = "95,-6,120,6"
# Standard-processing (SP) archive covers up to SP_END; later dates only exist as near-real-time (NRT).
# SP and NRT use slightly different processing; this is stated in the data statement.
SP_END = date(2026, 6, 30)


def firms_sources(d: date):
    kind = "SP" if d <= SP_END else "NRT"
    return [f"VIIRS_SNPP_{kind}", f"VIIRS_NOAA20_{kind}"]
SENSORS = {  # OpenAQ sensor id -> label (location id in comment)
    15992900: "palembang",   # 6313205 SD Muhammadiyah 6/14 Palembang
    13534513: "malacca",     # 4545510 Malacca - Masjid Tengkera
    17739683: "johor_ecobotanic",  # 6551253 Eco Botanic
}


def get(url, headers=None, tries=4):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read().decode()
        except Exception as e:
            if i == tries - 1:
                raise
            print(f"  retry after {e}")
            time.sleep(5 * (i + 1))


def firms(start: date, end: date):
    key = os.environ["FIRMS_MAP_KEY"]
    d = start
    while d <= end:
        n = min(5, (end - d).days + 1)
        if d <= SP_END < d + timedelta(days=n - 1):
            n = (SP_END - d).days + 1  # do not let a chunk straddle the SP/NRT boundary
        for src in firms_sources(d):
            path = OUT / "firms" / f"{src}_{d.isoformat()}_{n}d.csv"
            if path.exists():
                continue
            txt = get(f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/{src}/{AREA}/{n}/{d.isoformat()}")
            if not txt.startswith("latitude"):
                raise RuntimeError(f"FIRMS unexpected response for {src} {d}: {txt[:200]}")
            path.write_text(txt)
            print(f"firms {src} {d} +{n}d rows={txt.count(chr(10)) - 1}")
        d += timedelta(days=n)


def openaq(start: date, end: date):
    key = os.environ["OPENAQ_API_KEY"]
    for sid, label in SENSORS.items():
        path = OUT / "openaq" / f"{label}_{sid}_{start}_{end}.json"
        if path.exists():
            continue
        results, page = [], 1
        while True:
            url = (f"https://api.openaq.org/v3/sensors/{sid}/hours?datetime_from={start}T00:00:00"
                   f"&datetime_to={end + timedelta(days=1)}T00:00:00&limit=1000&page={page}")
            d = json.loads(get(url, {"X-API-Key": key}))
            results += d["results"]
            if len(d["results"]) < 1000:
                break
            page += 1
            time.sleep(1)
        path.write_text(json.dumps({"sensor_id": sid, "label": label, "results": results}))
        print(f"openaq {label} hours={len(results)}")


if __name__ == "__main__":
    s, e = date.fromisoformat(sys.argv[1]), date.fromisoformat(sys.argv[2])
    (OUT / "firms").mkdir(parents=True, exist_ok=True)
    (OUT / "openaq").mkdir(parents=True, exist_ok=True)
    firms(s, e)
    if "--firms-only" not in sys.argv:
        openaq(s, e)
