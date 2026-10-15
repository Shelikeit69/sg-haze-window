"""Evaluate the decision users actually make: "which hour today is best for outdoor exercise?"

Setup (per test day D and region):
- Issue time 05:00 on D. Candidate hours 06:00-21:00 on D (horizons 1-16 h).
- Each method picks the candidate hour with the lowest predicted PM2.5.
- Regret = actual PM2.5 at the picked hour - lowest actual PM2.5 among candidates.
- Saving = mean actual PM2.5 over candidates - actual PM2.5 at the picked hour.
  (Saving vs "go at a random time"; higher is better.)

Methods
- model           : one gradient-boosting model with horizon as an input, trained on
                    horizons 1-24, target = log change from the current reading. No CAMS.
- model+cams*     : same plus CAMS for the target hour (issue time unconfirmed).
- same_hour_yday  : yesterday's reading at each candidate hour.
- train_profile   : fixed hour = lowest median hour in the training data for that region.
- cams_raw*       : lowest CAMS hour.
Persistence cannot rank hours (it predicts the same value for all of them), so it is
not a method here.

Also reports MAE by horizon for the log-change model, to compare with train_eval.py.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

import features as F

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results"
SEED = 42
ISSUE_HOUR, FIRST, LAST = 5, 6, 21

FEATS = ["pm_now", "pm_lag1", "pm_lag2", "pm_lag3", "pm_lag6", "pm_lag12", "pm_lag24",
         "pm_d3", "pm_mean24", "pm_max24", "island_mean", "island_max", "island_mean_d3",
         "wind_speed", "wind_sin", "wind_cos", "rain_3h", "rh", "blh",
         "issue_hour", "target_hour", "pm_same_hour_yday", "region_code", "horizon"]

FOLDS = {
    "A (26 Sep-5 Oct)": ("2026-09-25 23:00", "2026-09-26", "2026-10-05"),
    "B (6 Oct-15 Oct)": ("2026-10-05 23:00", "2026-10-06", "2026-10-15"),
}


def build_all_horizons() -> pd.DataFrame:
    F.HORIZONS = list(range(1, 25))
    df = F.build()
    df["region_code"] = df.region.astype("category").cat.codes
    return df.dropna(subset=["y", "pm_now"])


def fit(X, y):
    return HistGradientBoostingRegressor(loss="absolute_error", max_iter=300, learning_rate=0.05,
                                         max_leaf_nodes=15, min_samples_leaf=40,
                                         l2_regularization=1.0, random_state=SEED).fit(X, y)


def main():
    df = build_all_horizons()
    win_rows, mae_rows = [], []
    for fold, (train_end, d0, d1) in FOLDS.items():
        te = pd.Timestamp(train_end)
        tr = df[df.target_time <= te]
        ts = df[(df.issue_time >= pd.Timestamp(d0)) & (df.issue_time <= pd.Timestamp(d1) + pd.Timedelta(hours=23))]
        ts = ts.copy()
        for name, feats in (("model", FEATS), ("model+cams*", FEATS + ["cams_target"])):
            m = fit(tr[feats], np.log1p(tr.y) - np.log1p(tr.pm_now))
            ts[name] = np.expm1(np.log1p(ts.pm_now) + m.predict(ts[feats]))
        ts["persistence"] = ts.pm_now
        for meth in ("model", "model+cams*", "persistence"):
            for hg, (a, b) in {"1-3": (1, 3), "4-12": (4, 12), "13-24": (13, 24)}.items():
                s = ts[(ts.horizon >= a) & (ts.horizon <= b)]
                mae_rows.append({"fold": fold, "horizons": hg, "method": meth,
                                 "MAE": np.mean(np.abs(s.y - s[meth]))})

        prof = tr[(tr.target_hour >= FIRST) & (tr.target_hour <= LAST)].groupby(["region", "target_hour"]).y.median()
        fixed_hour = prof.groupby(level=0).idxmin().map(lambda x: x[1])

        day_sets = ts[(ts.issue_time.dt.hour == ISSUE_HOUR)
                      & (ts.target_time.dt.normalize() == ts.issue_time.dt.normalize())
                      & ts.target_hour.between(FIRST, LAST)]
        for (day, region), g in day_sets.groupby([day_sets.issue_time.dt.normalize(), "region"]):
            if len(g) < LAST - FIRST + 1:
                continue  # incomplete day (e.g. today): skip rather than guess
            actual = g.set_index("target_hour").y
            picks = {
                "model": g.loc[g["model"].idxmin(), "target_hour"],
                "model+cams*": g.loc[g["model+cams*"].idxmin(), "target_hour"],
                "same_hour_yday": g.loc[g.pm_same_hour_yday.astype(float).idxmin(), "target_hour"],
                "train_profile": fixed_hour[region],
                "cams_raw*": g.loc[g.cams_target.astype(float).idxmin(), "target_hour"],
            }
            for meth, hr in picks.items():
                v = actual[hr]
                win_rows.append({"fold": fold, "day": day.date(), "region": region, "method": meth,
                                 "pick_hour": hr, "regret": v - actual.min(), "saving": actual.mean() - v,
                                 "picked_band": F.band(v), "best_band": F.band(actual.min())})

    OUT.mkdir(exist_ok=True)
    win = pd.DataFrame(win_rows)
    win.to_csv(OUT / "window_picks.csv", index=False, float_format="%.2f")
    pd.DataFrame(mae_rows).to_csv(OUT / "metrics_logchange.csv", index=False, float_format="%.3f")

    print("MAE µg/m³, single log-change model vs persistence")
    print(pd.DataFrame(mae_rows).pivot_table(index=["fold", "method"], columns="horizons", values="MAE")
          [["1-3", "4-12", "13-24"]].round(1).to_string())
    print(f"\nWindow choice, issue {ISSUE_HOUR:02d}:00, candidates {FIRST:02d}:00-{LAST:02d}:00")
    summ = win.groupby(["fold", "method"]).agg(
        days=("day", "size"), mean_saving=("saving", "mean"), median_regret=("regret", "median"),
        mean_regret=("regret", "mean"), pick_is_best_band=("picked_band", lambda s: np.nan)).drop(columns="pick_is_best_band")
    win["same_band_as_best"] = win.picked_band == win.best_band
    summ["same_band_as_best"] = win.groupby(["fold", "method"]).same_band_as_best.mean()
    print(summ.round(2).to_string())
    print("\nFixed hour chosen by train_profile per fold/region:")
    print(win[win.method == "train_profile"].groupby(["fold", "region"]).pick_hour.first().unstack().to_string())


if __name__ == "__main__":
    main()
