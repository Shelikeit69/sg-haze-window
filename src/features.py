"""Build the modelling table: one row per (issue time t, region, horizon h).

Rule: every feature must be knowable at issue time t. Weather is taken at or before t
only. CAMS at the target hour is kept in a separate column (cams_target) because its
issue time cannot be confirmed (see data/raw/README.md); the main model does not use it.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_W = ROOT / "data" / "raw" / "weather"
PM = ROOT / "data" / "processed" / "pm25_hourly.csv"
REGIONS = ["central", "east", "north", "south", "west"]
HORIZONS = [3, 6, 12, 24]

# NEA 1-hour PM2.5 bands (µg/m³)
BANDS = [(0, 55, "I Normal"), (56, 150, "II Elevated"), (151, 250, "III High"), (251, 10_000, "IV Very High")]


def band(v: float) -> int:
    for i, (lo, hi, _) in enumerate(BANDS):
        if v <= hi:
            return i
    return len(BANDS) - 1


def load_pm() -> pd.DataFrame:
    df = pd.read_csv(PM, parse_dates=["timestamp"])
    df["timestamp"] = df.timestamp.dt.tz_convert("Asia/Singapore").dt.tz_localize(None)
    return df.pivot(index="timestamp", columns="region", values="pm25").asfreq("h")


def load_open_meteo(prefix: str) -> dict:
    out = {}
    for r in REGIONS:
        f = next(RAW_W.glob(f"{prefix}_{r}_*.json"))
        h = json.loads(f.read_text())["hourly"]
        idx = pd.to_datetime(h.pop("time"))
        out[r] = pd.DataFrame(h, index=idx).asfreq("h")
    return out


def build() -> pd.DataFrame:
    pm = load_pm()
    wx = load_open_meteo("weather")
    cams = load_open_meteo("cams")
    island_mean = pm.mean(axis=1)
    island_max = pm.max(axis=1)
    rows = []
    for r in REGIONS:
        s = pm[r]
        w = wx[r].reindex(pm.index)
        wd = np.deg2rad(w["wind_direction_10m"])
        base = pd.DataFrame({
            "region": r,
            "pm_now": s,
            "pm_lag1": s.shift(1), "pm_lag2": s.shift(2), "pm_lag3": s.shift(3),
            "pm_lag6": s.shift(6), "pm_lag12": s.shift(12), "pm_lag24": s.shift(24),
            "pm_d3": s - s.shift(3),
            "pm_mean24": s.rolling(24).mean(),
            "pm_max24": s.rolling(24).max(),
            "island_mean": island_mean, "island_max": island_max,
            "island_mean_d3": island_mean - island_mean.shift(3),
            "wind_speed": w["wind_speed_10m"],
            # direction wind blows FROM; u/v-style components
            "wind_sin": np.sin(wd), "wind_cos": np.cos(wd),
            "rain_3h": w["precipitation"].rolling(3).sum(),
            "rh": w["relative_humidity_2m"],
            "blh": w["boundary_layer_height"],
            "issue_hour": pm.index.hour,
        }, index=pm.index)
        for h in HORIZONS:
            b = base.copy()
            b["horizon"] = h
            tgt_time = pm.index + pd.Timedelta(hours=h)
            b["target_time"] = tgt_time
            b["target_hour"] = tgt_time.hour
            b["y"] = s.reindex(tgt_time).to_numpy()
            # seasonal-naive candidate: same clock hour, one day before the target
            b["pm_same_hour_yday"] = s.reindex(tgt_time - pd.Timedelta(hours=24)).to_numpy()
            b["cams_target"] = cams[r]["pm2_5"].reindex(tgt_time).to_numpy()
            rows.append(b)
    df = pd.concat(rows).rename_axis("issue_time").reset_index()
    # the seasonal-naive value must already be observed at issue time (needs h <= 24)
    return df


if __name__ == "__main__":
    df = build()
    print(df.shape)
    print(df.isna().sum()[lambda x: x > 0].to_string())
