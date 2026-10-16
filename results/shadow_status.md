# Shadow model status (shadow-v1)

Scored at 2026-10-16T23:56:35+00:00 UTC. Criteria: docs/promotion_criteria.md

- Logged predictions with a known outcome: 375
- Distinct haze days scored (12-24 h): 2 / 30 needed

| Criterion | Met |
|---|---|
| 1. >= 30 haze days | no |
| 2. MAE 35.6 <= 0.9 x persistence 22.0 and < advisor 32.9 | no |
| 3. every region <= 1.1 x persistence (worst 2.56) | no |
| 4. P10-P90 coverage 0.66 in [0.70, 0.90] | no |

**Promote: NO — stays in shadow mode**

## Hour choice (live)

Candidates: 06:00-21:00 in the 24 h after each issue. Saving = mean PM2.5 over the candidates minus PM2.5 at the picked hour (higher is better). Regret = picked minus the lowest candidate (lower is better). Not part of the promotion criteria.

No issue has all candidate hours observed yet.
