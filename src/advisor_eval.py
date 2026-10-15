"""Fallback advisor (track B): simple, transparent combinations, tuned on fold A only
and tested once on fold B.

Two outputs the advisor gives a user at 05:00:
1. WHICH HOUR (06:00-21:00) is likely lowest
   score(hour) = a * profile(region, hour) + (1 - a) * cams(hour)
   profile = median PM2.5 for that region and clock hour in the training data
   a is chosen on fold A from {0, 0.25, 0.5, 0.75, 1}.
2. HOW BAD it will be at that hour (level / NEA band)
   level = b * current_reading + (1 - b) * cams_corrected(hour)
   cams_corrected = CAMS scaled by the training-period median ratio obs/CAMS per region
   b is chosen on fold A from {0, 0.25, 0.5, 0.75, 1}.

Protocol: fold A (26 Sep-5 Oct) = validation for choosing a and b.
Fold B (6-15 Oct) = test, evaluated once with the chosen values. Fold B was already
looked at in window_eval.py for the earlier methods; that is stated in the README.
CAMS issue time is unconfirmed (see data/raw/README.md), so results using CAMS may be
optimistic.
"""
from pathlib import Path

import numpy as np
import pandas as pd

import features as F
from window_eval import FIRST, ISSUE_HOUR, LAST, build_all_horizons

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results"
GRID = [0, 0.25, 0.5, 0.75, 1.0]
FOLDS = {
    "A_val": ("2026-09-25 23:00", "2026-09-26", "2026-10-05"),
    "B_test": ("2026-10-05 23:00", "2026-10-06", "2026-10-15"),
}


def day_sets(df, train_end, d0, d1):
    # Same-season data only: 2023-2025 had almost no haze in Singapore, and clean-air days
    # have a different daily pattern (afternoon minimum) from haze days (morning minimum).
    # Mixing them moved the "best hour" to the afternoon and made it worse (window_eval.py).
    season_start = pd.Timestamp(year=pd.Timestamp(d0).year, month=8, day=1)
    tr = df[(df.target_time <= pd.Timestamp(train_end)) & (df.target_time >= season_start)]
    ts = df[(df.issue_time >= pd.Timestamp(d0)) & (df.issue_time <= pd.Timestamp(d1) + pd.Timedelta(hours=23))]
    prof = (tr[tr.horizon == 1].groupby(["region", "target_hour"]).y.median())
    ratio = (tr[tr.horizon == 1].assign(r=lambda x: x.y / x.cams_target.astype(float))
             .groupby("region").r.median())
    g = ts[(ts.issue_time.dt.hour == ISSUE_HOUR)
           & (ts.target_time.dt.normalize() == ts.issue_time.dt.normalize())
           & ts.target_hour.between(FIRST, LAST)].copy()
    g["profile"] = prof.reindex(list(zip(g.region, g.target_hour))).to_numpy()

    # Regime profile (all years): haze-day vs clean-day daily pattern, picked by the current state.
    # Threshold 56 µg/m³ = lower bound of NEA Band II (Elevated); taken from NEA, not tuned.
    tr_all = df[(df.target_time <= pd.Timestamp(train_end)) & (df.horizon == 1)]
    day_mean = tr_all.groupby([tr_all.target_time.dt.normalize(), "region"]).y.transform("mean")
    tr_all = tr_all.assign(haze_day=day_mean >= 56)
    prof_r = tr_all.groupby(["haze_day", "region", "target_hour"]).y.median()
    g["haze_now"] = g.pm_mean24 >= 56
    g["profile_regime"] = prof_r.reindex(list(zip(g.haze_now, g.region, g.target_hour))).to_numpy()
    g["cams"] = g.cams_target.astype(float)
    g["cams_corr"] = g.cams * g.region.map(ratio)
    g["day"] = g.issue_time.dt.normalize()
    full = g.groupby(["day", "region"]).target_hour.transform("size") == (LAST - FIRST + 1)
    return g[full], ratio


def score_choice(g, a, col="profile"):
    g = g.assign(s=a * g[col] + (1 - a) * g.cams)
    rows = []
    for (day, region), d in g.groupby(["day", "region"]):
        pick = d.loc[d.s.idxmin()]
        rows.append({"saving": d.y.mean() - pick.y, "regret": pick.y - d.y.min(),
                     "same_band": F.band(pick.y) == F.band(d.y.min())})
    return pd.DataFrame(rows).mean()


def score_level(g, b):
    p = b * g.pm_now + (1 - b) * g.cams_corr
    return pd.Series({"MAE": np.mean(np.abs(g.y - p)),
                      "band_acc": np.mean([F.band(x) == F.band(y) for x, y in zip(g.y, p)])})


def main():
    df = build_all_horizons()
    sets = {k: day_sets(df, *v) for k, v in FOLDS.items()}
    gA, gB = sets["A_val"][0], sets["B_test"][0]

    choice_val = pd.DataFrame({a: score_choice(gA, a) for a in GRID}).T
    level_val = pd.DataFrame({b: score_level(gA, b) for b in GRID}).T
    a_best = choice_val.saving.idxmax()
    b_best = level_val.MAE.idxmin()
    print("Validation (fold A) — hour choice by weight a on profile (1 = profile only, 0 = CAMS only)")
    print(choice_val.round(2).to_string())
    print(f"-> a = {a_best}")
    print("\nValidation (fold A) — level by weight b on current reading (1 = persistence, 0 = corrected CAMS)")
    print(level_val.round(2).to_string())
    print(f"-> b = {b_best}")

    choice_val_r = pd.DataFrame({a: score_choice(gA, a, "profile_regime") for a in GRID}).T
    a_best_r = choice_val_r.saving.idxmax()
    print("\nValidation (fold A) — hour choice with REGIME profile (haze-day / clean-day pattern, all years)")
    print(choice_val_r.round(2).to_string())
    print(f"-> a = {a_best_r}")
    print("haze_now share at 05:00 — A:", round(gA.haze_now.mean(), 2), " B:", round(gB.haze_now.mean(), 2))

    test = {
        "advisor (a,b chosen on A)": (score_choice(gB, a_best), score_level(gB, b_best)),
        "advisor, regime profile (a chosen on A)": (score_choice(gB, a_best_r, "profile_regime"), score_level(gB, b_best)),
        "regime profile only (a=1)": (score_choice(gB, 1.0, "profile_regime"), score_level(gB, 1.0)),
        "profile only (a=1) / persistence (b=1)": (score_choice(gB, 1.0), score_level(gB, 1.0)),
        "CAMS only (a=0) / corrected CAMS (b=0)": (score_choice(gB, 0.0), score_level(gB, 0.0)),
    }
    print("\nTEST (fold B, 6-15 Oct, evaluated once)")
    rows = []
    for k, (c, l) in test.items():
        rows.append({"method": k, **c.round(2).to_dict(), **l.round(2).to_dict()})
    res = pd.DataFrame(rows).set_index("method")
    print(res.to_string())
    print("\nCAMS correction ratio obs/CAMS (training median), fold B:")
    print(sets["B_test"][1].round(2).to_string())
    OUT.mkdir(exist_ok=True)
    choice_val.to_csv(OUT / "advisor_val_choice.csv", float_format="%.3f")
    level_val.to_csv(OUT / "advisor_val_level.csv", float_format="%.3f")
    choice_val_r.to_csv(OUT / "advisor_val_choice_regime.csv", float_format="%.3f")
    res.assign(a=a_best, a_regime=a_best_r, b=b_best).to_csv(OUT / "advisor_test.csv", float_format="%.3f")


if __name__ == "__main__":
    main()
