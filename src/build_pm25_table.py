"""Turn raw daily PM2.5 JSON into one tidy table and print a data-quality report.

Output: data/processed/pm25_hourly.csv  columns: timestamp, region, pm25
Nothing is filled in: missing hours stay missing and are listed in the report.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "pm25"
OUT = ROOT / "data" / "processed" / "pm25_hourly.csv"


def load() -> pd.DataFrame:
    rows = []
    for f in sorted(RAW.glob("*.json")):
        for it in json.loads(f.read_text())["data"]["items"]:
            for region, v in it["readings"]["pm25_one_hourly"].items():
                rows.append({"timestamp": it["timestamp"], "region": region, "pm25": v})
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values(["timestamp", "region"]).reset_index(drop=True)


def report(df: pd.DataFrame) -> None:
    print(f"rows={len(df)}  hours={df.timestamp.nunique()}  regions={sorted(df.region.unique())}")
    print(f"range: {df.timestamp.min()} -> {df.timestamp.max()}")
    dup = df.duplicated(["timestamp", "region"]).sum()
    print(f"duplicate (timestamp, region): {dup}")
    print(f"null pm25: {df.pm25.isna().sum()}")
    # missing hours counted only inside downloaded days (seasons), not in the gaps between seasons
    present = pd.DatetimeIndex(df.timestamp.unique())
    days = present.normalize().unique()
    full = pd.DatetimeIndex([d + pd.Timedelta(hours=h) for d in days for h in range(24)])
    full = full[full <= present.max()]
    missing = full.difference(present)
    print(f"days with data: {len(days)}; missing hours inside those days: {len(missing)}")
    by_day = pd.Series(1, index=missing).groupby(missing.normalize()).size()
    if len(by_day):
        print("  days with gaps (hours missing):", ", ".join(f"{d.date()}({n})" for d, n in by_day.items()))
    print("per-region summary (µg/m³):")
    print(df.groupby("region").pm25.describe()[["min", "50%", "max"]].to_string())


if __name__ == "__main__":
    df = load()
    report(df)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"written: {OUT.relative_to(ROOT)}")
