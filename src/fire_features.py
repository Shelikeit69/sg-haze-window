"""Aggregate NASA FIRMS VIIRS detections into hourly upstream fire features (SGT).

- Only nominal and high confidence detections are used.
- A detection is treated as available AVAILABILITY_LAG hours after acquisition
  (FIRMS near-real-time latency), so features never use data that was not yet published.
- For every hour t: number of detections and summed fire radiative power (FRP, MW)
  that became available in (t-24h, t] and in (t-48h, t-24h], per source region.
- Hours after the last published overpass are left missing, not set to zero.

Output: data/processed/fire_hourly.csv
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "upstream" / "firms"
OUT = ROOT / "data" / "processed" / "fire_hourly.csv"
AVAILABILITY_LAG = 3  # hours

# (lon_min, lon_max, lat_min, lat_max)
REGIONS = {
    "ssum": (102.0, 106.0, -5.0, -1.5),   # South Sumatra / Jambi south
    "riau": (100.0, 104.5, -1.5, 2.5),    # Riau / Jambi north
    "kal": (108.0, 117.0, -4.5, 2.0),     # West / Central Kalimantan
}


def load() -> pd.DataFrame:
    df = pd.concat(pd.read_csv(f) for f in sorted(RAW.glob("*.csv")))
    # daily live refreshes download overlapping chunks: count each detection once
    df = df.drop_duplicates(subset=["latitude", "longitude", "acq_date", "acq_time", "satellite"])
    df = df[df.confidence.isin(["n", "h"])].copy()
    t = pd.to_datetime(df.acq_date + " " + df.acq_time.astype(str).str.zfill(4), format="%Y-%m-%d %H%M", utc=True)
    df["available_sgt"] = (t + pd.Timedelta(hours=AVAILABILITY_LAG)).dt.tz_convert("Asia/Singapore").dt.tz_localize(None).dt.ceil("h")
    df["region"] = None
    for name, (x0, x1, y0, y1) in REGIONS.items():
        m = df.longitude.between(x0, x1) & df.latitude.between(y0, y1)
        df.loc[m, "region"] = name
    return df.dropna(subset=["region"])


def covered_days() -> set:
    """Days for which FIRMS files were downloaded (from file names: SOURCE_YYYY-MM-DD_Nd.csv)."""
    days = set()
    for f in RAW.glob("*.csv"):
        start, n = f.stem.split("_")[-2], int(f.stem.split("_")[-1].rstrip("d"))
        days.update(pd.date_range(start, periods=n).date)
    return days


def build() -> pd.DataFrame:
    df = load()
    last_available = df.available_sgt.max()
    idx = pd.date_range("2023-08-01 00:00", pd.Timestamp.now(tz="Asia/Singapore").tz_localize(None).floor("h"), freq="h")
    out = pd.DataFrame(index=idx)
    for name in REGIONS:
        g = df[df.region == name].groupby("available_sgt").agg(n=("frp", "size"), frp=("frp", "sum"))
        g = g.reindex(idx, fill_value=0)
        for col in ("n", "frp"):
            roll24 = g[col].rolling(24, min_periods=24).sum()
            out[f"fire_{name}_{col}_24h"] = roll24
            out[f"fire_{name}_{col}_24_48h"] = roll24.shift(24)
    # hours later than the last published overpass + 13 h (next overpass not yet in) are unknown
    out.loc[out.index > last_available + pd.Timedelta(hours=13)] = float("nan")
    # outside downloaded periods we know nothing: a 48 h window must lie fully inside coverage
    cov = pd.Series(pd.Index(out.index.date).isin(list(covered_days())), index=out.index)
    ok = cov.rolling(48 + AVAILABILITY_LAG + 24, min_periods=1).min().astype(bool)
    out.loc[~ok] = float("nan")
    out = out.dropna(how="all")
    out.index.name = "timestamp"
    return out


if __name__ == "__main__":
    f = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    f.to_csv(OUT, float_format="%.1f")
    print(f.shape, "last non-missing:", f.dropna().index.max())
    d = f.resample("D").last()[[c for c in f.columns if c.endswith("_n_24h")]].dropna()
    print("Median daily detections (24 h window), Sep 1 - Oct 15 of each year:")
    sel = d[(d.index.month == 9) | ((d.index.month == 10) & (d.index.day <= 15))]
    print(sel.groupby(sel.index.year).median().round(0).to_string())
