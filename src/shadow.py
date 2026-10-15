"""Shadow model: train once and freeze, log daily predictions, score them prospectively.

    python src/shadow.py train     # fit and save models/shadow-v1.joblib (+ metadata json)
    python src/shadow.py predict   # refresh recent data, predict next 1-24 h, append to log
    python src/shadow.py score     # score logged predictions against NEA readings

Predictions are logged, never shown to users, until docs/promotion_criteria.md is met.
Live inputs: NEA PM2.5 (data.gov.sg), Open-Meteo weather, CAMS forecast (live CAMS
forecasts are genuinely available before the target hour), NASA FIRMS NRT fires.
Keys: export FIRMS_MAP_KEY before `predict` (see src/fetch_upstream.py).
"""
import json
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

import features as F

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
VERSION = "shadow-v1"
MODEL = ROOT / "models" / f"{VERSION}.joblib"
META = ROOT / "models" / f"{VERSION}.json"
LOG = ROOT / "logs" / "shadow_predictions.csv"
STATUS = ROOT / "results" / "shadow_status.md"
SEED = 42
HAZE = 56  # NEA Band II lower bound

BASE = ["pm_now", "pm_lag1", "pm_lag2", "pm_lag3", "pm_lag6", "pm_lag12", "pm_lag24",
        "pm_d3", "pm_mean24", "pm_max24", "island_mean", "island_max", "island_mean_d3",
        "wind_speed", "wind_sin", "wind_cos", "rain_3h", "rh", "blh",
        "issue_hour", "target_hour", "pm_same_hour_yday", "region_code", "horizon"]


def table() -> pd.DataFrame:
    F.HORIZONS = list(range(1, 25))
    df = F.build()
    df["region_code"] = df.region.map({r: i for i, r in enumerate(F.REGIONS)})
    return df


def feats(df):
    return BASE + sorted(c for c in df.columns if c.startswith("fire_")) + ["cams_target"]


def hgb(**kw):
    return HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_leaf_nodes=15,
                                         min_samples_leaf=40, l2_regularization=1.0,
                                         random_state=SEED, **kw)


def train():
    if MODEL.exists():
        sys.exit(f"{MODEL.name} already exists. A retrain must use a new VERSION (resets the counter).")
    df = table().dropna(subset=["y", "pm_now"])
    X, cols = df[feats(df)], feats(df)
    d = np.log1p(df.y) - np.log1p(df.pm_now)
    models = {"p50": hgb(loss="absolute_error").fit(X, d),
              "p10": hgb(loss="quantile", quantile=0.1).fit(X, d),
              "p90": hgb(loss="quantile", quantile=0.9).fit(X, d)}
    MODEL.parent.mkdir(exist_ok=True)
    joblib.dump({"models": models, "features": cols, "version": VERSION}, MODEL)
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    meta = {
        "version": VERSION,
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "code_commit_at_training": commit,
        "training_target_range": [str(df.target_time.min()), str(df.target_time.max())],
        "training_rows": int(len(df)),
        "training_years": sorted(int(y) for y in df.target_time.dt.year.unique()),
        "features": cols,
        "target": "log1p(PM2.5 at target) - log1p(PM2.5 at issue time); horizons 1-24 h",
        "backtest_note": "Did not beat persistence in 2026 backtests; see README Results. Shadow only.",
        "promotion_criteria": "docs/promotion_criteria.md",
    }
    META.write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


def refresh():
    today = date.today()
    run = lambda *a: subprocess.run([sys.executable, str(SRC / a[0]), *a[1:]], check=True)
    run("fetch_pm25.py", str(today - timedelta(days=2)), str(today))
    run("build_pm25_table.py")
    run("fetch_weather.py", str(today - timedelta(days=3)), str(today + timedelta(days=2)))
    run("fetch_upstream.py", str(today - timedelta(days=3)), str(today), "--firms-only")
    run("fire_features.py")


