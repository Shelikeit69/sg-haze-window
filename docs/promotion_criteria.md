# Shadow model: promotion criteria

Written on 15 October 2026, before any prospective prediction was scored. These rules decide when the machine-learning model may start to influence what users see. Until then it runs in shadow mode: it makes and logs predictions every day, and users only see the transparent advisor (0.5 × current reading + 0.5 × bias-corrected CAMS).

## Why shadow mode

In backtests on 2023–2026 data the model did not beat the persistence baseline (see README, Results). The most likely reason is too few haze examples: 2023–2025 had almost no haze in Singapore, so the model has seen only one real episode (2026). The approach is physically reasonable (CAMS itself turns satellite fire detections and winds into PM2.5 forecasts, and CAMS was the most useful input in our tests), but the model has not yet earned trust. Showing its forecasts now could lead someone to exercise during a high-exposure hour.

## What is scored

- Only predictions logged by `src/shadow.py` after the model was frozen. No backfilled or recomputed predictions.
- Target: NEA 1-hour PM2.5 for each of the five regions.
- Horizons 12–24 h (the decision horizon: "tonight or tomorrow morning?").
- Comparison methods, computed at the same issue times:
  - persistence (target = reading at issue time)
  - the advisor level estimate shown to users.

## Haze day

A date on which at least one NEA region has a daily mean 1-hour PM2.5 of 56 µg/m³ or more (the lower bound of NEA Band II, Elevated). Taken from NEA, not tuned.

## Promotion requires all of the following

1. **Enough evidence:** at least 30 distinct haze days with logged predictions.
2. **Accuracy:** on haze days, mean absolute error at 12–24 h is at least 10 % lower than persistence and lower than the advisor.
3. **No hidden weak spot:** in every region, model MAE is no more than 10 % worse than persistence.
4. **Honest uncertainty:** the share of actual values inside the P10–P90 interval is between 70 % and 90 %.

## Rules that keep the test fair

- Retraining creates a new model version and resets the counter. Scores of different versions are never pooled.
- The criteria above are not changed after scoring starts. If they are changed, the change is dated in this file with the reason, and the counter resets.
- Failing the criteria is reported, not hidden. The shadow log and scores are committed to the repository.

## Status

See `results/shadow_status.md` (written by `python src/shadow.py score`).
