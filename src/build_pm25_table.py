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
    full = pd.date_range(df.timestamp.min(), df.timestamp.max(), freq="h")
    missing = full.difference(df.timestamp.unique())
    print(f"missing hours: {len(missing)}" + (f" -> {list(missing)}" if len(missing) else ""))
    print("per-region summary (µg/m³):")
    print(df.groupby("region").pm25.describe()[["min", "50%", "max"]].to_string())


if __name__ == "__main__":
    df = load()
    report(df)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"written: {OUT.relative_to(ROOT)}")