def predict(do_refresh=True):
    if do_refresh:
        refresh()
    bundle = joblib.load(MODEL)
    df = table()
    issue = df.issue_time.max()
    now = df[df.issue_time == issue].copy()
    X = now[bundle["features"]]
    for q, m in bundle["models"].items():
        now[q] = np.expm1(np.log1p(now.pm_now) + m.predict(X))
    now["p10"], now["p90"] = np.minimum(now.p10, now.p50), np.maximum(now.p90, now.p50)
    # advisor level estimate shown to users, logged at the same issue time for comparison
    season = df[(df.horizon == 1) & (df.target_time >= pd.Timestamp(issue.year, 8, 1))
                & (df.target_time <= issue)].dropna(subset=["y"])
    ratio = (season.y / season.cams_target.astype(float)).groupby(season.region).median()
    now["advisor"] = 0.5 * now.pm_now + 0.5 * now.cams_target.astype(float) * now.region.map(ratio)
    now["version"] = VERSION
    now["logged_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cols = ["version", "logged_at_utc", "issue_time", "target_time", "region", "horizon",
            "pm_now", "p10", "p50", "p90", "advisor"]
    out = now[cols]
    LOG.parent.mkdir(exist_ok=True)
    if LOG.exists():
        old = pd.read_csv(LOG, parse_dates=["issue_time", "target_time"])
        key = ["version", "issue_time", "region", "horizon"]
        out = out[~out.set_index(key).index.isin(old.set_index(key).index)]
        out = pd.concat([old, out])
    out.to_csv(LOG, index=False, float_format="%.2f")
    print(f"logged issue {issue} ({len(now)} rows); log now {len(out)} rows")


def score():
    log = pd.read_csv(LOG, parse_dates=["issue_time", "target_time"])
    log = log[log.version == VERSION]
    pm = F.load_pm().stack().rename("y").reset_index()
    pm.columns = ["target_time", "region", "y"]
    s = log.merge(pm, on=["target_time", "region"], how="inner")
    daily = pm.groupby([pm.target_time.dt.normalize(), "region"]).y.mean()
    haze_dates = set(d for (d, _), v in daily.items() if v >= HAZE)
    s["haze_day"] = s.target_time.dt.normalize().isin(haze_dates)
    h = s[s.haze_day & s.horizon.between(12, 24)]
    lines = [f"# Shadow model status ({VERSION})", "",
             f"Scored at {datetime.now(timezone.utc).isoformat(timespec='seconds')} UTC. "
             f"Criteria: docs/promotion_criteria.md", "",
             f"- Logged predictions with a known outcome: {len(s)}",
             f"- Distinct haze days scored (12-24 h): {h.target_time.dt.normalize().nunique()} / 30 needed"]
    if len(h):
        mae = lambda c: float(np.mean(np.abs(h.y - h[c])))
        m, p, a = mae("p50"), mae("pm_now"), mae("advisor")
        cover = float(np.mean((h.y >= h.p10) & (h.y <= h.p90)))
        per = h.groupby("region").apply(lambda g: np.mean(np.abs(g.y - g.p50)) / np.mean(np.abs(g.y - g.pm_now)))
        checks = {
            "1. >= 30 haze days": h.target_time.dt.normalize().nunique() >= 30,
            f"2. MAE {m:.1f} <= 0.9 x persistence {p:.1f} and < advisor {a:.1f}": m <= 0.9 * p and m < a,
            f"3. every region <= 1.1 x persistence (worst {per.max():.2f})": bool((per <= 1.1).all()),
            f"4. P10-P90 coverage {cover:.2f} in [0.70, 0.90]": 0.70 <= cover <= 0.90,
        }
        lines += ["", "| Criterion | Met |", "|---|---|"] + [f"| {k} | {'yes' if v else 'no'} |" for k, v in checks.items()]
        lines += ["", f"**Promote: {'YES' if all(checks.values()) else 'NO — stays in shadow mode'}**"]
    else:
        lines += ["", "No haze-day outcomes yet. **Promote: NO — stays in shadow mode**"]
    STATUS.parent.mkdir(exist_ok=True)
    STATUS.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "score"
    {"train": train, "predict": lambda: predict("--no-refresh" not in sys.argv), "score": score}[cmd]()
