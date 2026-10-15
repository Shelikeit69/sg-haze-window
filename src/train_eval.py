"""Train per-horizon gradient-boosting models and compare them with simple baselines
on two time-ordered test folds. Writes results/metrics.csv and prints a summary.

Model target is the change from the current reading (y - pm_now), so the model
only has to learn how the next hours differ from "stay the same".
Prediction intervals: separate quantile models for P10 and P90.

Variants
- model      : main model, no CAMS (every input known at issue time)
- model+cams : adds CAMS PM2.5 for the target hour. Optimistic upper bound only:
               whether that CAMS value was available at issue time is unconfirmed.
Baselines
- persistence     : target = current reading
- same_hour_yday  : target = reading at the same clock hour 24 h before the target
- climatology     : median of training data for that region and target hour
- cams_raw        : CAMS value for the target hour (same caveat as model+cams)
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from features import HORIZONS, band, build

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results"
SEED = 42

BASE_FEATS = ["pm_now", "pm_lag1", "pm_lag2", "pm_lag3", "pm_lag6", "pm_lag12", "pm_lag24",
              "pm_d3", "pm_mean24", "pm_max24", "island_mean", "island_max", "island_mean_d3",
              "wind_speed", "wind_sin", "wind_cos", "rain_3h", "rh", "blh",
              "issue_hour", "target_hour", "pm_same_hour_yday", "region_code"]

FOLDS = {
    "A (26 Sep-5 Oct)": ("2026-09-25 23:00", "2026-09-26 00:00", "2026-10-05 23:00"),
    "B (6 Oct-15 Oct)": ("2026-10-05 23:00", "2026-10-06 00:00", "2100-01-01 00:00"),
}


def fit(X, y, loss="absolute_error", q=None):
    kw = dict(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=40,
              l2_regularization=1.0, random_state=SEED)
    if q is not None:
        m = HistGradientBoostingRegressor(loss="quantile", quantile=q, **kw)
    else:
        m = HistGradientBoostingRegressor(loss=loss, **kw)
    return m.fit(X, y)


def metrics(name, fold, h, y, p, lo=None, hi=None):
    ok = ~np.isnan(p)
    y, p = y[ok], p[ok]
    row = {"fold": fold, "horizon_h": h, "method": name, "n": int(ok.sum()),
           "MAE": np.mean(np.abs(y - p)), "RMSE": np.sqrt(np.mean((y - p) ** 2)),
           "band_acc": np.mean([band(a) == band(b) for a, b in zip(y, p)])}
    if lo is not None:
        lo, hi = lo[ok], hi[ok]
        row["cover_p10_p90"] = np.mean((y >= lo) & (y <= hi))
        row["mean_width"] = np.mean(hi - lo)
    return row


def main():
    df = build()
    df["region_code"] = df.region.astype("category").cat.codes
    df = df.dropna(subset=["y", "pm_now"])
    rows = []
    preds = []
    for fold, (train_end, test_start, test_end) in FOLDS.items():
        te_, ts_, tt_ = map(pd.Timestamp, (train_end, test_start, test_end))
        for h in HORIZONS:
            d = df[df.horizon == h]
            # training rows: target already observed before the cutoff (no overlap with test)
            tr = d[d.target_time <= te_]
            ts = d[(d.issue_time >= ts_) & (d.issue_time <= tt_)]
            y = ts.y.to_numpy()

            clim = tr.groupby(["region", "target_hour"]).y.median()
            rows.append(metrics("persistence", fold, h, y, ts.pm_now.to_numpy()))
            rows.append(metrics("same_hour_yday", fold, h, y, ts.pm_same_hour_yday.to_numpy(dtype=float)))
            rows.append(metrics("climatology", fold, h, y,
                                clim.reindex(list(zip(ts.region, ts.target_hour))).to_numpy()))
            rows.append(metrics("cams_raw*", fold, h, y, ts.cams_target.to_numpy(dtype=float)))

            for name, feats in (("model", BASE_FEATS), ("model+cams*", BASE_FEATS + ["cams_target"])):
                Xtr, Xts = tr[feats], ts[feats]
                dtr = tr.y - tr.pm_now
                p50 = ts.pm_now.to_numpy() + fit(Xtr, dtr).predict(Xts)
                p10 = ts.pm_now.to_numpy() + fit(Xtr, dtr, q=0.1).predict(Xts)
                p90 = ts.pm_now.to_numpy() + fit(Xtr, dtr, q=0.9).predict(Xts)
                p10, p90 = np.minimum(p10, p50), np.maximum(p90, p50)
                rows.append(metrics(name, fold, h, y, p50, p10, p90))
                if name == "model":
                    preds.append(ts[["issue_time", "target_time", "region", "horizon", "y", "pm_now"]]
                                 .assign(fold=fold, p10=p10, p50=p50, p90=p90))

    OUT.mkdir(exist_ok=True)
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "metrics.csv", index=False, float_format="%.3f")
    pd.concat(preds).to_csv(OUT / "test_predictions.csv", index=False, float_format="%.2f")

    pd.set_option("display.width", 200)
    for fold in FOLDS:
        t = res[res.fold == fold].pivot(index="method", columns="horizon_h", values="MAE")
        print(f"\nMAE µg/m³ — fold {fold}   (* = CAMS issue time unconfirmed)")
        print(t.round(1).to_string())
    print("\nMain model: P10-P90 coverage (target 0.80) and band accuracy")
    m = res[res.method == "model"][["fold", "horizon_h", "n", "cover_p10_p90", "mean_width", "band_acc"]]
    print(m.round(2).to_string(index=False))
    print("\nBand accuracy, persistence vs model")
    print(res[res.method.isin(["persistence", "model"])]
          .pivot_table(index=["fold", "method"], columns="horizon_h", values="band_acc").round(2).to_string())


if __name__ == "__main__":
    main()
