"""Export everything the demo page needs that is not fetched live, to app/data.json.

Every number on the page comes either from a live API call in the browser or from this
file, and this file is built only from result files and data in the repository.
Run after advisor_eval.py, window_eval.py and shadow.py predict.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import features as F

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
OUT = ROOT / "app" / "data.json"


def r(x, n=1):
    return None if pd.isna(x) else round(float(x), n)


def main():
    pm = F.load_pm()
    cams = F.load_open_meteo("cams")
    now = pm.dropna(how="all").index.max()

    # CAMS correction ratio: same season (from 1 Aug), median observed / CAMS, per region.
    # Same definition as advisor_eval.py (fold B) and shadow.py predict.
    season = pm[pm.index >= pd.Timestamp(now.year, 8, 1)]
    ratio = {}
    for reg in F.REGIONS:
        c = cams[reg]["pm2_5"].reindex(season.index)
        ratio[reg] = r((season[reg] / c).median(), 3)

    adv = pd.read_csv(RES / "advisor_test.csv").set_index("method")
    a_row = adv.loc["advisor (a,b chosen on A)"]
    p_row = adv.loc["profile only (a=1) / persistence (b=1)"]
    c_row = adv.loc["CAMS only (a=0) / corrected CAMS (b=0)"]
    win = pd.read_csv(RES / "window_picks.csv")
    ml_saving = win[(win.method == "model+fire+cams*") & win.fold.str.startswith("B")].saving.mean()
    ml = pd.read_csv(RES / "metrics_logchange.csv")
    ml_b = ml[ml.fold.str.startswith("B") & (ml.horizons == "13-24")].set_index("method").MAE

    log = pd.read_csv(ROOT / "logs" / "shadow_predictions.csv", parse_dates=["issue_time", "target_time"])
    last = log[log.issue_time == log.issue_time.max()]
    shadow = {reg: [{"t": t.strftime("%Y-%m-%dT%H:%M"), "p10": r(a), "p50": r(b), "p90": r(c)}
                    for t, a, b, c in g[["target_time", "p10", "p50", "p90"]].itertuples(index=False)]
              for reg, g in last.groupby("region")}

    snap_from = now - pd.Timedelta(hours=23)
    snapshot = {
        "pm25_last24h": {reg: [r(v, 0) for v in pm.loc[snap_from:now, reg]] for reg in F.REGIONS},
        "pm25_end": now.strftime("%Y-%m-%dT%H:%M"),
        "cams": {reg: {t.strftime("%Y-%m-%dT%H:%M"): r(v) for t, v in
                       cams[reg]["pm2_5"][now - pd.Timedelta(hours=1): now + pd.Timedelta(hours=40)].items()}
                 for reg in F.REGIONS},
    }

    out = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cams_ratio": ratio,
        "level_weight_current": float(a_row.b),
        "backtest": {
            "test_period": "6-15 Oct 2026",
            "validation_period": "26 Sep-5 Oct 2026",
            "advisor": {"saving": r(a_row.saving), "MAE": r(a_row.MAE), "band_acc": r(a_row.band_acc, 2)},
            "persistence_MAE": r(p_row.MAE), "persistence_band_acc": r(p_row.band_acc, 2),
            "cams_corrected_MAE": r(c_row.MAE),
            "fixed_hour_saving": r(p_row.saving),
            "ml_saving": r(ml_saving),
            "ml_MAE_13_24": r(ml_b.get("model+fire+cams*")), "persistence_MAE_13_24": r(ml_b.get("persistence")),
        },
        "shadow": {"version": str(last.version.iloc[0]), "issue_time": last.issue_time.iloc[0].strftime("%Y-%m-%dT%H:%M"),
                   "by_region": shadow},
        "snapshot": snapshot,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, separators=(",", ":")))
    print(json.dumps({k: v for k, v in out.items() if k not in ("shadow", "snapshot")}, indent=1))
    print("shadow issue", out["shadow"]["issue_time"], "| snapshot end", snapshot["pm25_end"], "| bytes", OUT.stat().st_size)


if __name__ == "__main__":
    main()
